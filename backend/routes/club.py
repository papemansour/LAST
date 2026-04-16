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

@router.get("/club/posts")
async def get_club_posts(category: Optional[str] = None):
    """Get all club posts or filter by category"""
    query = {"category": category} if category else {}
    posts = await db.club_posts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return posts


@router.post("/club/posts")
async def create_club_post(post_data: ClubPostCreate, current_user: dict = Depends(get_current_user)):
    """Create a new club post"""
    post = ClubPost(
        author_id=current_user['id'],
        author_name=f"{current_user['first_name']} {current_user['last_name']}",
        author_role=current_user['role'],
        title=post_data.title,
        content=post_data.content,
        category=post_data.category
    )
    
    doc = post.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.club_posts.insert_one(doc)
    
    logger.info(f"Club post created by {current_user['id']}: {post.title}")
    
    # Create notifications for all users except the author
    all_users = await db.users.find(
        {
            "role": {"$in": ["teacher", "student", "admin"]}, 
            "status": "approved",
            "id": {"$ne": current_user['id']}
        },
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in all_users:
        await create_notification(
            user_id=user["id"],
            title="🏆 Nouveau post KALAMA CLUB !",
            message=f"{current_user['first_name']} {current_user['last_name']} a publié : {post.title}",
            notification_type="club"
        )
    
    return {"message": "Post créé", "id": post.id}


@router.post("/club/posts/{post_id}/like")
async def like_club_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Like a club post"""
    await db.club_posts.update_one(
        {"id": post_id},
        {"$inc": {"likes": 1}}
    )
    return {"message": "Post liké"}


@router.get("/club/posts/{post_id}/comments")
async def get_post_comments(post_id: str):
    """Get comments for a post"""
    comments = await db.club_comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return comments


@router.post("/club/posts/{post_id}/comments")
async def create_comment(post_id: str, comment_data: ClubCommentCreate, current_user: dict = Depends(get_current_user)):
    """Add comment to a post"""
    comment = ClubComment(
        post_id=post_id,
        author_id=current_user['id'],
        author_name=f"{current_user['first_name']} {current_user['last_name']}",
        author_role=current_user['role'],
        content=comment_data.content
    )
    
    doc = comment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.club_comments.insert_one(doc)
    logger.info(f"Comment added to post {post_id} by {current_user['id']}")
    
    # Increment comment count
    await db.club_posts.update_one(
        {"id": post_id},
        {"$inc": {"comments_count": 1}}
    )
    
    return {"message": "Commentaire ajouté", "id": comment.id}

# ==================== LEADERBOARD ENDPOINTS ====================

class LeaderboardEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    user_name: str
    user_role: str  # 'teacher' ou 'student'
    rank: int  # 1-10
    created_by: str  # Admin ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@router.get("/club/leaderboard")
async def get_leaderboard():
    """Get current leaderboard - Public endpoint"""
    entries = await db.leaderboard.find({}, {"_id": 0}).sort("rank", 1).to_list(10)
    return entries


@router.post("/club/leaderboard")
async def create_leaderboard_entry(
    user_id: str,
    rank: int,
    current_user: dict = Depends(get_current_user)
):
    """Create or update leaderboard entry - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if rank < 1 or rank > 10:
        raise HTTPException(status_code=400, detail="Rank must be between 1 and 10")
    
    # Get user details
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if rank already taken
    existing = await db.leaderboard.find_one({"rank": rank})
    if existing:
        raise HTTPException(status_code=400, detail=f"Rank {rank} is already taken by {existing['user_name']}")
    
    # Check if user already in leaderboard
    user_entry = await db.leaderboard.find_one({"user_id": user_id})
    if user_entry:
        raise HTTPException(status_code=400, detail=f"{user['first_name']} {user['last_name']} is already ranked at position {user_entry['rank']}")
    
    entry = LeaderboardEntry(
        user_id=user_id,
        user_name=f"{user['first_name']} {user['last_name']}",
        user_role=user['role'],
        rank=rank,
        created_by=current_user['id']
    )
    
    doc = entry.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.leaderboard.insert_one(doc)
    
    logger.info(f"Leaderboard entry created: {user['first_name']} {user['last_name']} at rank {rank}")
    return {"message": "Entry added to leaderboard", "id": entry.id}


@router.put("/club/leaderboard/{user_id}")
async def update_leaderboard_rank(
    user_id: str,
    new_rank: int,
    current_user: dict = Depends(get_current_user)
):
    """Update user's rank - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if new_rank < 1 or new_rank > 10:
        raise HTTPException(status_code=400, detail="Rank must be between 1 and 10")
    
    # Check if new rank is taken
    existing = await db.leaderboard.find_one({"rank": new_rank, "user_id": {"$ne": user_id}})
    if existing:
        raise HTTPException(status_code=400, detail=f"Rank {new_rank} is already taken")
    
    result = await db.leaderboard.update_one(
        {"user_id": user_id},
        {"$set": {"rank": new_rank, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    
    return {"message": "Rank updated"}


@router.delete("/club/leaderboard/{user_id}")
async def remove_from_leaderboard(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove user from leaderboard - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.leaderboard.delete_one({"user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    
    return {"message": "Removed from leaderboard"}


@router.get("/club/student-of-month")
async def get_student_of_month():
    """Get current Student of the Month"""
    badge = await db.student_of_month.find_one({"active": True}, {"_id": 0})
    if not badge:
        return None
    
    # Check if expired
    if badge.get('expires_at'):
        expires_date = datetime.fromisoformat(badge['expires_at'])
        if datetime.now(timezone.utc) > expires_date:
            await db.student_of_month.update_one(
                {"user_id": badge['user_id']},
                {"$set": {"active": False}}
            )
            return None
    
    return badge


@router.post("/club/student-of-month")
async def set_student_of_month(
    user_id: str,
    duration_days: int,
    current_user: dict = Depends(get_current_user)
):
    """Set Student of the Month - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get user details
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Deactivate previous badge
    await db.student_of_month.update_many(
        {"active": True},
        {"$set": {"active": False}}
    )
    
    # Create new badge
    expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    badge_title = "Meilleur Prof du Mois" if user['role'] == 'teacher' else "Étudiant du Mois"
    badge = {
        "id": str(uuid4()),
        "user_id": user_id,
        "user_name": f"{user['first_name']} {user['last_name']}",
        "user_role": user['role'],
        "badge_title": badge_title,
        "active": True,
        "likes": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at.isoformat(),
        "created_by": current_user['id']
    }
    
    await db.student_of_month.insert_one(badge)
    logger.info(f"{badge_title} set: {user['first_name']} {user['last_name']} for {duration_days} days")
    
    return {"message": f"Badge {badge_title} attribué", "expires_at": expires_at.isoformat()}


@router.post("/club/student-of-month/like")
async def like_student_of_month(current_user: dict = Depends(get_current_user)):
    """Like the Student/Teacher of the Month"""
    badge = await db.student_of_month.find_one({"active": True})
    if not badge:
        raise HTTPException(status_code=404, detail="Aucun badge actif")
    
    await db.student_of_month.update_one(
        {"id": badge['id']},
        {"$inc": {"likes": 1}}
    )
    
    return {"message": "Like ajouté!", "likes": badge.get('likes', 0) + 1}


@router.get("/club/events")
async def get_club_events():
    """Get all upcoming club events"""
    events = await db.club_events.find({}, {"_id": 0}).sort("event_date", 1).to_list(1000)
    return events


@router.post("/club/events")
async def create_club_event(event_data: ClubEventCreate, current_user: dict = Depends(get_current_user)):
    """Create a new club event (teachers and admin only)"""
    if current_user['role'] not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Seuls les professeurs et admins peuvent créer des événements")
    
    event = ClubEvent(
        title=event_data.title,
        description=event_data.description,
        event_date=datetime.fromisoformat(event_data.event_date),
        duration_minutes=event_data.duration_minutes,
        max_participants=event_data.max_participants,
        event_link=event_data.event_link,
        created_by=current_user['id']
    )
    
    doc = event.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['event_date'] = doc['event_date'].isoformat()
    await db.club_events.insert_one(doc)
    
    logger.info(f"Club event created by {current_user['id']}: {event.title}")
    return {"message": "Événement créé", "id": event.id}


@router.delete("/club/posts/{post_id}")
async def delete_club_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a club post (admin or teacher only)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    result = await db.club_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post non trouvé")
    
    # Also delete comments for this post
    await db.club_comments.delete_many({"post_id": post_id})
    
    logger.info(f"Club post deleted by {current_user['role']}: {post_id}")
    return {"message": "Post supprimé"}


@router.delete("/club/events/{event_id}")
async def delete_club_event(event_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a club event (admin or teacher only)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    result = await db.club_events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    logger.info(f"Club event deleted by {current_user['role']}: {event_id}")
    return {"message": "Événement supprimé"}


@router.post("/club/events/{event_id}/join")
async def join_club_event(event_id: str, current_user: dict = Depends(get_current_user)):
    """Join a club event"""
    event = await db.club_events.find_one({"id": event_id}, {"_id": 0})
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    if current_user['id'] in event.get('participants', []):
        raise HTTPException(status_code=400, detail="Déjà inscrit")
    
    if len(event.get('participants', [])) >= event['max_participants']:
        raise HTTPException(status_code=400, detail="Événement complet")
    
    await db.club_events.update_one(
        {"id": event_id},
        {"$push": {"participants": current_user['id']}}
    )
    
    return {"message": "Inscription confirmée"}


@router.get("/club/leaderboard")
async def get_club_leaderboard():
    """Get club leaderboard based on contributions"""
    # Get post counts per user
    pipeline = [
        {"$group": {
            "_id": "$author_id",
            "author_name": {"$first": "$author_name"},
            "author_role": {"$first": "$author_role"},
            "post_count": {"$sum": 1},
            "total_likes": {"$sum": "$likes"}
        }},
        {"$sort": {"total_likes": -1}},
        {"$limit": 10}
    ]
    
    leaderboard = await db.club_posts.aggregate(pipeline).to_list(10)
    return leaderboard

# ============ GAMES & FLASHCARDS ENDPOINTS ============


