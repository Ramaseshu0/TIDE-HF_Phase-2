from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import mimetypes

from ..database import get_db
from ..models.user import User
from ..models.patient import Patient, MedicalRecord, UploadedFile, FileType
from ..models.audit import AuditLog, AuditAction
from ..routers.auth import get_current_user
from ..utils.s3 import S3Service
from ..utils.ocr import OCRService
from ..utils.dicom_handler import DICOMHandler

router = APIRouter(prefix="/api/upload", tags=["upload"])


def determine_file_type(filename: str, mime_type: str) -> FileType:
    """Determine the file type based on filename and MIME type"""
    filename_lower = filename.lower()

    if mime_type == 'application/dicom' or filename_lower.endswith('.dcm'):
        return FileType.DICOM
    elif 'mri' in filename_lower:
        return FileType.MRI
    elif 'ct' in filename_lower or 'ctscan' in filename_lower:
        return FileType.CT_SCAN
    elif 'xray' in filename_lower or 'x-ray' in filename_lower or 'chest' in filename_lower:
        return FileType.XRAY
    elif mime_type == 'application/pdf' or filename_lower.endswith('.pdf'):
        return FileType.EHR_PDF
    elif 'lab' in filename_lower or 'report' in filename_lower:
        return FileType.LAB_REPORT
    else:
        return FileType.OTHER


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    patient_id: UUID = Form(...),
    medical_record_id: Optional[UUID] = Form(None),
    perform_ocr: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file (medical image, EHR document, etc.) for a patient"""

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify medical record if provided
    if medical_record_id:
        record = db.query(MedicalRecord).filter(
            MedicalRecord.id == medical_record_id,
            MedicalRecord.patient_id == patient_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="Medical record not found")

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type:
        mime_type = file.content_type or 'application/octet-stream'

    # Determine file type
    file_type = determine_file_type(file.filename, mime_type)

    # Check if it's a DICOM file
    is_dicom = DICOMHandler.is_dicom_file(file_content)
    if is_dicom:
        file_type = FileType.DICOM

    # Initialize S3 service and upload
    s3_service = S3Service()
    success, s3_key, s3_url = s3_service.upload_file(
        file_content,
        patient.patient_id,
        file.filename,
        mime_type
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to S3"
        )

    # Process DICOM metadata if applicable
    dicom_metadata = None
    if is_dicom:
        dicom_metadata = DICOMHandler.extract_dicom_metadata(file_content)

    # Perform OCR if requested and applicable
    ocr_text = None
    ocr_data = None
    if perform_ocr and file_type in [FileType.EHR_PDF, FileType.LAB_REPORT]:
        ocr_service = OCRService()
        ocr_result = ocr_service.process_ehr_document(file_content, mime_type)
        if ocr_result['success']:
            ocr_text = ocr_result['raw_text']
            ocr_data = ocr_result['extracted_data']

    # Create database record
    uploaded_file = UploadedFile(
        patient_id=patient_id,
        medical_record_id=medical_record_id,
        file_name=file.filename,
        file_type=file_type,
        file_size_bytes=file_size,
        mime_type=mime_type,
        s3_bucket=s3_service.bucket_name,
        s3_key=s3_key,
        s3_url=s3_url,
        is_dicom=is_dicom,
        dicom_metadata=dicom_metadata,
        ocr_text=ocr_text,
        ocr_data=ocr_data,
        uploaded_by=current_user.id
    )

    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPLOAD,
        resource_type="file",
        resource_id=uploaded_file.id,
        description=f"Uploaded file: {file.filename} for patient {patient.patient_id}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "message": "File uploaded successfully",
        "file_id": str(uploaded_file.id),
        "file_type": file_type.value,
        "is_dicom": is_dicom,
        "ocr_performed": perform_ocr and ocr_text is not None,
        "ocr_data": ocr_data if ocr_data else None,
        "dicom_metadata": dicom_metadata if dicom_metadata else None
    }


@router.post("/ehr-document")
async def upload_ehr_with_ocr(
    file: UploadFile = File(...),
    patient_id: UUID = Form(...),
    medical_record_id: Optional[UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an EHR document and automatically perform OCR to extract data
    This endpoint automatically processes the document and returns extracted fields
    """

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Read file content
    file_content = await file.read()

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type:
        mime_type = file.content_type or 'application/octet-stream'

    # Perform OCR
    ocr_service = OCRService()
    ocr_result = ocr_service.process_ehr_document(file_content, mime_type)

    if not ocr_result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}"
        )

    # Upload to S3
    s3_service = S3Service()
    success, s3_key, s3_url = s3_service.upload_file(
        file_content,
        patient.patient_id,
        file.filename,
        mime_type
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to S3"
        )

    # Create database record
    uploaded_file = UploadedFile(
        patient_id=patient_id,
        medical_record_id=medical_record_id,
        file_name=file.filename,
        file_type=FileType.EHR_PDF,
        file_size_bytes=len(file_content),
        mime_type=mime_type,
        s3_bucket=s3_service.bucket_name,
        s3_key=s3_key,
        s3_url=s3_url,
        is_dicom=False,
        ocr_text=ocr_result['raw_text'],
        ocr_data=ocr_result['extracted_data'],
        uploaded_by=current_user.id
    )

    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    # Update medical record with OCR data if provided
    if medical_record_id and ocr_result['extracted_data']:
        record = db.query(MedicalRecord).filter(
            MedicalRecord.id == medical_record_id
        ).first()
        if record:
            record.ocr_extracted_data = ocr_result['extracted_data']
            db.commit()

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPLOAD,
        resource_type="file",
        resource_id=uploaded_file.id,
        description=f"Uploaded EHR document with OCR: {file.filename}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "message": "EHR document processed successfully",
        "file_id": str(uploaded_file.id),
        "extracted_data": ocr_result['extracted_data'],
        "raw_text": ocr_result['raw_text'][:500] + "..." if len(ocr_result['raw_text']) > 500 else ocr_result['raw_text'],
        "confidence": ocr_result.get('confidence', 'unknown')
    }


