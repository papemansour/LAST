"""Auto-generated route module."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import Response
from config import db, logger, get_current_user, hash_password, verify_password, create_access_token, FRONTEND_URL, SECRET_KEY, ALGORITHM, security, pwd_context
from models.schemas import StudentPoints, ChallengeProgress
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


@router.get("/student/my-receipts")
async def get_student_receipts(current_user: dict = Depends(get_current_user)):
    """Get all payment receipts for the current student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    receipts = await db.student_receipts.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return receipts


@router.get("/student/my-course-summaries")
async def get_student_course_summaries(current_user: dict = Depends(get_current_user)):
    """Get all course summaries sent to the student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    summaries = await db.course_summaries.find(
        {"student_ids": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Mark as read and get question status
    for summary in summaries:
        # Check if student has unread questions
        unread_answers = await db.summary_questions.count_documents({
            "summary_id": summary['id'],
            "student_id": current_user['id'],
            "answer": {"$exists": True},
            "answer_read": {"$ne": True}
        })
        summary['unread_answers'] = unread_answers
    
    return summaries


@router.post("/student/ask-summary-question")
async def ask_summary_question(question_data: dict, current_user: dict = Depends(get_current_user)):
    """Student asks a question about a course summary"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Verify student has access to this summary
    summary = await db.course_summaries.find_one(
        {"id": question_data['summary_id'], "student_ids": current_user['id']},
        {"_id": 0}
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found or access denied")
    
    question = {
        "id": str(uuid4()),
        "summary_id": question_data['summary_id'],
        "student_id": current_user['id'],
        "student_name": f"{current_user['first_name']} {current_user['last_name']}",
        "teacher_id": summary['teacher_id'],
        "question": question_data.get('question', ''),
        "question_audio_url": question_data.get('question_audio_url'),
        "answer": None,
        "answer_audio_url": None,
        "question_read": False,
        "answer_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.summary_questions.insert_one(question)
    # Remove _id added by insert_one before returning
    question.pop('_id', None)
    
    # Notify teacher via database notification
    try:
        await create_notification(
            user_id=summary['teacher_id'],
            notification_type="summary_question",
            data={"message": f"Question de {current_user['first_name']}: {question_data.get('question', 'Message vocal')[:50]}..."}
        )
    except Exception as e:
        logger.warning(f"Failed to create notification: {e}")
    
    # Send real-time WebSocket notification to teacher
    try:
        await ws_manager.send_personal_notification(
            user_id=summary['teacher_id'],
            notification={
                "type": "new_question",
                "title": "📩 Nouvelle Question",
                "message": f"{current_user['first_name']} a posé une question sur '{summary.get('title', 'Résumé')}'",
                "summary_id": question_data['summary_id'],
                "question_id": question['id'],
                "student_name": f"{current_user['first_name']} {current_user['last_name']}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket notification: {e}")
    
    logger.info(f"Summary question from student {current_user['id']} on summary {question_data['summary_id']}")
    return {"message": "Question envoyée avec succès", "question": question}


@router.post("/student/upload-question-audio")
async def upload_question_audio(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload audio file for student voice question"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    allowed_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/webm', 'audio/ogg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'webm'
    unique_filename = f"student_audio_{uuid4()}.{file_extension}"
    
    # Store audio file in MongoDB GridFS for persistence
    content = await file.read()
    audio_doc = {
        "id": unique_filename,
        "filename": unique_filename,
        "content_type": file.content_type,
        "data": base64.b64encode(content).decode('utf-8'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user['id']
    }
    await db.audio_files.insert_one(audio_doc)
    
    file_url = f"/api/audio/{unique_filename}"
    return {"file_url": file_url, "message": "Audio uploadé avec succès"}


@router.delete("/student/delete-question/{question_id}")
async def delete_student_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Student deletes their own question"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    result = await db.summary_questions.delete_one({
        "id": question_id,
        "student_id": current_user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question supprimée"}


@router.put("/student/mark-answer-read/{question_id}")
async def mark_answer_read(question_id: str, current_user: dict = Depends(get_current_user)):
    """Student marks an answer as read"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    await db.summary_questions.update_one(
        {"id": question_id, "student_id": current_user['id']},
        {"$set": {"answer_read": True}}
    )
    return {"message": "Réponse marquée comme lue"}


@router.get("/student/my-summary-questions/{summary_id}")
async def get_student_summary_questions(summary_id: str, current_user: dict = Depends(get_current_user)):
    """Get student's questions and answers for a summary"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    questions = await db.summary_questions.find(
        {"summary_id": summary_id, "student_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Mark answers as read
    await db.summary_questions.update_many(
        {"summary_id": summary_id, "student_id": current_user['id'], "answer": {"$exists": True}},
        {"$set": {"answer_read": True}}
    )
    
    return questions


@router.get("/student/my-links")
async def get_student_links(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get links sent by teacher to this student
    links = await db.student_links.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return links


@router.get("/student/my-documents")
async def get_student_documents(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get documents from teacher
    teacher_docs = await db.documents.find(
        {"recipient_id": current_user['id'], "recipient_type": "student"},
        {"_id": 0}
    ).to_list(1000)
    
    # Get documents from admin
    admin_docs = await db.admin_documents.find(
        {"to_user_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    return teacher_docs + admin_docs


@router.get("/student/my-homeworks")
async def get_student_homeworks(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    homeworks = await db.student_homeworks.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return homeworks


@router.get("/student/my-teacher/{teacher_id}")
async def get_student_teacher(teacher_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    teacher = await db.users.find_one(
        {"id": teacher_id, "role": "teacher"},
        {"_id": 0, "password_hash": 0}
    )
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return teacher


@router.post("/student/send-document-to-admin")
async def student_send_document_to_admin(doc_data: dict, current_user: dict = Depends(get_current_user)):
    """Student sends a document to admin"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get admin user
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    document = {
        "id": str(uuid4()),
        "from_user_id": current_user['id'],
        "from_user_role": "student",
        "to_user_id": admin['id'],
        "to_user_role": "admin",
        "title": doc_data['title'],
        "description": doc_data.get('description', ''),
        "file_url": doc_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(document)
    
    # Create notification for admin
    await create_notification(
        user_id=admin['id'],
        notification_type="new_document",
        data={"message": f"Nouveau document de l'étudiant {current_user['first_name']}: {doc_data['title']}"}
    )
    
    logger.info(f"Document sent by student {current_user['id']} to admin")
    return {"message": "Document envoyé à l'admin avec succès"}


@router.post("/student/upload-homework")
async def upload_homework(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    file_url = f"/uploads/homeworks/{current_user['id']}/{file.filename}"
    logger.info(f"Homework file uploaded by student {current_user['id']}: {file.filename}")
    
    return {
        "message": "File uploaded successfully",
        "file_url": file_url,
        "filename": file.filename
    }


@router.post("/student/submit-homework")
async def submit_homework(homework_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get student info
    student = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    homework = {
        "id": str(uuid.uuid4()),
        "student_id": current_user['id'],
        "student_name": f"{student['first_name']} {student['last_name']}",
        "teacher_id": student.get('assigned_teacher'),
        "title": homework_data['title'],
        "description": homework_data.get('description', ''),
        "file_url": homework_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "submitted"
    }
    
    await db.student_homeworks.insert_one(homework)
    logger.info(f"Homework submitted by student {current_user['id']}: {homework_data['title']}")
    
    # Create notification for teacher if assigned
    if student.get('assigned_teacher'):
        await create_notification(student['assigned_teacher'], 'homework_submitted', {
            "student_name": f"{student['first_name']} {student['last_name']}",
            "title": homework_data['title']
        })
    
    return {"message": "Homework submitted successfully"}

# Route for teacher to send links to specific student


@router.get("/student/my-group-courses")
async def get_student_group_courses(current_user: dict = Depends(get_current_user)):
    """Get group courses the current student is enrolled in"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Accès réservé aux étudiants")
    
    courses = await db.group_courses.find(
        {"student_ids": current_user['id'], "status": "active"},
        {"_id": 0}
    ).to_list(50)
    
    # Get upcoming sessions for each course
    for course in courses:
        sessions = await db.group_sessions.find(
            {"group_id": course['id'], "status": "scheduled"},
            {"_id": 0}
        ).sort("scheduled_date", 1).to_list(5)
        course['upcoming_sessions'] = sessions
    
    return courses


@router.get("/student/my-meet-links")
async def get_my_meet_links(current_user: dict = Depends(get_current_user)):
    """Get all meet links for current student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    meet_links = await db.meet_links.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).sort("scheduled_date", -1).to_list(100)
    
    return meet_links


@router.put("/student/mark-meet-attended/{meet_id}")
async def mark_meet_attended(meet_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a meet link as attended by student"""

# ========== STUDENT AVAILABILITY SYSTEM ==========


@router.post("/student/set-availability")
async def set_student_availability(data: dict, current_user: dict = Depends(get_current_user)):
    """Student sets their weekly availability"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    availability = {
        "student_id": current_user['id'],
        "student_name": f"{current_user['first_name']} {current_user['last_name']}",
        "slots": data.get('slots', []),  # List of {day: "monday", time: "09:00", available: true}
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert - update if exists, insert if not
    await db.student_availability.update_one(
        {"student_id": current_user['id']},
        {"$set": availability},
        upsert=True
    )
    
    return {"message": "Disponibilités enregistrées", "availability": availability}


@router.get("/student/my-availability")
async def get_student_availability(current_user: dict = Depends(get_current_user)):
    """Get student's own availability"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    availability = await db.student_availability.find_one(
        {"student_id": current_user['id']},
        {"_id": 0}
    )
    
    return availability or {"slots": []}


@router.get("/student/my-progression")
async def get_my_progression(current_user: dict = Depends(get_current_user)):
    """Get student progression statistics"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get all meet links
    all_meets = await db.meet_links.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    # Calculate statistics
    total_courses = len(all_meets)
    completed_courses = len([m for m in all_meets if m.get('attended', False)])
    
    # Calculate percentage
    percentage = round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0
    
    # Calculate consecutive days (simplified - count unique dates of attended courses in last 30 days)
    now = datetime.now(timezone.utc)
    recent_attended = [
        m for m in all_meets 
        if m.get('attended', False) and 
        datetime.fromisoformat(m['scheduled_date'].replace('Z', '+00:00')) > now - timedelta(days=30)
    ]
    
    # Get unique dates
    attended_dates = set()
    for m in recent_attended:
        date = datetime.fromisoformat(m['scheduled_date'].replace('Z', '+00:00')).date()
        attended_dates.add(date)
    
    # Calculate consecutive days
    consecutive_days = 0
    if attended_dates:
        sorted_dates = sorted(attended_dates, reverse=True)
        consecutive_days = 1
        for i in range(len(sorted_dates) - 1):
            if (sorted_dates[i] - sorted_dates[i+1]).days == 1:
                consecutive_days += 1
            else:
                break
    
    return {
        "percentage": percentage,
        "consecutive_days": consecutive_days,
        "courses_completed": completed_courses,
        "total_courses": total_courses
    }

# ==================== BADGES ENDPOINTS ====================


@router.get("/student/my-badges")
async def get_my_badges(current_user: dict = Depends(get_current_user)):
    """Get all badges for current student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get student's badge IDs
    student_badges = await db.student_badges.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    badge_ids = [sb['badge_id'] for sb in student_badges]
    
    # Get all badges
    all_badges = await db.badges.find({}, {"_id": 0}).to_list(100)
    
    # Mark which badges the student has
    for badge in all_badges:
        badge['earned'] = badge['id'] in badge_ids
        if badge['earned']:
            sb = next((sb for sb in student_badges if sb['badge_id'] == badge['id']), None)
            if sb:
                badge['awarded_at'] = sb.get('awarded_at')
    
    return all_badges


@router.get("/student/my-points")
async def get_my_points(current_user: dict = Depends(get_current_user)):
    """Get student's points and discount - Coffre aux Trésors"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get or create student points record
    points_record = await db.student_points.find_one({"student_id": current_user['id']}, {"_id": 0})
    
    if not points_record:
        # Create new record
        points = StudentPoints(student_id=current_user['id'])
        doc = points.model_dump()
        doc['last_updated'] = doc['last_updated'].isoformat()
        await db.student_points.insert_one(doc)
        points_record = doc
    
    available_points = points_record.get('available_points', 0)
    
    # Système de récompenses par paliers
    rewards = {
        "unlocked": available_points >= 50,  # Réductions actives à partir de 50 points
        "current_tier": 0,
        "tiers": [
            {"points": 50, "discount_eur": 5, "discount_fcfa": 3000, "label": "🥉 Bronze", "unlocked": available_points >= 50},
            {"points": 100, "discount_eur": 12, "discount_fcfa": 7500, "label": "🥈 Argent", "unlocked": available_points >= 100},
            {"points": 200, "discount_eur": 25, "discount_fcfa": 15000, "label": "🥇 Or", "unlocked": available_points >= 200},
            {"points": 500, "discount_eur": 70, "discount_fcfa": 45000, "label": "💎 Diamant", "unlocked": available_points >= 500}
        ],
        "next_tier_points": 50 if available_points < 50 else (100 if available_points < 100 else (200 if available_points < 200 else (500 if available_points < 500 else None)))
    }
    
    # Déterminer le palier actuel
    if available_points >= 500:
        rewards["current_tier"] = 4
    elif available_points >= 200:
        rewards["current_tier"] = 3
    elif available_points >= 100:
        rewards["current_tier"] = 2
    elif available_points >= 50:
        rewards["current_tier"] = 1
    
    # Calculer la réduction actuelle basée sur le palier
    current_discount_eur = 0
    current_discount_fcfa = 0
    if rewards["current_tier"] > 0:
        tier_index = rewards["current_tier"] - 1
        current_discount_eur = rewards["tiers"][tier_index]["discount_eur"]
        current_discount_fcfa = rewards["tiers"][tier_index]["discount_fcfa"]
    
    return {
        "total_points": points_record.get('total_points', 0),
        "available_points": available_points,
        "rewards": rewards,
        "current_discount_eur": current_discount_eur,
        "current_discount_fcfa": current_discount_fcfa,
        "points_to_next_tier": (rewards["next_tier_points"] - available_points) if rewards["next_tier_points"] else 0,
        "total_discount_earned": points_record.get('total_discount_earned', 0)
    }


# ============ COURS GROUPÉS (GROUP COURSES) ============


@router.get("/student/my-group-courses")
async def get_my_group_courses(current_user: dict = Depends(get_current_user)):
    """Get all group courses the student is enrolled in"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Find courses where student is enrolled
    courses = await db.group_courses.find(
        {"current_students": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    for course in courses:
        teacher = await db.users.find_one(
            {"id": course['teacher_id']},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if teacher:
            course['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
        
        # Get other students in the group (for social features)
        course['group_members'] = []
        for student_id in course.get('current_students', []):
            if student_id != current_user['id']:
                student = await db.users.find_one(
                    {"id": student_id},
                    {"_id": 0, "first_name": 1, "last_name": 1}
                )
                if student:
                    course['group_members'].append(f"{student['first_name']} {student['last_name'][0]}.")
    
    return courses


@router.get("/student/my-challenge-progress")
async def get_my_challenge_progress(current_user: dict = Depends(get_current_user)):
    """Get student's progress on current challenges"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get current challenges
    now = datetime.now(timezone.utc)
    challenges = await db.weekly_challenges.find(
        {
            "active": True,
            "week_start": {"$lte": now},
            "week_end": {"$gte": now}
        },
        {"_id": 0}
    ).to_list(100)
    
    # Get progress for each challenge
    for challenge in challenges:
        progress = await db.challenge_progress.find_one(
            {"student_id": current_user['id'], "challenge_id": challenge['id']},
            {"_id": 0}
        )
        challenge['progress'] = progress if progress else {
            "current_count": 0,
            "completed": False
        }
    
    return challenges


@router.post("/student/complete-challenge/{challenge_id}")
async def complete_challenge(challenge_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a challenge as completed and award points"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get challenge
    challenge = await db.weekly_challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if already completed
    existing_progress = await db.challenge_progress.find_one({
        "student_id": current_user['id'],
        "challenge_id": challenge_id,
        "completed": True
    })
    
    if existing_progress:
        raise HTTPException(status_code=400, detail="Challenge already completed")
    
    # Mark as completed
    progress = ChallengeProgress(
        student_id=current_user['id'],
        challenge_id=challenge_id,
        current_count=challenge['target_count'],
        completed=True,
        completed_at=datetime.now(timezone.utc)
    )
    
    progress_doc = progress.model_dump()
    progress_doc['completed_at'] = progress_doc['completed_at'].isoformat()
    await db.challenge_progress.update_one(
        {"student_id": current_user['id'], "challenge_id": challenge_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    # Award points
    points_record = await db.student_points.find_one({"student_id": current_user['id']})
    
    if not points_record:
        points = StudentPoints(
            student_id=current_user['id'],
            total_points=challenge['points_reward'],
            available_points=challenge['points_reward']
        )
        doc = points.model_dump()
        doc['last_updated'] = doc['last_updated'].isoformat()
        await db.student_points.insert_one(doc)
    else:
        await db.student_points.update_one(
            {"student_id": current_user['id']},
            {
                "$inc": {
                    "total_points": challenge['points_reward'],
                    "available_points": challenge['points_reward']
                },
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    # Get updated points
    updated_points = await db.student_points.find_one({"student_id": current_user['id']}, {"_id": 0})
    
    # Check if student reached 50 points threshold - notify admin
    if updated_points['available_points'] >= 50:
        # Get admin
        admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
        if admin:
            await create_notification(
                user_id=admin['id'],
                title=f"💰 Étudiant a atteint 50 points",
                message=f"L'étudiant {current_user['id']} a atteint {updated_points['available_points']} points",
                notification_type="points_milestone"
            )
    
    # Notify student
    await create_notification(
        user_id=current_user['id'],
        title=f"🎉 Défi complété !",
        message=f"Vous avez gagné {challenge['points_reward']} points XP",
        notification_type="challenge_completed"
    )
    
    return {
        "message": "Défi complété !",
        "points_earned": challenge['points_reward'],
        "total_points": updated_points['total_points'],
        "available_points": updated_points['available_points']
    }

# ==================== NOTIFICATIONS ENDPOINTS ====================


@router.get("/student/my-games")
async def get_student_games(current_user: dict = Depends(get_current_user)):
    """Get all games assigned to student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    games = await db.game_assignments.find({"student_id": current_user['id']}, {"_id": 0}).to_list(100)
    
    # Enrich games with actual game data
    for game in games:
        if game['game_type'] == 'flashcard' and game.get('game_id'):
            flashcard_set = await db.flashcard_sets.find_one({"id": game['game_id']}, {"_id": 0})
            if flashcard_set:
                game['flashcards'] = flashcard_set['flashcards']
        elif game['game_type'] == 'quiz' and game.get('game_id'):
            quiz = await db.quizzes.find_one({"id": game['game_id']}, {"_id": 0})
            if quiz:
                game['questions'] = quiz['questions']
                game['time_limit'] = quiz.get('time_limit', 0)
        elif game['game_type'] == 'memory' and game.get('game_id'):
            memory_game = await db.memory_games.find_one({"id": game['game_id']}, {"_id": 0})
            if memory_game:
                game['pairs'] = memory_game['pairs']
    
    return games


@router.post("/student/submit-game-score")
async def submit_game_score(data: dict, current_user: dict = Depends(get_current_user)):
    """Student submits game score"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    result = await db.game_assignments.update_one(
        {"id": data['assignment_id'], "student_id": current_user['id']},
        {
            "$set": {
                "completed": True,
                "score": data['score'],
                "total": data['total'],
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Score submitted successfully"}

# ============ TEST QUESTIONS MANAGEMENT (ADMIN) ============


@router.get("/student/my-videos")
async def get_student_videos(current_user: dict = Depends(get_current_user)):
    """Get all videos assigned to student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    videos = await db.student_videos.find({"student_id": current_user['id']}, {"_id": 0}).to_list(100)
    return videos

# ============ WEEKEND GIFTS FOR KIDS ============


@router.get("/student/weekend-gift")
async def get_weekend_gift(current_user: dict = Depends(get_current_user)):
    """Get current weekend gift"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get current week number
    from datetime import datetime
    week_number = datetime.now(timezone.utc).isocalendar()[1]
    year = datetime.now(timezone.utc).year
    
    # Check if gift already collected this week
    collected = await db.collected_gifts.find_one({
        "student_id": current_user['id'],
        "week_number": week_number,
        "year": year
    }, {"_id": 0})
    
    # Get gift for this week (rotate through available gifts)
    gifts = await db.weekend_gifts.find({"active": True}, {"_id": 0}).to_list(100)
    if not gifts:
        # Create default gifts if none exist
        await create_default_gifts()
        gifts = await db.weekend_gifts.find({"active": True}, {"_id": 0}).to_list(100)
    
    gift_index = week_number % len(gifts)
    gift = gifts[gift_index]
    gift['is_collected'] = collected is not None
    
    return gift


@router.post("/student/collect-gift")
async def collect_gift(data: dict, current_user: dict = Depends(get_current_user)):
    """Mark gift as collected and add stars"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    week_number = datetime.now(timezone.utc).isocalendar()[1]
    year = datetime.now(timezone.utc).year
    
    # Check if already collected
    existing = await db.collected_gifts.find_one({
        "student_id": current_user['id'],
        "week_number": week_number,
        "year": year
    })
    
    if existing:
        return {"message": "Gift already collected"}
    
    # Get the gift details
    gift = await db.weekend_gifts.find_one({"id": data['gift_id']}, {"_id": 0})
    
    # Save collection
    collection = {
        "id": str(uuid4()),
        "student_id": current_user['id'],
        "gift_id": data['gift_id'],
        "word_french": gift['word_french'],
        "word_english": gift['word_english'],
        "image_url": gift['image_url'],
        "week_number": week_number,
        "year": year,
        "collected_at": datetime.now(timezone.utc).isoformat()
    }
    await db.collected_gifts.insert_one(collection)
    
    # Add 10 stars to user
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"stars": 10}}
    )
    
    return {"message": "Gift collected!", "stars_earned": 10}


@router.get("/student/my-collected-gifts")
async def get_collected_gifts(current_user: dict = Depends(get_current_user)):
    """Get all collected gifts"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    gifts = await db.collected_gifts.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).sort("collected_at", -1).to_list(100)
    
    return gifts

async def create_default_gifts():
    """Create default weekend gifts"""
    default_gifts = [
        {
            "id": str(uuid4()),
            "word_french": "Chat",
            "word_english": "Cat",
            "image_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Chien",
            "word_english": "Dog",
            "image_url": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Papillon",
            "word_english": "Butterfly",
            "image_url": "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Pomme",
            "word_english": "Apple",
            "image_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Soleil",
            "word_english": "Sun",
            "image_url": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=400",
            "audio_url": "",
            "active": True
        }
    ]
    
    await db.weekend_gifts.insert_many(default_gifts)

# ============ PROMO CODE ROUTES ============


