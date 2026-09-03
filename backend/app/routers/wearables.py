from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID

from ..database import get_db
from ..models.user import User
from ..models.patient import Patient, WearableData, WearableType
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/wearables", tags=["wearables"])


# Pydantic models
class WearableConnect(BaseModel):
    patient_id: UUID
    wearable_type: WearableType
    device_name: Optional[str] = None


class WearableDataCreate(BaseModel):
    patient_id: UUID
    wearable_type: WearableType
    recorded_at: datetime
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    calories: Optional[int] = None
    sleep_hours: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    raw_data: Optional[dict] = None


@router.post("/connect")
async def connect_wearable(
    wearable_info: WearableConnect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect a wearable device to a patient

    NOTE: This is a placeholder implementation. In production, you would need to:
    1. Implement OAuth flows for each wearable provider (Fitbit, Whoop, etc.)
    2. Store authorization tokens securely
    3. Set up webhooks for real-time data sync

    Supported wearables:
    - Fitbit (requires Fitbit API OAuth)
    - Whoop (requires Whoop API OAuth)
    - Apple Watch (via HealthKit export)
    - Garmin (requires Garmin Connect API)
    - Medical devices (custom integration)
    """

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == wearable_info.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if wearable already connected
    existing = db.query(WearableData).filter(
        WearableData.patient_id == wearable_info.patient_id,
        WearableData.wearable_type == wearable_info.wearable_type,
        WearableData.is_authorized == True
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wearable device already connected for this patient"
        )

    # Create wearable connection record
    # In production, this would store OAuth tokens
    wearable = WearableData(
        patient_id=wearable_info.patient_id,
        wearable_type=wearable_info.wearable_type,
        device_name=wearable_info.device_name,
        is_authorized=False,  # Would be set to True after OAuth completion
        recorded_at=datetime.now(timezone.utc)
    )

    db.add(wearable)
    db.commit()
    db.refresh(wearable)

    return {
        "message": "Wearable device registered. Patient needs to authorize access.",
        "wearable_id": str(wearable.id),
        "wearable_type": wearable_info.wearable_type.value,
        "authorization_required": True,
        "instructions": get_authorization_instructions(wearable_info.wearable_type)
    }


def get_authorization_instructions(wearable_type: WearableType) -> str:
    """Get instructions for authorizing a specific wearable type"""
    instructions = {
        WearableType.FITBIT: "Patient needs to log in to Fitbit and authorize access to their health data.",
        WearableType.WHOOP: "Patient needs to log in to Whoop and authorize access to their recovery data.",
        WearableType.APPLE_WATCH: "Patient needs to export their Health data from the Health app on iPhone.",
        WearableType.GARMIN: "Patient needs to log in to Garmin Connect and authorize data sharing.",
        WearableType.MEDICAL_DEVICE: "Medical device data will be manually synced by healthcare provider.",
        WearableType.OTHER: "Follow device-specific authorization process."
    }
    return instructions.get(wearable_type, "Authorization instructions not available.")


@router.post("/data")
async def add_wearable_data(
    data: WearableDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add wearable data for a patient

    This endpoint can be used to:
    1. Manually enter wearable data
    2. Receive webhook data from wearable providers
    3. Batch upload exported data
    """

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create wearable data record
    wearable_data = WearableData(
        patient_id=data.patient_id,
        wearable_type=data.wearable_type,
        recorded_at=data.recorded_at,
        heart_rate=data.heart_rate,
        steps=data.steps,
        calories=data.calories,
        sleep_hours=data.sleep_hours,
        oxygen_saturation=data.oxygen_saturation,
        blood_pressure_systolic=data.blood_pressure_systolic,
        blood_pressure_diastolic=data.blood_pressure_diastolic,
        raw_data=data.raw_data,
        is_authorized=True
    )

    db.add(wearable_data)
    db.commit()
    db.refresh(wearable_data)

    return {
        "message": "Wearable data added successfully",
        "data_id": str(wearable_data.id)
    }


@router.get("/patient/{patient_id}/data")
async def get_patient_wearable_data(
    patient_id: UUID,
    wearable_type: Optional[WearableType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wearable data for a patient"""

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    query = db.query(WearableData).filter(WearableData.patient_id == patient_id)

    if wearable_type:
        query = query.filter(WearableData.wearable_type == wearable_type)

    if start_date:
        query = query.filter(WearableData.recorded_at >= start_date)

    if end_date:
        query = query.filter(WearableData.recorded_at <= end_date)

    data = query.order_by(WearableData.recorded_at.desc()).limit(1000).all()

    return {
        "patient_id": str(patient_id),
        "total_records": len(data),
        "data": [
            {
                "id": str(d.id),
                "wearable_type": d.wearable_type.value,
                "device_name": d.device_name,
                "recorded_at": d.recorded_at.isoformat(),
                "heart_rate": d.heart_rate,
                "steps": d.steps,
                "calories": d.calories,
                "sleep_hours": d.sleep_hours,
                "oxygen_saturation": d.oxygen_saturation,
                "blood_pressure": f"{d.blood_pressure_systolic}/{d.blood_pressure_diastolic}" if d.blood_pressure_systolic else None,
                "synced_at": d.synced_at.isoformat()
            }
            for d in data
        ]
    }


@router.get("/patient/{patient_id}/devices")
async def get_patient_devices(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all connected wearable devices for a patient"""

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    devices = db.query(WearableData).filter(
        WearableData.patient_id == patient_id,
        WearableData.is_authorized == True
    ).distinct(WearableData.wearable_type).all()

    return {
        "patient_id": str(patient_id),
        "connected_devices": [
            {
                "wearable_type": d.wearable_type.value,
                "device_name": d.device_name,
                "is_authorized": d.is_authorized,
                "last_sync": d.synced_at.isoformat()
            }
            for d in devices
        ]
    }


@router.get("/supported-devices")
async def get_supported_devices():
    """Get list of supported wearable devices"""

    return {
        "supported_devices": [
            {
                "type": "fitbit",
                "name": "Fitbit",
                "description": "Fitness tracker with heart rate, activity, and sleep tracking",
                "data_available": ["heart_rate", "steps", "calories", "sleep_hours"],
                "requires_oauth": True,
                "status": "integration_required"
            },
            {
                "type": "whoop",
                "name": "Whoop",
                "description": "Recovery-focused wearable with HRV, strain, and sleep tracking",
                "data_available": ["heart_rate", "sleep_hours", "calories"],
                "requires_oauth": True,
                "status": "integration_required"
            },
            {
                "type": "apple_watch",
                "name": "Apple Watch",
                "description": "Smartwatch with comprehensive health tracking",
                "data_available": ["heart_rate", "steps", "calories", "oxygen_saturation"],
                "requires_oauth": False,
                "status": "manual_export"
            },
            {
                "type": "garmin",
                "name": "Garmin",
                "description": "GPS and fitness tracking devices",
                "data_available": ["heart_rate", "steps", "calories", "sleep_hours"],
                "requires_oauth": True,
                "status": "integration_required"
            },
            {
                "type": "medical_device",
                "name": "Medical Wearables",
                "description": "FDA-approved medical monitoring devices",
                "data_available": ["heart_rate", "blood_pressure", "oxygen_saturation"],
                "requires_oauth": False,
                "status": "manual_sync"
            }
        ],
        "note": "OAuth integrations require patient authorization. Contact administrator for setup."
    }
