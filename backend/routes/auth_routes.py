"""
Authentication Routes - Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4
import uuid
from jose import jwt
import logging

from config import db, pwd_context, SECRET_KEY, ALGORITHM, security
from email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ============ PYDANTIC MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    level: str
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class GroupMember(BaseModel):
    first_name: str
    last_name: str

class GroupRegistration(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    level: str
    additional_members: List[GroupMember]
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None

class RegisterWithCode(BaseModel):
    code: str
    password: str

# ============ HELPER FUNCTIONS ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")

# ============ ROUTES ============

@router.post("/register")
async def register(user_data: UserCreate):
    """Register a new student (pending approval)"""
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = {
        "id": str(uuid4()),
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "level": user_data.level,
        "role": "student",
        "is_active": False,
        "is_restricted": False,
        "password_hash": "",
        "preferred_slots": user_data.preferred_slots,
        "referral_source": user_data.referral_source,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    # Send notifications
    await email_service.send_admin_notification(
        user_data.email, user_data.first_name, user_data.last_name,
        user_data.level, user_data.phone
    )
    await email_service.send_registration_confirmation_email(
        user_data.email, user_data.first_name, user_data.last_name
    )
    
    return {"message": "Registration submitted. Please wait for admin approval."}

@router.post("/login")
async def login(credentials: UserLogin):
    """User login"""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get('is_active'):
        raise HTTPException(status_code=403, detail="Account not activated yet.")
    
    if user.get('role') == 'student' and user.get('is_restricted', False):
        raise HTTPException(status_code=403, detail="Your access has been restricted.")
    
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user['id'], "role": user['role']})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "role": user['role'],
            "level": user.get('level')
        }
    }

@router.post("/secretary-login")
async def secretary_login(code: str = Body(..., embed=True)):
    """Secretary login with secret code"""
    SECRETARY_CODES = ["secretaire2025", "kalama2025", "admin2025"]
    
    if code not in SECRETARY_CODES:
        raise HTTPException(status_code=401, detail="Invalid secretary code")
    
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="No admin found")
    
    token = create_access_token({"sub": admin['id'], "role": "secretary"})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": admin['id'],
            "email": admin['email'],
            "first_name": "Secrétaire",
            "last_name": "",
            "role": "secretary"
        }
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post("/change-password")
async def change_password(password_data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    if not verify_password(password_data.old_password, current_user['password_hash']):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_hash = hash_password(password_data.new_password)
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"password_hash": new_hash, "temporary_password": None}}
    )
    
    return {"message": "Password changed successfully"}

@router.get("/validate-code/{code}")
async def validate_magic_code(code: str):
    """Validate a magic code for registration"""
    user = await db.users.find_one(
        {"magic_code": code, "is_active": False},
        {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1, "level": 1}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired code")
    
    return {"valid": True, "user": user}

@router.post("/register-with-code")
async def register_with_code(registration: RegisterWithCode):
    """Complete registration using magic code"""
    user = await db.users.find_one(
        {"magic_code": registration.code, "is_active": False},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired code")
    
    password_hash = hash_password(registration.password)
    
    await db.users.update_one(
        {"magic_code": registration.code},
        {
            "$set": {
                "password_hash": password_hash,
                "is_active": True,
                "activated_at": datetime.now(timezone.utc).isoformat()
            },
            "$unset": {"magic_code": ""}
        }
    )
    
    token = create_access_token({"sub": user['id'], "role": user['role']})
    
    return {
        "message": "Account activated successfully",
        "access_token": token,
        "token_type": "bearer"
    }
