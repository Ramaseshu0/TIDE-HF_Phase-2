from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from ..database import Base


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BloodType(str, enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class FileType(str, enum.Enum):
    DICOM = "dicom"
    MRI = "mri"
    CT_SCAN = "ct_scan"
    XRAY = "xray"
    EHR_PDF = "ehr_pdf"
    LAB_REPORT = "lab_report"
    OTHER = "other"


class WearableType(str, enum.Enum):
    FITBIT = "fitbit"
    WHOOP = "whoop"
    APPLE_WATCH = "apple_watch"
    GARMIN = "garmin"
    MEDICAL_DEVICE = "medical_device"
    OTHER = "other"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String(50), unique=True, nullable=False, index=True)  # Hospital/Clinic ID

    # Basic Information
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)

    # Contact Information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Medical Information
    blood_type = Column(SQLEnum(BloodType), nullable=True)
    allergies = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)

    # System fields
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="patient", cascade="all, delete-orphan")
    wearable_data = relationship("WearableData", back_populates="patient", cascade="all, delete-orphan")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # Visit Information
    visit_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_followup = Column(Boolean, default=False)
    followup_of = Column(UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True)
    visit_type = Column(String(100), nullable=True)  # Regular, Emergency, Follow-up

    # Clinical Data
    chief_complaint = Column(Text, nullable=True)
    present_illness = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    treatment_plan = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Vitals
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)

    # OCR Extracted Data
    ocr_extracted_data = Column(JSON, nullable=True)

    # System fields
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    uploaded_files = relationship("UploadedFile", back_populates="medical_record", cascade="all, delete-orphan")
    lab_data = relationship("LabData", back_populates="medical_record", cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    medical_record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True)

    # File Information
    file_name = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # Storage Information
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    s3_url = Column(String(1000), nullable=False)

    # DICOM specific
    is_dicom = Column(Boolean, default=False)
    dicom_metadata = Column(JSON, nullable=True)

    # OCR Data
    ocr_text = Column(Text, nullable=True)
    ocr_data = Column(JSON, nullable=True)

    # System fields
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="uploaded_files")
    medical_record = relationship("MedicalRecord", back_populates="uploaded_files")


class LabData(Base):
    __tablename__ = "lab_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medical_record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=False)

    # Lab Information
    test_name = Column(String(255), nullable=False)
    test_date = Column(DateTime, nullable=False)
    test_result = Column(String(255), nullable=True)
    test_unit = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    is_abnormal = Column(Boolean, default=False)

    # Additional data
    lab_notes = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)

    # System fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="lab_data")


class WearableData(Base):
    __tablename__ = "wearable_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # Wearable Information
    wearable_type = Column(SQLEnum(WearableType), nullable=False)
    device_name = Column(String(100), nullable=True)

    # Authorization
    is_authorized = Column(Boolean, default=False)
    authorization_token = Column(String(500), nullable=True)
    authorization_expires = Column(DateTime, nullable=True)

    # Data
    recorded_at = Column(DateTime, nullable=False)
    heart_rate = Column(Integer, nullable=True)
    steps = Column(Integer, nullable=True)
    calories = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)

    # Raw data from device
    raw_data = Column(JSON, nullable=True)

    # System fields
    synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="wearable_data")


class DemographicData(Base):
    __tablename__ = "demographic_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True)

    # Demographics
    race = Column(String(100), nullable=True)
    ethnicity = Column(String(100), nullable=True)
    language = Column(String(100), nullable=True)
    marital_status = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    education_level = Column(String(100), nullable=True)

    # Insurance
    insurance_provider = Column(String(255), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    insurance_group_number = Column(String(100), nullable=True)

    # Social History
    smoking_status = Column(String(50), nullable=True)
    alcohol_use = Column(String(50), nullable=True)
    exercise_frequency = Column(String(50), nullable=True)

    # System fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
