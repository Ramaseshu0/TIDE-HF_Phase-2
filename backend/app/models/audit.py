from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from ..database import Base


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    VIEW_PATIENT = "view_patient"
    VIEW_RECORD = "view_record"
    VIEW_FILE = "view_file"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who did what
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(SQLEnum(AuditAction), nullable=False)

    # What was accessed
    resource_type = Column(String(50), nullable=False)  # patient, record, file
    resource_id = Column(UUID(as_uuid=True), nullable=True)

    # Details
    description = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AuditLog {self.user_id} - {self.action} - {self.resource_type}>"
