from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from io import BytesIO

from ..database import get_db
from ..models.user import User, UserRole
from ..models.patient import UploadedFile
from ..models.audit import AuditLog, AuditAction
from ..routers.auth import get_current_user
from ..utils.s3 import S3Service
from ..utils.dicom_handler import DICOMHandler

router = APIRouter(prefix="/api/viewer", tags=["viewer"])


def check_file_access_permission(user: User, file: UploadedFile) -> bool:
    """Check if user has permission to access the file"""
    # Admin and doctors can access all files
    if user.role in [UserRole.ADMIN, UserRole.DOCTOR]:
        return True

    # Viewers can only view, not download original files (for this example)
    # You can customize this logic based on your requirements
    if user.role == UserRole.VIEWER:
        return True

    return False


@router.get("/file/{file_id}")
async def get_file_info(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about an uploaded file"""

    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permission
    if not check_file_access_permission(current_user, file):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this file"
        )

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.VIEW_FILE,
        resource_type="file",
        resource_id=file.id,
        description=f"Viewed file info: {file.file_name}"
    )
    db.add(audit_log)
    db.commit()

    # Generate presigned URL for temporary access
    s3_service = S3Service()
    presigned_url = s3_service.generate_presigned_url(file.s3_key, expiration=3600)

    return {
        "file_id": str(file.id),
        "file_name": file.file_name,
        "file_type": file.file_type.value,
        "file_size_bytes": file.file_size_bytes,
        "mime_type": file.mime_type,
        "is_dicom": file.is_dicom,
        "dicom_metadata": file.dicom_metadata,
        "ocr_data": file.ocr_data,
        "uploaded_at": file.uploaded_at.isoformat(),
        "presigned_url": presigned_url,
        "patient_id": str(file.patient_id),
        "medical_record_id": str(file.medical_record_id) if file.medical_record_id else None
    }


@router.get("/file/{file_id}/download")
async def download_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file"""

    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permission
    if not check_file_access_permission(current_user, file):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this file"
        )

    # Download from S3
    s3_service = S3Service()
    file_content = s3_service.download_file(file.s3_key)

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file from storage"
        )

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.DOWNLOAD,
        resource_type="file",
        resource_id=file.id,
        description=f"Downloaded file: {file.file_name}"
    )
    db.add(audit_log)
    db.commit()

    return StreamingResponse(
        BytesIO(file_content),
        media_type=file.mime_type,
        headers={"Content-Disposition": f"attachment; filename={file.file_name}"}
    )


@router.get("/file/{file_id}/dicom-image")
async def get_dicom_image(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get DICOM file converted to viewable image format (PNG)"""

    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if not file.is_dicom:
        raise HTTPException(status_code=400, detail="File is not a DICOM file")

    # Check permission
    if not check_file_access_permission(current_user, file):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this file"
        )

    # Download from S3
    s3_service = S3Service()
    file_content = s3_service.download_file(file.s3_key)

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file from storage"
        )

    # Convert DICOM to image
    image_bytes = DICOMHandler.convert_dicom_to_image(file_content)

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert DICOM to image"
        )

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.VIEW_FILE,
        resource_type="file",
        resource_id=file.id,
        description=f"Viewed DICOM image: {file.file_name}"
    )
    db.add(audit_log)
    db.commit()

    return Response(content=image_bytes, media_type="image/png")


@router.get("/file/{file_id}/dicom-thumbnail")
async def get_dicom_thumbnail(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get DICOM file thumbnail as base64"""

    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if not file.is_dicom:
        raise HTTPException(status_code=400, detail="File is not a DICOM file")

    # Check permission
    if not check_file_access_permission(current_user, file):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this file"
        )

    # Download from S3
    s3_service = S3Service()
    file_content = s3_service.download_file(file.s3_key)

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file from storage"
        )

    # Generate thumbnail
    thumbnail_base64 = DICOMHandler.get_dicom_thumbnail(file_content)

    if not thumbnail_base64:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate thumbnail"
        )

    return {"thumbnail": thumbnail_base64}


@router.get("/record/{record_id}/files")
async def get_record_files(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all files associated with a medical record"""

    files = db.query(UploadedFile).filter(
        UploadedFile.medical_record_id == record_id
    ).all()

    return {
        "record_id": str(record_id),
        "total_files": len(files),
        "files": [
            {
                "file_id": str(f.id),
                "file_name": f.file_name,
                "file_type": f.file_type.value,
                "is_dicom": f.is_dicom,
                "uploaded_at": f.uploaded_at.isoformat()
            }
            for f in files
        ]
    }


@router.get("/audit-logs")
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get audit logs (admin/doctor only)"""

    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view audit logs"
        )

    logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).limit(limit).all()

    return {
        "total_logs": len(logs),
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "action": log.action.value,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "description": log.description,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }
