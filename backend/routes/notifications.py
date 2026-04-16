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

@router.get("/notifications/my-notifications")
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return notifications


@router.post("/notifications/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

async def create_notification(user_id: str, arg2=None, arg3=None, arg4=None, *, 
                             notification_type: str = None, data: dict = None, 
                             title: str = None, message: str = None):
    """Helper function to create notifications
    Supports multiple calling formats:
    1. create_notification(user_id, notification_type, data) - legacy 3-param format
    2. create_notification(user_id, title, message, notification_type) - 4-param positional
    3. create_notification(user_id, title=..., message=..., notification_type=...) - named params
    """
    # Determine which format was used
    actual_title = title
    actual_message = message
    actual_type = notification_type
    actual_data = data
    
    if isinstance(arg2, str) and isinstance(arg3, dict):
        # Format 1: create_notification(user_id, notification_type, data)
        actual_type = arg2
        actual_data = arg3
    elif isinstance(arg2, str) and isinstance(arg3, str) and isinstance(arg4, str):
        # Format 2: create_notification(user_id, title, message, notification_type)
        actual_title = arg2
        actual_message = arg3
        actual_type = arg4
    elif isinstance(arg2, str) and isinstance(arg3, str) and arg4 is None:
        # Format 2 with 3 positional: create_notification(user_id, title, message)
        actual_title = arg2
        actual_message = arg3
    
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": actual_type or "general",
        "is_read": False,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Handle legacy format with data dict
    if actual_data:
        notification.update(actual_data)
    
    # Handle named parameters
    if actual_title:
        notification["title"] = actual_title
    if actual_message:
        notification["message"] = actual_message
    
    await db.notifications.insert_one(notification)
    logger.info(f"Notification created for user {user_id}: {notification.get('type')}")
    return notification

# Admin delete user (teacher or student)


@router.get("/notifications/my-notifications")
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    """Get all notifications for the current user"""
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return notifications


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.put("/notifications/mark-all-read")
async def mark_all_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    await db.notifications.update_many(
        {"user_id": current_user['id'], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    result = await db.notifications.delete_one(
        {"id": notification_id, "user_id": current_user['id']}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}


@router.delete("/notifications/clear-all")
async def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Delete all notifications for current user"""
    result = await db.notifications.delete_many({"user_id": current_user['id']})
    return {"message": f"{result.deleted_count} notifications supprimées"}

