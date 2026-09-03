from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone

from ..database import get_db
from ..models.user import User, UserRole
from ..models.audit import AuditLog, AuditAction
from ..utils.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_token,
    MFAService
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic models for requests/responses
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.DOCTOR
    organization: Optional[str] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str
    mfa_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    requires_mfa: bool = False


class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list


class MFAVerifyRequest(BaseModel):
    token: str


# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


@router.post("/register", response_model=dict)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (doctor)"""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        organization=user_data.organization,
        license_number=user_data.license_number,
        specialty=user_data.specialty,
        is_verified=False  # Requires verification in production
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": str(new_user.id),
        "email": new_user.email
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user"""

    # Find user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Check if MFA is enabled
    if user.mfa_enabled:
        # For MFA-enabled users, we need the MFA token
        # This is a simplified flow - in production, you might want a two-step process
        if not form_data.scopes or 'mfa_token' not in form_data.scopes:
            return TokenResponse(
                access_token="",
                token_type="bearer",
                user={},
                requires_mfa=True
            )

        # Verify MFA token (assuming it's passed in scopes for this example)
        mfa_token = form_data.scopes[0] if form_data.scopes else None
        if not mfa_token or not MFAService.verify_totp(user.mfa_secret, mfa_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token"
            )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create audit log
    audit_log = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        resource_type="auth",
        description="User logged in"
    )
    db.add(audit_log)
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "organization": user.organization
        },
        requires_mfa=False
    )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup MFA for user"""

    # Generate MFA secret
    secret = MFAService.generate_secret()

    # Generate QR code
    qr_code = MFAService.generate_qr_code(current_user.email, secret)

    # Update user with MFA secret (but don't enable yet)
    current_user.mfa_secret = secret
    db.commit()

    return MFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=[]  # Could generate backup codes here
    )


@router.post("/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify MFA token and enable MFA"""

    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not set up")

    # Verify token
    if not MFAService.verify_totp(current_user.mfa_secret, request.token):
        raise HTTPException(status_code=400, detail="Invalid MFA token")

    # Enable MFA
    current_user.mfa_enabled = True
    db.commit()

    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def disable_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA for user"""

    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA not enabled")

    # Verify token before disabling
    if not MFAService.verify_totp(current_user.mfa_secret, request.token):
        raise HTTPException(status_code=400, detail="Invalid MFA token")

    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()

    return {"message": "MFA disabled successfully"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "organization": current_user.organization,
        "specialty": current_user.specialty,
        "mfa_enabled": current_user.mfa_enabled,
        "created_at": current_user.created_at.isoformat()
    }
