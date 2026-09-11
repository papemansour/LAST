"""Notifications route module."""
from fastapi import APIRouter, HTTPException, Depends
from config import db, logger, get_current_user
from datetime import datetime, timezone
import uuid

router = APIRouter()


@router.get("/notifications/my-notifications")
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    """Get all notifications for the current user"""
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


# IMPORTANT: Place static routes BEFORE parameterized routes to avoid shadowing
@router.delete("/notifications/clear-all")
async def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Delete all notifications for current user"""
    result = await db.notifications.delete_many({"user_id": current_user['id']})
    return {"message": f"{result.deleted_count} notifications supprimées"}


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