@router.post("/batch")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    patient_id: UUID = Form(...),
    medical_record_id: Optional[UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple files at once (e.g., DICOM series)"""

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if len(files) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 files can be uploaded at once"
        )

    uploaded_files = []
    s3_service = S3Service()

    for file in files:
        file_content = await file.read()
        file_size = len(file_content)

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = file.content_type or 'application/octet-stream'

        # Determine file type
        file_type = determine_file_type(file.filename, mime_type)

        # Check if DICOM
        is_dicom = DICOMHandler.is_dicom_file(file_content)
        if is_dicom:
            file_type = FileType.DICOM

        # Upload to S3
        success, s3_key, s3_url = s3_service.upload_file(
            file_content,
            patient.patient_id,
            file.filename,
            mime_type
        )

        if not success:
            continue  # Skip failed uploads

        # Process DICOM metadata
        dicom_metadata = None
        if is_dicom:
            dicom_metadata = DICOMHandler.extract_dicom_metadata(file_content)

        # Create database record
        uploaded_file = UploadedFile(
            patient_id=patient_id,
            medical_record_id=medical_record_id,
            file_name=file.filename,
            file_type=file_type,
            file_size_bytes=file_size,
            mime_type=mime_type,
            s3_bucket=s3_service.bucket_name,
            s3_key=s3_key,
            s3_url=s3_url,
            is_dicom=is_dicom,
            dicom_metadata=dicom_metadata,
            uploaded_by=current_user.id
        )

        db.add(uploaded_file)
        uploaded_files.append(uploaded_file)

    db.commit()

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPLOAD,
        resource_type="file",
        description=f"Batch uploaded {len(uploaded_files)} files for patient {patient.patient_id}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "message": f"Successfully uploaded {len(uploaded_files)} files",
        "total_uploaded": len(uploaded_files),
        "files": [
            {
                "file_id": str(f.id),
                "file_name": f.file_name,
                "file_type": f.file_type.value,
                "is_dicom": f.is_dicom
            }
            for f in uploaded_files
        ]
    }


@router.get("/patient/{patient_id}/files")
async def list_patient_files(
    patient_id: UUID,
    file_type: Optional[FileType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all uploaded files for a patient"""

    query = db.query(UploadedFile).filter(UploadedFile.patient_id == patient_id)

    if file_type:
        query = query.filter(UploadedFile.file_type == file_type)

    files = query.order_by(UploadedFile.uploaded_at.desc()).all()

    return {
        "patient_id": str(patient_id),
        "total_files": len(files),
        "files": [
            {
                "file_id": str(f.id),
                "file_name": f.file_name,
                "file_type": f.file_type.value,
                "file_size_bytes": f.file_size_bytes,
                "is_dicom": f.is_dicom,
                "uploaded_at": f.uploaded_at.isoformat(),
                "uploaded_by": str(f.uploaded_by)
            }
            for f in files
        ]
    }
