"""Auto-generated route module."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import Response
from config import db, logger, get_current_user, hash_password, verify_password, create_access_token, FRONTEND_URL, SECRET_KEY, ALGORITHM, security, pwd_context
from models.schemas import News, NewsCreate
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

@router.get("/news/all")
async def get_all_news():
    """Get all news (public access for students and teachers)"""
    news_list = await db.news.find({}, {"_id": 0}).sort("published_date", -1).to_list(1000)
    return news_list


@router.get("/news/{news_id}")
async def get_news_by_id(news_id: str):
    """Get a specific news item"""
    news = await db.news.find_one({"id": news_id}, {"_id": 0})
    if not news:
        raise HTTPException(status_code=404, detail="News non trouvée")
    return news


@router.post("/news")
async def create_news(news_data: NewsCreate, current_user: dict = Depends(get_current_user)):
    """Create news (Admin and Teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    news = News(
        title=news_data.title,
        content=news_data.content,
        image_url=news_data.image_url,
        event_date=datetime.fromisoformat(news_data.event_date) if news_data.event_date else None,
        author_id=current_user['id'],
        author_name=f"{current_user['first_name']} {current_user['last_name']}"
    )
    
    doc = news.model_dump()
    doc['published_date'] = doc['published_date'].isoformat()
    if doc.get('event_date'):
        doc['event_date'] = doc['event_date'].isoformat()
    
    await db.news.insert_one(doc)
    logger.info(f"News created by {current_user['id']}: {news.title}")
    
    # Create notifications for all users (teachers and students)
    all_users = await db.users.find(
        {"role": {"$in": ["teacher", "student"]}, "status": "approved"},
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in all_users:
        await create_notification(
            user_id=user["id"],
            title="📰 Nouvelle actualité !",
            message=f"Découvrez : {news.title}",
            notification_type="news"
        )
    
    return {"message": "Actualité créée avec succès", "id": news.id}


@router.put("/news/{news_id}")
async def update_news(news_id: str, news_data: NewsCreate, current_user: dict = Depends(get_current_user)):
    """Update news (Admin and Teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    existing_news = await db.news.find_one({"id": news_id})
    if not existing_news:
        raise HTTPException(status_code=404, detail="News non trouvée")
    
    update_data = {
        "title": news_data.title,
        "content": news_data.content,
        "image_url": news_data.image_url,
        "event_date": datetime.fromisoformat(news_data.event_date).isoformat() if news_data.event_date else None
    }
    
    await db.news.update_one({"id": news_id}, {"$set": update_data})
    logger.info(f"News updated by {current_user['id']}: {news_id}")
    
    return {"message": "Actualité mise à jour"}


@router.delete("/news/{news_id}")
async def delete_news(news_id: str, current_user: dict = Depends(get_current_user)):
    """Delete news (Admin and Teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    result = await db.news.delete_one({"id": news_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News non trouvée")
    
    logger.info(f"News deleted by {current_user['id']}: {news_id}")
    return {"message": "Actualité supprimée"}


@router.post("/news/{news_id}/like")
async def like_news(news_id: str, current_user: dict = Depends(get_current_user)):
    """Like a news post"""
    await db.news.update_one(
        {"id": news_id},
        {"$inc": {"likes": 1}}
    )
    return {"message": "News likée"}


@router.get("/news/{news_id}/comments")
async def get_news_comments(news_id: str):
    """Get comments for a news post"""
    comments = await db.news_comments.find({"news_id": news_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return comments


@router.post("/news/{news_id}/comments")
async def create_news_comment(news_id: str, comment_data: dict, current_user: dict = Depends(get_current_user)):
    """Add comment to a news post"""
    comment = {
        "id": str(uuid4()),
        "news_id": news_id,
        "author_id": current_user['id'],
        "author_name": f"{current_user['first_name']} {current_user['last_name']}",
        "author_role": current_user['role'],
        "content": comment_data.get('content'),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.news_comments.insert_one(comment)
    
    # Increment comment count
    await db.news.update_one(
        {"id": news_id},
        {"$inc": {"comments": 1}}
    )
    
    logger.info(f"Comment added to news {news_id} by {current_user['id']}")
    return {"message": "Commentaire ajouté", "id": comment["id"]}

# ============ WELCOME LETTER ROUTES ============


