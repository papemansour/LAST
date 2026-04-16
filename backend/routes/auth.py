"""Auto-generated route module."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import Response
from config import db, logger, get_current_user, hash_password, verify_password, create_access_token, FRONTEND_URL, SECRET_KEY, ALGORITHM, security, pwd_context
from models.schemas import *
from utils.helpers import create_notification, add_student_points, send_admin_notification_email, generate_welcome_letter_content, TEST_QUESTIONS
from email_service import email_service
from websocket_manager import ws_manager
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import List, Optional
from pathlib import Path
from jose import jwt, JWTError
import uuid
import os
import logging
import random
import string
import base64
import mimetypes
import io
import csv
import stripe

router = APIRouter()

@router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (inactive until admin approves)
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        level=user_data.level,
        role="student",
        is_active=False,
        is_restricted=False,
        password_hash="",  # Will be set by admin
        preferred_slots=user_data.preferred_slots,
        referral_source=user_data.referral_source
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Send notification email to admin
    await email_service.send_admin_notification(
        user_data.email,
        user_data.first_name,
        user_data.last_name,
        user_data.level,
        user_data.phone
    )
    
    # Send confirmation email to student
    await email_service.send_registration_confirmation_email(
        user_data.email,
        user_data.first_name,
        user_data.last_name
    )
    
    return {"message": "Registration submitted. Please wait for admin approval."}


@router.post("/auth/register-group")
async def register_group(group_data: GroupRegistration):
    """Register a group - 1 person with full info + 1-2 additional members (name only)"""
    
    # Validate: must have at least 1 additional member for group registration
    if len(group_data.additional_members) == 0:
        raise HTTPException(status_code=400, detail="L'inscription de groupe nécessite au moins 2 personnes")
    
    if len(group_data.additional_members) > 2:
        raise HTTPException(status_code=400, detail="Maximum 3 personnes au total (vous + 2 autres)")
    
    # Check if email already exists
    existing = await db.users.find_one({"email": group_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà enregistrée")
    
    # Generate group ID
    group_id = str(uuid.uuid4())
    
    # Prepare group members list
    total_members = len(group_data.additional_members) + 1
    members_list = [
        {
            "first_name": group_data.first_name,
            "last_name": group_data.last_name,
            "is_main": True
        }
    ]
    
    for member in group_data.additional_members:
        members_list.append({
            "first_name": member.first_name,
            "last_name": member.last_name,
            "is_main": False
        })
    
    # Create ONE pending group registration (not activated yet)
    group_registration = {
        "id": group_id,
        "email": group_data.email,
        "phone": group_data.phone,
        "level": group_data.level,
        "role": "student",
        "course_type": "group",
        "is_active": False,
        "is_approved": False,  # Admin needs to approve
        "password_hash": "",
        "temporary_password": None,  # Will be set by admin when generating magic code
        "total_members": total_members,
        "members": members_list,
        "assigned_teacher": None,  # Will be set by admin
        "preferred_slots": group_data.preferred_slots or "",
        "referral_source": group_data.referral_source or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "magic_code_generated": False
    }
    
    await db.users.insert_one(group_registration)
    
    # Send notification to admin
    members_names = ", ".join([f"{m['first_name']} {m['last_name']}" for m in members_list])
    await email_service.send_admin_notification(
        group_data.email,
        f"Groupe de {total_members}",
        members_names,
        group_data.level,
        group_data.phone
    )
    
    logger.info(f"Group registration submitted: {group_data.email} with {total_members} members")
    
    return {
        "message": f"Inscription de groupe envoyée avec succès pour {total_members} personne(s)! En attente d'approbation par l'administrateur.",
        "group_id": group_id,
        "total_members": total_members,
        "members_names": members_names
    }


@router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get('is_active'):
        raise HTTPException(status_code=403, detail="Account not activated yet. Please wait for admin approval.")
    
    # Check if student access is restricted
    if user.get('role') == 'student' and user.get('is_restricted', False):
        raise HTTPException(status_code=403, detail="Your access has been restricted. Please contact the administrator.")
    
    # Verify password
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
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


@router.post("/auth/secretary-login")
async def secretary_login(code: str = Body(..., embed=True)):
    """Special login for secretary with secret code - gives admin access"""
    if code != "secretaire2025":
        raise HTTPException(status_code=401, detail="Code incorrect")
    
    # Find or create secretary user with admin role
    secretary = await db.users.find_one({"email": "secretaire@mykalamaenglish.com"}, {"_id": 0})
    
    if not secretary:
        # Create secretary user with admin role
        secretary_id = str(uuid4())
        secretary = {
            "id": secretary_id,
            "email": "secretaire@mykalamaenglish.com",
            "first_name": "Secrétaire",
            "last_name": "KALAMA",
            "phone": "+221000000000",
            "role": "secretary",  # Secretary role to access secretary dashboard
            "is_active": True,
            "password_hash": hash_password("secretaire2025"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "first_login": False
        }
        await db.users.insert_one(secretary)
        logger.info(f"Secretary user created with admin access via code")
    
    # Create token with secretary role
    token = create_access_token({"sub": secretary['id'], "role": "secretary"})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": secretary['id'],
            "email": secretary['email'],
            "first_name": secretary['first_name'],
            "last_name": secretary['last_name'],
            "role": "secretary"  # Return secretary role
        }
    }

# SECRETARY ENDPOINTS


@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/auth/change-password")
async def change_password(password_data: PasswordChange, current_user: dict = Depends(get_current_user)):
    # Verify old password
    if not verify_password(password_data.old_password, current_user['password_hash']):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Update password
    new_hash = hash_password(password_data.new_password)
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {
            "password_hash": new_hash, 
            "temporary_password": None,
            "current_password_plain": password_data.new_password,  # Store plain password for admin visibility
            "password_changed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Password changed by user {current_user['id']} - plain text stored for admin")
    return {"message": "Password changed successfully"}


@router.post("/auth/mark-welcome-letter-opened")
async def mark_welcome_letter_opened(current_user: dict = Depends(get_current_user)):
    """Mark welcome letter as opened for first-time users"""
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {
            "first_login": False,
            "welcome_letter_opened_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    logger.info(f"Welcome letter opened by user {current_user['id']}")
    return {"message": "Welcome letter marked as opened"}

# ADMIN ROUTES


@router.get("/auth/validate-code/{code}")
async def validate_group_code(code: str):
    """Validate a group code and return group information (public endpoint)"""
    group_code = await db.group_codes.find_one(
        {"code": code.upper()},
        {"_id": 0}
    )
    
    if not group_code:
        raise HTTPException(status_code=404, detail="Code invalide")
    
    if not group_code['is_active']:
        raise HTTPException(status_code=400, detail="Ce code n'est plus actif")
    
    if group_code['current_students'] >= group_code['max_students']:
        raise HTTPException(status_code=400, detail="Ce groupe est complet")
    
    return {
        "valid": True,
        "group_name": group_code['group_name'],
        "teacher_name": group_code['teacher_name'],
        "level": group_code['level'],
        "available_spots": group_code['max_students'] - group_code['current_students']
    }


@router.post("/auth/register-with-code")
async def register_with_code(registration: RegisterWithCode):
    """Register a GROUP account with a shared login code"""
    # Validate code
    group_code = await db.group_codes.find_one(
        {"code": registration.code.upper()},
        {"_id": 0}
    )
    
    if not group_code:
        raise HTTPException(status_code=404, detail="Code invalide")
    
    if not group_code['is_active']:
        raise HTTPException(status_code=400, detail="Ce code n'est plus actif")
    
    # Check if there's enough space for this group
    remaining_spots = group_code['max_students'] - group_code['current_students']
    if remaining_spots < registration.number_of_students:
        raise HTTPException(
            status_code=400, 
            detail=f"Pas assez de places disponibles. Places restantes: {remaining_spots}"
        )
    
    # Check if email already exists
    existing = await db.users.find_one({"email": registration.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà enregistrée")
    
    # Generate unique shared login code (8 characters)
    shared_login_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure code is unique
    while await db.users.find_one({"temporary_password": shared_login_code}, {"_id": 0}):
        shared_login_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Create ONE group account for all members
    user = User(
        email=registration.email,
        first_name=registration.first_name,
        last_name=registration.last_name,
        phone=registration.phone,
        level=group_code['level'],
        role="student",
        is_active=False,  # Will be activated by admin
        is_restricted=False,
        password_hash=pwd_context.hash(shared_login_code),  # Hash the shared code
        temporary_password=shared_login_code,  # Store it for display
        assigned_teacher=group_code['teacher_id']
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['group_code'] = registration.code.upper()
    doc['group_id'] = group_code['id']
    doc['course_type'] = 'group'
    doc['number_of_students'] = registration.number_of_students  # Track group size
    
    await db.users.insert_one(doc)
    
    # Increment student count by the number of students in this group
    await db.group_codes.update_one(
        {"id": group_code['id']},
        {"$inc": {"current_students": registration.number_of_students}}
    )
    
    # Send notification to admin
    await email_service.send_admin_notification(
        registration.email,
        f"{registration.first_name} {registration.last_name} (Groupe de {registration.number_of_students})",
        registration.last_name,
        group_code['level'],
        registration.phone
    )
    
    logger.info(f"Group account created with code {registration.code.upper()}: {registration.email} ({registration.number_of_students} students)")
    
    return {
        "message": "Inscription envoyée avec succès! Voici votre code de connexion partagé.",
        "group_name": group_code['group_name'],
        "teacher_name": group_code['teacher_name'],
        "shared_login_code": shared_login_code,  # Return the code to display to user
        "email": registration.email,
        "number_of_students": registration.number_of_students
    }


