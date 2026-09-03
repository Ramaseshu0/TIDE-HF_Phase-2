from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID

from ..database import get_db
from ..models.user import User
from ..models.patient import (
    Patient, MedicalRecord, DemographicData, LabData,
    Gender, BloodType
)
from ..models.audit import AuditLog, AuditAction
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["patients"])


# Pydantic models
class PatientCreate(BaseModel):
    patient_id: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: datetime
    gender: Gender
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    blood_type: Optional[BloodType] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    current_medications: Optional[str] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    blood_type: Optional[BloodType] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    current_medications: Optional[str] = None


class MedicalRecordCreate(BaseModel):
    visit_date: Optional[datetime] = None
    is_followup: bool = False
    followup_of: Optional[UUID] = None
    visit_type: Optional[str] = None
    chief_complaint: Optional[str] = None
    present_illness: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None


class LabDataCreate(BaseModel):
    test_name: str
    test_date: datetime
    test_result: Optional[str] = None
    test_unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False
    lab_notes: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new patient"""

    # Check if patient ID already exists
    existing_patient = db.query(Patient).filter(
        Patient.patient_id == patient_data.patient_id
    ).first()

    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient ID already exists"
        )

    # Create patient
    new_patient = Patient(
        **patient_data.model_dump(),
        created_by=current_user.id
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="patient",
        resource_id=new_patient.id,
        description=f"Created patient: {patient_data.first_name} {patient_data.last_name}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "message": "Patient created successfully",
        "patient_id": str(new_patient.id),
        "patient": {
            "id": str(new_patient.id),
            "patient_id": new_patient.patient_id,
            "full_name": f"{new_patient.first_name} {new_patient.last_name}",
            "date_of_birth": new_patient.date_of_birth.isoformat(),
            "gender": new_patient.gender.value
        }
    }


@router.get("/search")
async def search_patients(
    q: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search patients by name or patient ID"""

    patients = db.query(Patient).filter(
        (Patient.first_name.ilike(f"%{q}%")) |
        (Patient.last_name.ilike(f"%{q}%")) |
        (Patient.patient_id.ilike(f"%{q}%"))
    ).limit(50).all()

    return {
        "results": [
            {
                "id": str(p.id),
                "patient_id": p.patient_id,
                "full_name": f"{p.first_name} {p.last_name}",
                "date_of_birth": p.date_of_birth.isoformat(),
                "gender": p.gender.value,
                "phone": p.phone
            }
            for p in patients
        ]
    }


@router.get("/{patient_id}")
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient details"""

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create audit log for viewing
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.VIEW_PATIENT,
        resource_type="patient",
        resource_id=patient.id,
        description=f"Viewed patient: {patient.first_name} {patient.last_name}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "id": str(patient.id),
        "patient_id": patient.patient_id,
        "first_name": patient.first_name,
        "middle_name": patient.middle_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth.isoformat(),
        "gender": patient.gender.value,
        "email": patient.email,
        "phone": patient.phone,
        "emergency_contact": patient.emergency_contact,
        "emergency_phone": patient.emergency_phone,
        "address": {
            "line1": patient.address_line1,
            "line2": patient.address_line2,
            "city": patient.city,
            "state": patient.state,
            "zip_code": patient.zip_code,
            "country": patient.country
        },
        "blood_type": patient.blood_type.value if patient.blood_type else None,
        "allergies": patient.allergies,
        "chronic_conditions": patient.chronic_conditions,
        "current_medications": patient.current_medications,
        "created_at": patient.created_at.isoformat(),
        "updated_at": patient.updated_at.isoformat()
    }


@router.put("/{patient_id}")
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update patient information"""

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Update only provided fields
    update_data = patient_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="patient",
        resource_id=patient.id,
        description=f"Updated patient: {patient.first_name} {patient.last_name}"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Patient updated successfully"}


@router.post("/{patient_id}/records", status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    patient_id: UUID,
    record_data: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a medical record for a patient"""

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Calculate BMI if height and weight provided
    bmi = None
    if record_data.height_cm and record_data.weight_kg:
        height_m = record_data.height_cm / 100
        bmi = record_data.weight_kg / (height_m ** 2)

    # Create medical record
    new_record = MedicalRecord(
        **record_data.model_dump(exclude={'patient_id'}),
        patient_id=patient_id,
        bmi=bmi,
        created_by=current_user.id,
        visit_date=record_data.visit_date or datetime.now(timezone.utc)
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="medical_record",
        resource_id=new_record.id,
        description=f"Created medical record for patient: {patient.first_name} {patient.last_name}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "message": "Medical record created successfully",
        "record_id": str(new_record.id)
    }


@router.get("/{patient_id}/records")
async def get_patient_records(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical records for a patient"""

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id
    ).order_by(MedicalRecord.visit_date.desc()).all()

    return {
        "patient_id": str(patient_id),
        "total_records": len(records),
        "records": [
            {
                "id": str(r.id),
                "visit_date": r.visit_date.isoformat(),
                "is_followup": r.is_followup,
                "visit_type": r.visit_type,
                "diagnosis": r.diagnosis,
                "vitals": {
                    "height_cm": r.height_cm,
                    "weight_kg": r.weight_kg,
                    "bmi": r.bmi,
                    "blood_pressure": f"{r.blood_pressure_systolic}/{r.blood_pressure_diastolic}" if r.blood_pressure_systolic else None,
                    "heart_rate": r.heart_rate,
                    "temperature_celsius": r.temperature_celsius,
                    "respiratory_rate": r.respiratory_rate,
                    "oxygen_saturation": r.oxygen_saturation
                }
            }
            for r in records
        ]
    }


@router.post("/{patient_id}/records/{record_id}/labs", status_code=status.HTTP_201_CREATED)
async def add_lab_data(
    patient_id: UUID,
    record_id: UUID,
    lab_data: LabDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add lab data to a medical record"""

    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.patient_id == patient_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    new_lab = LabData(
        medical_record_id=record_id,
        **lab_data.model_dump()
    )

    db.add(new_lab)
    db.commit()
    db.refresh(new_lab)

    return {
        "message": "Lab data added successfully",
        "lab_id": str(new_lab.id)
    }
