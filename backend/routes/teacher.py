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

@router.get("/teacher/documents-from-admin")
async def get_teacher_documents_from_admin(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    documents = await db.documents.find(
        {"to_user_id": current_user['id'], "from_user_role": "admin"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return documents


@router.post("/teacher/send-document-to-admin")
async def teacher_send_document_to_admin(doc_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher sends a document to admin"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get admin user
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    document = {
        "id": str(uuid4()),
        "from_user_id": current_user['id'],
        "from_user_role": "teacher",
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
        data={"message": f"Nouveau document du professeur {current_user['first_name']}: {doc_data['title']}"}
    )
    
    logger.info(f"Document sent by teacher {current_user['id']} to admin")
    return {"message": "Document sent to admin successfully"}


@router.post("/teacher/send-kkid-video")
async def teacher_send_kkid_video(video_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher uploads and sends a video to a specific K-Kid student"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Verify the student exists and is a K-Kid
    student = await db.users.find_one({"id": video_data['student_id']}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student.get('level') != 'kkid':
        raise HTTPException(status_code=400, detail="Only K-Kid students can receive these videos")
    
    video = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "teacher_name": f"{current_user['first_name']} {current_user['last_name']}",
        "student_id": video_data['student_id'],
        "student_name": f"{student['first_name']} {student['last_name']}",
        "title": video_data['title'],
        "description": video_data.get('description', ''),
        "video_url": video_data['video_url'],
        "thumbnail_url": video_data.get('thumbnail_url', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.kkid_videos.insert_one(video)
    
    # Create notification for the K-Kid student
    await create_notification(
        user_id=video_data['student_id'],
        notification_type="new_video",
        data={"message": f"Nouvelle vidéo de {current_user['first_name']}: {video_data['title']}"}
    )
    
    logger.info(f"K-Kid video uploaded by teacher {current_user['id']} for student {video_data['student_id']}: {video_data['title']}")
    return {"message": "Vidéo envoyée avec succès à l'élève K-Kid", "video": video}


@router.delete("/teacher/delete-kkid-video/{video_id}")
async def delete_kkid_video(video_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a K-Kid video"""
    if current_user['role'] not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")
    
    result = await db.kkid_videos.delete_one({"id": video_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    logger.info(f"K-Kid video {video_id} deleted by {current_user['role']} {current_user['id']}")
    return {"message": "Vidéo supprimée avec succès"}

# ========== COURSE SUMMARIES / REVISION SYSTEM ==========


@router.post("/teacher/create-course-summary")
async def create_course_summary(summary_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher creates a course summary with rich text formatting"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    summary = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "teacher_name": f"{current_user['first_name']} {current_user['last_name']}",
        "title": summary_data['title'],
        "content": summary_data['content'],  # HTML content with formatting
        "comments": summary_data.get('comments', ''),
        "student_ids": summary_data.get('student_ids', []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.course_summaries.insert_one(summary)
    
    # Notify students
    for student_id in summary_data.get('student_ids', []):
        await create_notification(
            user_id=student_id,
            title="Nouveau résumé de cours",
            message=f"Nouveau résumé de cours: {summary_data['title']}",
            notification_type="new_summary"
        )
    
    logger.info(f"Course summary created by teacher {current_user['id']}: {summary_data['title']}")
    return {"message": "Résumé de cours créé avec succès", "summary_id": summary["id"]}


@router.get("/teacher/my-course-summaries")
async def get_teacher_course_summaries(current_user: dict = Depends(get_current_user)):
    """Get all course summaries created by the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    summaries = await db.course_summaries.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with student names
    for summary in summaries:
        student_names = []
        for sid in summary.get('student_ids', []):
            student = await db.users.find_one({"id": sid}, {"_id": 0, "first_name": 1, "last_name": 1})
            if student:
                student_names.append(f"{student['first_name']} {student['last_name']}")
        summary['student_names'] = student_names
        
        # Get question count
        questions = await db.summary_questions.count_documents({"summary_id": summary['id']})
        summary['question_count'] = questions
    
    return summaries


@router.put("/teacher/update-course-summary/{summary_id}")
async def update_course_summary(summary_id: str, summary_data: dict, current_user: dict = Depends(get_current_user)):
    """Update a course summary"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.course_summaries.update_one(
        {"id": summary_id, "teacher_id": current_user['id']},
        {"$set": {
            "title": summary_data.get('title'),
            "content": summary_data.get('content'),
            "comments": summary_data.get('comments', ''),
            "student_ids": summary_data.get('student_ids', []),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return {"message": "Résumé mis à jour avec succès"}


@router.delete("/teacher/delete-course-summary/{summary_id}")
async def delete_course_summary(summary_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a course summary"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.course_summaries.delete_one({"id": summary_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Also delete related questions
    await db.summary_questions.delete_many({"summary_id": summary_id})
    
    return {"message": "Résumé supprimé avec succès"}


@router.delete("/teacher/delete-question/{question_id}")
async def delete_teacher_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Teacher deletes a question"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.summary_questions.delete_one({
        "id": question_id,
        "teacher_id": current_user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question supprimée"}


@router.put("/teacher/mark-question-read/{question_id}")
async def mark_question_read(question_id: str, current_user: dict = Depends(get_current_user)):
    """Teacher marks question as read"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    await db.summary_questions.update_one(
        {"id": question_id, "teacher_id": current_user['id']},
        {"$set": {"question_read": True}}
    )
    return {"message": "Question marquée comme lue"}


@router.get("/teacher/summary-questions/{summary_id}")
async def get_summary_questions(summary_id: str, current_user: dict = Depends(get_current_user)):
    """Get all questions for a specific summary"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    questions = await db.summary_questions.find(
        {"summary_id": summary_id, "teacher_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return questions


@router.get("/teacher/all-summary-questions")
async def get_all_summary_questions(current_user: dict = Depends(get_current_user)):
    """Get all unanswered questions for the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    questions = await db.summary_questions.find(
        {"teacher_id": current_user['id'], "answer": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with summary titles
    for q in questions:
        summary = await db.course_summaries.find_one({"id": q['summary_id']}, {"_id": 0, "title": 1})
        q['summary_title'] = summary['title'] if summary else "Résumé supprimé"
    
    return questions


@router.post("/teacher/answer-summary-question/{question_id}")
async def answer_summary_question(question_id: str, answer_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher answers a student's question (text or audio)"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    update_data = {
        "answered_at": datetime.now(timezone.utc).isoformat(),
        "answer_read": False
    }
    
    if answer_data.get('answer'):
        update_data['answer'] = answer_data['answer']
    if answer_data.get('answer_audio_url'):
        update_data['answer_audio_url'] = answer_data['answer_audio_url']
    
    result = await db.summary_questions.update_one(
        {"id": question_id, "teacher_id": current_user['id']},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get question to notify student
    question = await db.summary_questions.find_one({"id": question_id}, {"_id": 0})
    if question:
        # Database notification
        await create_notification(
            user_id=question['student_id'],
            title="Réponse du professeur",
            message="Réponse du professeur à votre question",
            notification_type="summary_answer"
        )
        
        # Real-time WebSocket notification to student
        try:
            await ws_manager.send_personal_notification(
                user_id=question['student_id'],
                notification={
                    "type": "new_answer",
                    "title": "✅ Réponse reçue",
                    "message": f"Le professeur {current_user['first_name']} a répondu à votre question",
                    "summary_id": question.get('summary_id'),
                    "question_id": question_id,
                    "teacher_name": f"{current_user['first_name']} {current_user['last_name']}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification: {e}")
    
    return {"message": "Réponse envoyée avec succès"}


@router.post("/teacher/upload-audio-answer")
async def upload_audio_answer(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload audio file for voice answer"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Validate file type
    allowed_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/webm', 'audio/ogg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    
    # Save file
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp3'
    unique_filename = f"audio_{uuid4()}.{file_extension}"
    file_path = f"/app/frontend/public/uploads/audio/{unique_filename}"
    
    # Ensure directory exists
    os.makedirs("/app/frontend/public/uploads/audio", exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    file_url = f"/uploads/audio/{unique_filename}"
    logger.info(f"Audio answer uploaded by teacher {current_user['id']}: {file_url}")
    
    return {"file_url": file_url, "message": "Audio uploadé avec succès"}


@router.post("/teacher/set-availability")
async def set_teacher_availability(availability_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # availability_data format: { "monday": ["09:00", "10:00", "14:00"], "tuesday": [...], ... }
    availability = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "availability": availability_data['availability'],
        "week_start": availability_data.get('week_start', datetime.now(timezone.utc).isoformat()),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Replace existing availability
    await db.teacher_availability.delete_many({"teacher_id": current_user['id']})
    await db.teacher_availability.insert_one(availability)
    
    logger.info(f"Availability set by teacher {current_user['id']}")
    return {"message": "Availability updated successfully"}


@router.get("/teacher/my-availability")
async def get_my_availability(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    availability = await db.teacher_availability.find_one(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    )
    
    return availability or {"availability": {}}

# ============ LEAVE REQUEST ENDPOINTS ============


@router.get("/teacher/my-leave-requests")
async def get_my_leave_requests(current_user: dict = Depends(get_current_user)):
    """Get all leave requests for the connected teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    leaves = await db.leave_requests.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return leaves


@router.get("/teacher/my-leave-balance")
async def get_my_leave_balance(current_user: dict = Depends(get_current_user)):
    """Get leave balance for the connected teacher"""
    if current_user['role'] not in ['teacher', 'secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Employee access required")
    
    balance = await db.leave_balances.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    created_at = current_user.get('created_at')
    if isinstance(created_at, str):
        try:
            from dateutil import parser as dt_parser
            created_date = dt_parser.parse(created_at)
        except Exception:
            created_date = datetime.now(timezone.utc)
    elif isinstance(created_at, datetime):
        created_date = created_at
    else:
        created_date = datetime.now(timezone.utc)
    
    now = datetime.now(timezone.utc)
    if created_date.tzinfo is None:
        from datetime import timezone as tz
        created_date = created_date.replace(tzinfo=tz.utc)
    
    months_worked = max(0, (now.year - created_date.year) * 12 + (now.month - created_date.month))
    total_earned = round(months_worked * 2.5, 1)
    if total_earned > 30:
        total_earned = 30.0
    
    total_taken = balance.get('total_taken', 0) if balance else 0
    remaining = total_earned - total_taken
    
    return {
        "months_worked": months_worked,
        "total_earned": total_earned,
        "total_taken": total_taken,
        "remaining": remaining
    }




@router.post("/teacher/leave-request")
async def create_leave_request(leave_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Teacher submits a leave request"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    start_date = leave_data.get('start_date')
    end_date = leave_data.get('end_date')
    reason = leave_data.get('reason', '')
    
    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="Start and end dates are required")
    
    leave_request = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "teacher_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        "teacher_email": current_user.get('email', ''),
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "status": "pending",  # pending, approved, rejected
        "admin_comment": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.leave_requests.insert_one(leave_request)
    
    # Notify admin (create notification)
    admin_users = await db.users.find({"role": "admin"}, {"_id": 0, "id": 1}).to_list(10)
    for admin in admin_users:
        notification = {
            "id": str(uuid4()),
            "user_id": admin['id'],
            "message": f"🏖️ Nouvelle demande de congé de {leave_request['teacher_name']} ({start_date} → {end_date})",
            "read": False,
            "link": "/admin?tab=leave-requests",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    logger.info(f"Leave request created by {leave_request['teacher_name']}: {start_date} to {end_date}")
    return {"message": "Leave request submitted", "id": leave_request['id']}


@router.delete("/teacher/leave-request/{leave_id}")
async def cancel_leave_request(leave_id: str, current_user: dict = Depends(get_current_user)):
    """Teacher cancels their own pending leave request"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Only allow canceling own pending requests
    leave = await db.leave_requests.find_one({"id": leave_id, "teacher_id": current_user['id']})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.get('status') != 'pending':
        raise HTTPException(status_code=400, detail="Can only cancel pending requests")
    
    await db.leave_requests.delete_one({"id": leave_id})
    return {"message": "Leave request cancelled"}

# Admin endpoints for leave management


@router.post("/teacher/create-group-code")
async def create_group_code(code_data: GroupCodeCreate, current_user: dict = Depends(get_current_user)):
    """Teacher creates a group code for students to join"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Generate unique code
    code = generate_unique_code()
    
    # Ensure code is unique
    while await db.group_codes.find_one({"code": code}, {"_id": 0}):
        code = generate_unique_code()
    
    # Create group code
    group_code = GroupCode(
        code=code,
        teacher_id=current_user['id'],
        teacher_name=f"{current_user['first_name']} {current_user['last_name']}",
        group_name=code_data.group_name,
        level=code_data.level,
        max_students=code_data.max_students,
        current_students=0,
        is_active=True
    )
    
    doc = group_code.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.group_codes.insert_one(doc)
    
    # Retrieve the inserted document without _id
    created_code = await db.group_codes.find_one({"id": group_code.id}, {"_id": 0})
    
    logger.info(f"Group code {code} created by teacher {current_user['id']}")
    
    return {
        "message": "Code de groupe créé avec succès",
        "group_code": created_code
    }


@router.get("/teacher/my-group-codes")
async def get_my_group_codes(current_user: dict = Depends(get_current_user)):
    """Get all group codes created by the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    codes = await db.group_codes.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    return codes


@router.put("/teacher/toggle-group-code/{code_id}")
async def toggle_group_code(code_id: str, current_user: dict = Depends(get_current_user)):
    """Activate or deactivate a group code"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    code = await db.group_codes.find_one(
        {"id": code_id, "teacher_id": current_user['id']},
        {"_id": 0}
    )
    
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    new_status = not code['is_active']
    
    await db.group_codes.update_one(
        {"id": code_id},
        {"$set": {"is_active": new_status}}
    )
    
    logger.info(f"Group code {code['code']} toggled to {new_status} by teacher {current_user['id']}")
    
    return {
        "message": f"Code {'activé' if new_status else 'désactivé'} avec succès",
        "is_active": new_status
    }


@router.get("/teacher/pending-group-students")
async def get_pending_group_students(current_user: dict = Depends(get_current_user)):
    """Get students assigned to teacher waiting for magic code generation"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    logger.info(f"Teacher {current_user['id']} requesting pending group students")
    
    # Find students assigned to this teacher, with course_type='group' and not yet active
    query = {
        "assigned_teacher": current_user['id'],
        "course_type": "group",
        "is_active": False
    }
    logger.info(f"Query: {query}")
    
    students = await db.users.find(
        query,
        {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1, "members": 1, "level": 1, "created_at": 1}
    ).to_list(1000)
    
    logger.info(f"Teacher {current_user['id']} retrieved {len(students)} pending group students")
    
    return students


@router.post("/teacher/generate-group-magic-code")
async def generate_group_magic_code(
    data: GenerateGroupMagicCode,
    current_user: dict = Depends(get_current_user)
):
    """Teacher generates a magic code for selected group students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    if not data.student_ids or len(data.student_ids) == 0:
        raise HTTPException(status_code=400, detail="Veuillez sélectionner au moins un étudiant")
    
    # Verify all students belong to this teacher and are pending
    students = await db.users.find(
        {
            "id": {"$in": data.student_ids},
            "assigned_teacher": current_user['id'],
            "course_type": "group",
            "is_active": False
        },
        {"_id": 0}
    ).to_list(1000)
    
    if len(students) != len(data.student_ids):
        raise HTTPException(
            status_code=400, 
            detail="Certains étudiants ne sont pas valides ou ont déjà un code"
        )
    
    # Generate unique magic code (8 characters)
    magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure code is unique
    while await db.users.find_one({"temporary_password": magic_code}, {"_id": 0}):
        magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Update all selected students with the same magic code
    hashed_password = pwd_context.hash(magic_code)
    
    for student in students:
        # Get main member info for login compatibility
        main_member = next((m for m in student.get('members', []) if m.get('is_main')), student.get('members', [{}])[0] if student.get('members') else {})
        
        await db.users.update_one(
            {"id": student['id']},
            {"$set": {
                "is_active": True,
                "is_approved": True,
                "password_hash": hashed_password,
                "temporary_password": magic_code,
                "magic_code_generated": True,
                "magic_code_generated_at": datetime.now(timezone.utc).isoformat(),
                "magic_code_generated_by": current_user['id'],
                "group_magic_code_name": data.group_name,
                "first_name": main_member.get('first_name', student.get('first_name', '')),
                "last_name": main_member.get('last_name', student.get('last_name', ''))
            }}
        )
    
    logger.info(f"Magic code {magic_code} generated for {len(students)} students in group '{data.group_name}' by teacher {current_user['id']}")
    
    # Create notification for admin
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0, "id": 1})
    if admin:
        student_names = ", ".join([
            f"{s.get('first_name', '')} {s.get('last_name', '')}" 
            for s in students
        ])
        await create_notification(
            admin['id'],
            'Code de groupe généré',
            f"Le professeur {current_user['first_name']} {current_user['last_name']} a généré le code {magic_code} pour le groupe '{data.group_name}' ({len(students)} étudiants: {student_names})",
            'group_code_generated'
        )
    
    return {
        "success": True,
        "magic_code": magic_code,
        "group_name": data.group_name,
        "student_count": len(students),
        "students": [
            {
                "id": s['id'],
                "name": f"{s.get('first_name', '')} {s.get('last_name', '')}",
                "email": s['email']
            }
            for s in students
        ]
    }


@router.get("/teacher/my-generated-groups")
async def get_my_generated_groups(current_user: dict = Depends(get_current_user)):
    """Get all groups with magic codes generated by this teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Find all students where this teacher generated their magic code
    groups = await db.users.find(
        {
            "magic_code_generated_by": current_user['id'],
            "magic_code_generated": True,
            "course_type": "group"
        },
        {"_id": 0}
    ).to_list(1000)
    
    # Group by magic code
    grouped = {}
    for student in groups:
        code = student.get('temporary_password', '')
        if code not in grouped:
            grouped[code] = {
                "magic_code": code,
                "group_name": student.get('group_magic_code_name', 'Groupe sans nom'),
                "created_at": student.get('magic_code_generated_at', ''),
                "students": []
            }
        
        grouped[code]['students'].append({
            "id": student['id'],
            "name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
            "email": student['email'],
            "level": student.get('level', ''),
            "members": student.get('members', [])
        })
    
    # Convert to list and sort by creation date
    result = list(grouped.values())
    result.sort(key=lambda x: x['created_at'], reverse=True)
    
    return result


@router.get("/teacher/my-students")
async def get_my_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    students = await db.users.find(
        {"assigned_teacher": current_user['id']},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    return students


@router.get("/teacher/my-courses")
async def get_my_courses(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    courses = await db.courses.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return courses


@router.get("/teacher/my-payments")
async def get_teacher_my_payments(current_user: dict = Depends(get_current_user)):
    """Get all payment slips for the connected teacher (filtered by visibility date)"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Search by teacher_id OR by email match
    teacher_email = current_user.get('email', '')
    teacher_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
    
    all_payments = await db.teacher_payments.find({
        "$or": [
            {"teacher_id": current_user['id']},
            {"teacher_email": teacher_email},
            {"email": teacher_email},
            {"teacher_name": teacher_name}
        ]
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    now = datetime.now(timezone.utc)
    visible_payments = []
    
    # Calculate net amount for each payment and filter by visibility
    for payment in all_payments:
        amount = float(payment.get('amount', 0))
        bonus = float(payment.get('bonus', 0))
        deductions = int(payment.get('deductions', 0))
        currency = payment.get('currency', 'EUR')
        deduction_unit = 5 if currency == 'EUR' else 1500
        deductions_amount = deductions * deduction_unit
        payment['montant_initial'] = amount + bonus
        payment['deductions_amount'] = deductions_amount
        payment['montant_net'] = max(0, amount + bonus - deductions_amount)
        
        # Check visibility date
        visible_from = payment.get('visible_from')
        if visible_from:
            try:
                visible_date = datetime.fromisoformat(visible_from.replace('Z', '+00:00'))
                if now >= visible_date:
                    visible_payments.append(payment)
            except:
                visible_payments.append(payment)
        else:
            # Old payments without visibility date - show them
            visible_payments.append(payment)
    
    return visible_payments


@router.get("/teacher/upcoming-balance")
async def get_teacher_upcoming_balance(current_user: dict = Depends(get_current_user)):
    """Get the upcoming balance for the teacher (visible from 25th of month)"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    now = datetime.now(timezone.utc)
    day_of_month = now.day
    
    # Only available from the 25th of the month
    if day_of_month < 25:
        return {
            "available": False,
            "message": "Le solde à venir sera disponible à partir du 25 du mois",
            "available_from": 25 - day_of_month
        }
    
    # Search by teacher_id OR by email match
    teacher_email = current_user.get('email', '')
    teacher_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
    
    # Get current month's pending payments (created between 25-28)
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()
    current_month_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc).isoformat() if now.month < 12 else datetime(now.year + 1, 1, 1, tzinfo=timezone.utc).isoformat()
    
    pending_payments = await db.teacher_payments.find({
        "$or": [
            {"teacher_id": current_user['id']},
            {"teacher_email": teacher_email},
            {"email": teacher_email},
            {"teacher_name": teacher_name}
        ],
        "created_at": {"$gte": current_month_start, "$lt": current_month_end},
        "status": "pending"
    }, {"_id": 0}).to_list(100)
    
    total_upcoming = 0
    upcoming_details = []
    
    for payment in pending_payments:
        amount = float(payment.get('amount', 0))
        bonus = float(payment.get('bonus', 0))
        deductions = int(payment.get('deductions', 0))
        currency = payment.get('currency', 'EUR')
        deduction_unit = 5 if currency == 'EUR' else 1500
        deductions_amount = deductions * deduction_unit
        montant_net = max(0, amount + bonus - deductions_amount)
        
        total_upcoming += montant_net
        upcoming_details.append({
            "month": payment.get('month'),
            "montant_net": montant_net,
            "currency": currency,
            "visible_from": payment.get('visible_from')
        })
    
    return {
        "available": True,
        "total_upcoming": total_upcoming,
        "currency": upcoming_details[0]['currency'] if upcoming_details else 'EUR',
        "details": upcoming_details,
        "message": f"Solde à venir pour ce mois: {total_upcoming} {upcoming_details[0]['currency'] if upcoming_details else 'EUR'}",
        "bulletin_visible_from": "29 du mois" if day_of_month < 29 else "Disponible maintenant"
    }


@router.post("/teacher/create-course")
async def create_course(course_data: CourseCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    course = Course(
        teacher_id=current_user['id'],
        title=course_data.title,
        description=course_data.description,
        level=course_data.level,
        schedule=course_data.schedule
    )
    
    doc = course.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.courses.insert_one(doc)
    
    return {"message": "Course created", "course": course}

# New models for enhanced teacher features
class CourseCreateEnhanced(BaseModel):
    title: str
    description: str
    level: str
    schedule: str
    student_id: Optional[str] = None
    meet_link: Optional[str] = None

class HomeworkDocumentCreate(BaseModel):
    title: str
    description: str
    recipient_type: str  # 'admin' or 'student'
    recipient_id: Optional[str] = None
    file_url: str

class HomeworkDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    title: str
    description: str
    recipient_type: str
    recipient_id: Optional[str] = None
    file_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionAction(BaseModel):
    action: str  # 'start', 'pause', 'resume', 'end'
    elapsed_time: Optional[int] = None
    paused_duration: Optional[int] = None

# Enhanced teacher routes


@router.post("/teacher/create-course")
async def create_course_enhanced(course_data: CourseCreateEnhanced, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")


@router.post("/teacher/upload-file")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Pour simplifier, on stocke juste le nom du fichier
    # En production, il faudrait uploader vers S3, Google Cloud Storage, etc.
    file_url = f"/uploads/{current_user['id']}/{file.filename}"
    
    logger.info(f"File uploaded by teacher {current_user['id']}: {file.filename}")
    
    return {
        "message": "File uploaded successfully",
        "file_url": file_url,
        "filename": file.filename
    }

# Student routes for links, documents and homeworks


@router.post("/teacher/send-link")
async def teacher_send_link(link_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    link = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "from_teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
        "student_id": link_data['student_id'],
        "title": link_data['title'],
        "description": link_data.get('description', ''),
        "url": link_data['url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.student_links.insert_one(link)
    logger.info(f"Link sent by teacher {current_user['id']} to student {link_data['student_id']}")
    
    # Create notification for student
    await create_notification(link_data['student_id'], 'new_link', {
        "title": link_data['title'],
        "from_name": f"{teacher['first_name']} {teacher['last_name']}"
    })
    
    return {"message": "Link sent successfully"}

# Route for teacher to get homeworks from their students


@router.get("/teacher/student-homeworks")
async def get_teacher_student_homeworks(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    homeworks = await db.student_homeworks.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    return homeworks


@router.post("/teacher/create-course-enhanced")
async def create_course_new(course_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    course = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "title": course_data.title,
        "description": course_data.description,
        "level": course_data.level,
        "schedule": course_data.schedule,
        "student_id": course_data.student_id,
        "meet_link": course_data.meet_link,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.courses.insert_one(course)
    return {"message": "Course created", "course": course}


@router.get("/teacher/my-documents")
async def get_my_documents(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    documents = await db.documents.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return documents


@router.post("/teacher/send-document")
async def send_homework_document(doc_data: HomeworkDocumentCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get teacher info
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    document = HomeworkDocument(
        teacher_id=current_user['id'],
        title=doc_data.title,
        description=doc_data.description,
        recipient_type=doc_data.recipient_type,
        recipient_id=doc_data.recipient_id if doc_data.recipient_type == 'student' else None,
        file_url=doc_data.file_url
    )
    
    doc = document.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['from_teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
    await db.documents.insert_one(doc)
    
    # Create notification for recipient
    if doc_data.recipient_type == 'student' and doc_data.recipient_id:
        await create_notification(doc_data.recipient_id, 'new_document', {
            "title": doc_data.title,
            "from_name": f"{teacher['first_name']} {teacher['last_name']}"
        })
    
    logger.info(f"Document sent by teacher {current_user['id']} to {doc_data.recipient_type}")
    return {"message": "Document sent successfully", "document": document}


@router.post("/teacher/session/start")
async def start_session(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "teacher_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        "teacher_email": current_user.get('email', ''),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "in_progress",
        "pauses": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.teacher_sessions.insert_one(session)
    logger.info(f"Session started by teacher {current_user['id']}")
    return {"message": "Session started", "session_id": session['id']}


@router.post("/teacher/session/pause")
async def pause_session(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = await db.teacher_sessions.find_one(
        {"teacher_id": current_user['id'], "status": "in_progress"},
        {"_id": 0},
        sort=[("start_time", -1)]
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    pause_record = {
        "pause_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.teacher_sessions.update_one(
        {"id": session['id']},
        {"$push": {"pauses": pause_record}}
    )
    
    logger.info(f"Session paused by teacher {current_user['id']}")
    return {"message": "Session paused"}


@router.post("/teacher/session/resume")
async def resume_session(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = await db.teacher_sessions.find_one(
        {"teacher_id": current_user['id'], "status": "in_progress"},
        {"_id": 0},
        sort=[("start_time", -1)]
    )
    
    if not session or not session.get('pauses'):
        raise HTTPException(status_code=404, detail="No paused session found")
    
    await db.teacher_sessions.update_one(
        {"id": session['id'], "pauses.resume_time": {"$exists": False}},
        {"$set": {"pauses.$[elem].resume_time": datetime.now(timezone.utc).isoformat()}},
        array_filters=[{"elem.resume_time": {"$exists": False}}]
    )
    
    logger.info(f"Session resumed by teacher {current_user['id']}")
    return {"message": "Session resumed"}


@router.post("/teacher/session/end")
async def end_session(session_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = await db.teacher_sessions.find_one(
        {"teacher_id": current_user['id'], "status": "in_progress"},
        {"_id": 0},
        sort=[("start_time", -1)]
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Update session with end time and total duration
    await db.teacher_sessions.update_one(
        {"id": session['id']},
        {"$set": {
            "end_time": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "total_time_seconds": session_data.get('total_time', 0),
            "paused_duration_seconds": session_data.get('paused_duration', 0)
        }}
    )
    
    # Get teacher and admin info
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    # Create notification for admin
    notification = {
        "id": str(uuid.uuid4()),
        "type": "session_completed",
        "teacher_id": current_user['id'],
        "teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
        "session_id": session['id'],
        "start_time": session['start_time'],
        "end_time": datetime.now(timezone.utc).isoformat(),
        "total_time_seconds": session_data.get('total_time', 0),
        "paused_duration_seconds": session_data.get('paused_duration', 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False
    }
    
    await db.admin_notifications.insert_one(notification)
    
    logger.info(f"Session ended by teacher {current_user['id']}, notification sent to admin")
    return {"message": "Session completed and sent to admin"}

# Admin endpoint to get all teacher sessions (for attendance tracking)


@router.get("/teacher/my-group-courses")
async def get_teacher_group_courses(current_user: dict = Depends(get_current_user)):
    """Get group courses assigned to the current teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Accès réservé aux professeurs")
    
    courses = await db.group_courses.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Enrichir avec les noms des étudiants
    for course in courses:
        student_names = []
        for sid in course.get('student_ids', []):
            student = await db.users.find_one({"id": sid}, {"_id": 0, "first_name": 1, "last_name": 1})
            if student:
                student_names.append({"id": sid, "name": f"{student['first_name']} {student['last_name']}"})
        course['students'] = student_names
        course['enrolled_count'] = len(course.get('student_ids', []))
    
    return courses


@router.post("/teacher/attendance")
async def mark_attendance(attendance_data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    attendance = Attendance(
        teacher_id=current_user['id'],
        date=datetime.fromisoformat(attendance_data.date),
        status=attendance_data.status
    )
    
    doc = attendance.model_dump()
    doc['date'] = doc['date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.attendances.insert_one(doc)
    
    return {"message": "Attendance marked"}


@router.get("/teacher/attendance")
async def get_my_attendance(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    attendances = await db.attendances.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return attendances

# MESSAGING


@router.post("/teacher/send-meet-link")
async def send_meet_link(data: MeetLinkCreate, current_user: dict = Depends(get_current_user)):
    """Teacher sends a Google Meet link to a student"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    meet_link = MeetLink(
        student_id=data.student_id,
        teacher_id=current_user['id'],
        meet_link=data.meet_link,
        title=data.title,
        scheduled_date=datetime.fromisoformat(data.scheduled_date.replace('Z', '+00:00'))
    )
    
    doc = meet_link.model_dump()
    doc['scheduled_date'] = doc['scheduled_date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    # Add teacher name for display in student dashboard
    doc['teacher_name'] = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
    await db.meet_links.insert_one(doc)
    
    # Create notification for student
    await create_notification(
        user_id=data.student_id,
        title="📅 Nouveau cours programmé",
        message=f"Votre professeur vous a envoyé un lien de cours: {data.title}",
        notification_type="meet_link"
    )
    
    # 🎁 Coffre aux Trésors: Ajouter +1 point pour chaque lien de cours reçu
    await add_student_points(
        student_id=data.student_id, 
        points=1, 
        reason=f"Lien de cours reçu: {data.title}"
    )
    
    logger.info(f"Meet link sent by teacher {current_user['id']} to student {data.student_id}")
    return {"message": "Lien de cours envoyé", "meet_link_id": meet_link.id}


@router.get("/teacher/students-availability")
async def get_students_availability_for_teacher(current_user: dict = Depends(get_current_user)):
    """Teacher gets availability of their assigned students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get teacher's assigned students
    students = await db.users.find(
        {"role": "student", "assigned_teacher": current_user['id']},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    ).to_list(1000)
    
    student_ids = [s['id'] for s in students]
    
    # Get availability for these students
    availabilities = await db.student_availability.find(
        {"student_id": {"$in": student_ids}},
        {"_id": 0}
    ).to_list(1000)
    
    # Merge student info with availability
    result = []
    for student in students:
        avail = next((a for a in availabilities if a['student_id'] == student['id']), {"slots": []})
        result.append({
            "student_id": student['id'],
            "student_name": f"{student['first_name']} {student['last_name']}",
            "email": student.get('email'),
            "slots": avail.get('slots', []),
            "updated_at": avail.get('updated_at')
        })
    
    return result


@router.get("/teacher/my-group-courses")
async def get_teacher_group_courses(current_user: dict = Depends(get_current_user)):
    """Get all group courses taught by the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    courses = await db.group_courses.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    for course in courses:
        course['enrolled_count'] = len(course.get('current_students', []))
        # Get student details
        course['students'] = []
        for student_id in course.get('current_students', []):
            student = await db.users.find_one(
                {"id": student_id},
                {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
            )
            if student:
                course['students'].append(student)
    
    return courses


@router.post("/teacher/group-courses/{course_id}/send-link")
async def send_group_meet_link(course_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Send meet link to all students in a group course"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    course = await db.group_courses.find_one({"id": course_id, "teacher_id": current_user['id']}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    # Update course meet link
    await db.group_courses.update_one(
        {"id": course_id},
        {"$set": {"meet_link": data.get('meet_link', '')}}
    )
    
    # Send notification and points to each student
    for student_id in course.get('current_students', []):
        await create_notification(
            user_id=student_id,
            title="📅 Cours groupé - Nouveau lien",
            message=f"Votre professeur a partagé le lien pour: {course['title']}",
            notification_type="meet_link"
        )
        # 🎁 +2 points pour chaque lien reçu
        await add_student_points(
            student_id=student_id,
            points=2,
            reason=f"Lien cours groupé: {course['title']}"
        )
    
    logger.info(f"Group meet link sent to {len(course.get('current_students', []))} students for course {course_id}")
    return {"message": f"Lien envoyé à {len(course.get('current_students', []))} étudiants"}


@router.post("/teacher/create-flashcard-set")
async def create_flashcard_set(data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher creates a new flashcard set"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    flashcard_set = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "flashcards": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.flashcard_sets.insert_one(flashcard_set)
    return {"message": "Flashcard set created", "set_id": flashcard_set['id']}


@router.post("/teacher/add-flashcard")
async def add_flashcard(data: dict, current_user: dict = Depends(get_current_user)):
    """Add a flashcard to a set"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    flashcard = {
        "id": str(uuid4()),
        "question": data['question'],
        "answer": data['answer']
    }
    
    result = await db.flashcard_sets.update_one(
        {"id": data['set_id'], "teacher_id": current_user['id']},
        {"$push": {"flashcards": flashcard}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    
    return {"message": "Flashcard added"}


@router.get("/teacher/my-flashcard-sets")
async def get_teacher_flashcard_sets(current_user: dict = Depends(get_current_user)):
    """Get all flashcard sets created by teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    sets = await db.flashcard_sets.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    return sets


@router.delete("/teacher/delete-flashcard-set/{set_id}")
async def delete_flashcard_set(set_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a flashcard set"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.flashcard_sets.delete_one({"id": set_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    
    return {"message": "Flashcard set deleted"}


@router.post("/teacher/assign-game")
async def assign_game(data: dict, current_user: dict = Depends(get_current_user)):
    """Assign a game (flashcard, kahoot, quiz, memory) to one or multiple students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Support single student_id or multiple student_ids
    student_ids = data.get('student_ids', [])
    if not student_ids and data.get('student_id'):
        student_ids = [data['student_id']]
    
    if not student_ids:
        raise HTTPException(status_code=400, detail="Au moins un étudiant requis")
    
    assigned_count = 0
    teacher_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}"
    
    for student_id in student_ids:
        assignment = {
            "id": str(uuid4()),
            "teacher_id": current_user['id'],
            "student_id": student_id,
            "game_type": data['game_type'],  # 'flashcard', 'kahoot', 'quiz', 'memory'
            "game_id": data.get('game_id'),  # flashcard/quiz/memory set id
            "game_url": data.get('game_url'),  # kahoot link
            "title": data['title'],
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "completed": False,
            "score": None
        }
        
        await db.game_assignments.insert_one(assignment)
        assigned_count += 1
        
        # Create notification for the student
        game_type_labels = {
            'flashcard': 'Flashcards',
            'kahoot': 'Kahoot',
            'quiz': 'Quiz',
            'memory': 'Memory'
        }
        game_label = game_type_labels.get(data['game_type'], 'Jeu')
        
        notification = {
            "id": str(uuid4()),
            "user_id": student_id,
            "type": "game_assigned",
            "title": f"🎮 Nouveau {game_label} assigné !",
            "message": f"{teacher_name} vous a assigné: {data['title']}",
            "data": {
                "game_type": data['game_type'],
                "game_id": data.get('game_id'),
                "assignment_id": assignment['id']
            },
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    return {
        "message": f"Jeu assigné à {assigned_count} étudiant(s)",
        "assigned_count": assigned_count
    }

# ============== QUIZ GAME ENDPOINTS ==============


@router.post("/teacher/create-quiz")
async def create_quiz(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new quiz with multiple choice questions"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    quiz = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "questions": [],  # Will contain {id, question, options[], correct_answer}
        "time_limit": data.get('time_limit', 0),  # seconds per question, 0 = no limit
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.quizzes.insert_one(quiz)
    return {"message": "Quiz créé", "quiz_id": quiz['id']}


@router.post("/teacher/add-quiz-question")
async def add_quiz_question(data: dict, current_user: dict = Depends(get_current_user)):
    """Add a question to a quiz"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    question = {
        "id": str(uuid4()),
        "question": data['question'],
        "options": data['options'],  # List of 4 options
        "correct_answer": data['correct_answer'],  # Index of correct option (0-3)
        "image_url": data.get('image_url', '')
    }
    
    result = await db.quizzes.update_one(
        {"id": data['quiz_id'], "teacher_id": current_user['id']},
        {"$push": {"questions": question}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {"message": "Question ajoutée", "question_id": question['id']}


@router.get("/teacher/my-quizzes")
async def get_teacher_quizzes(current_user: dict = Depends(get_current_user)):
    """Get all quizzes created by teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    quizzes = await db.quizzes.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    return quizzes


@router.delete("/teacher/delete-quiz/{quiz_id}")
async def delete_quiz(quiz_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a quiz"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.quizzes.delete_one({"id": quiz_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {"message": "Quiz supprimé"}

# ============== MEMORY GAME ENDPOINTS ==============


@router.post("/teacher/create-memory-game")
async def create_memory_game(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new memory matching game"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    memory_game = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "pairs": [],  # Will contain {id, word1, word2} or {id, image_url, word}
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.memory_games.insert_one(memory_game)
    return {"message": "Jeu Memory créé", "game_id": memory_game['id']}


@router.post("/teacher/add-memory-pair")
async def add_memory_pair(data: dict, current_user: dict = Depends(get_current_user)):
    """Add a pair to a memory game"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    pair = {
        "id": str(uuid4()),
        "card1": data['card1'],  # French word or image URL
        "card2": data['card2'],  # English translation
        "type": data.get('type', 'text')  # 'text' or 'image'
    }
    
    result = await db.memory_games.update_one(
        {"id": data['game_id'], "teacher_id": current_user['id']},
        {"$push": {"pairs": pair}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Memory game not found")
    
    return {"message": "Paire ajoutée", "pair_id": pair['id']}


@router.get("/teacher/my-memory-games")
async def get_teacher_memory_games(current_user: dict = Depends(get_current_user)):
    """Get all memory games created by teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    games = await db.memory_games.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    return games


@router.delete("/teacher/delete-memory-game/{game_id}")
async def delete_memory_game(game_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a memory game"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.memory_games.delete_one({"id": game_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Memory game not found")
    
    return {"message": "Jeu Memory supprimé"}


@router.get("/teacher/game-scores")
async def get_teacher_game_scores(current_user: dict = Depends(get_current_user)):
    """Get all game scores for teacher's students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    scores = await db.game_assignments.find(
        {"teacher_id": current_user['id'], "completed": True}, 
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with student names
    for score in scores:
        student = await db.users.find_one({"id": score['student_id']}, {"_id": 0, "first_name": 1, "last_name": 1})
        if student:
            score['student_name'] = f"{student['first_name']} {student['last_name']}"
    
    return scores


@router.post("/teacher/assign-video")
async def assign_video(data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher assigns video to a student (K-Kid)"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    video = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "student_id": data['student_id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "video_url": data['video_url'],
        "assigned_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.student_videos.insert_one(video)
    return {"message": "Video assigned"}


@router.get("/teacher/my-assigned-videos")
async def get_teacher_assigned_videos(current_user: dict = Depends(get_current_user)):
    """Get all videos assigned by teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    videos = await db.student_videos.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    
    # Enrich with student names
    for video in videos:
        student = await db.users.find_one({"id": video['student_id']}, {"_id": 0, "first_name": 1, "last_name": 1})
        if student:
            video['student_name'] = f"{student['first_name']} {student['last_name']}"
    
    return videos


@router.delete("/teacher/delete-video/{video_id}")
async def delete_video(video_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an assigned video"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.student_videos.delete_one({"id": video_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video deleted"}


