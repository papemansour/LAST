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

@router.get("/uploads/{file_path:path}")
async def serve_uploaded_file_api(file_path: str):
    """Serve uploaded files - tries MongoDB first, then local storage as fallback"""
    from fastapi.responses import Response
    import mimetypes
    import base64
    
    # Extract potential file_id from path (for new MongoDB files)
    # New format: /api/files/{file_id}
    # Old format: /uploads/documents/{uuid}.ext
    
    potential_file_id = file_path.split('/')[-1].split('.')[0] if '.' in file_path.split('/')[-1] else file_path.split('/')[-1]
    
    # Try MongoDB first
    file_data = await db.file_storage.find_one({"id": potential_file_id}, {"_id": 0})
    
    if file_data:
        try:
            content = base64.b64decode(file_data['data'])
            return Response(
                content=content,
                media_type=file_data.get('mime_type', 'application/octet-stream'),
                headers={
                    "Content-Disposition": f'inline; filename="{file_data["filename"]}"',
                    "X-Content-Type-Options": "nosniff",
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except Exception as e:
            logger.error(f"Error decoding MongoDB file: {e}")
    
    # Fallback to local file system (for old files)
    file_full_path = Path("/app/uploads") / file_path
    
    # Security check: ensure file is within uploads directory
    try:
        file_full_path.resolve().relative_to(Path("/app/uploads").resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Check if file exists
    if not file_full_path.exists() or not file_full_path.is_file():
        logger.warning(f"File not found (neither in MongoDB nor local): {file_full_path}")
        raise HTTPException(status_code=404, detail="Fichier non trouvé. Il a peut-être été supprimé lors d'un déploiement.")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(file_full_path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    logger.info(f"Serving local file via API: {file_path} ({mime_type})")
    
    # Read file content
    with open(file_full_path, "rb") as f:
        content = f.read()
    
    # Return response with download headers
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{file_full_path.name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get("/pricing")
async def get_pricing():
    """Get current pricing - Public endpoint"""
    pricing = await db.pricing.find_one({"id": "pricing"}, {"_id": 0})
    if not pricing:
        # Default pricing structure matching frontend expectations
        return {
            "kkid_eur": 30,
            "kkid_discount": 0,
            "beginner_eur": 76,
            "beginner_discount": 0,
            "intermediate_eur": 90,
            "intermediate_discount": 0,
            "advanced_eur": 102,
            "advanced_discount": 0
        }
    return pricing


@router.get("/kkid/videos")
async def get_kkid_videos(current_user: dict = Depends(get_current_user)):
    """Get K-Kid videos for current user"""
    if current_user.get('level') != 'kkid' and current_user['role'] not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Access restricted to K-Kids, teachers, and admins")
    
    # K-Kids only see their own videos
    if current_user.get('level') == 'kkid':
        videos = await db.kkid_videos.find(
            {"student_id": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(1000)
    # Teachers and admins see all videos they sent/manage
    else:
        if current_user['role'] == 'teacher':
            videos = await db.kkid_videos.find(
                {"teacher_id": current_user['id']},
                {"_id": 0}
            ).sort("created_at", -1).to_list(1000)
        else:  # admin
            videos = await db.kkid_videos.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return videos


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document (for students and teachers)"""
    # Check if document belongs to current user (either as sender or recipient)
    document = await db.documents.find_one({"id": document_id}, {"_id": 0})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check authorization (compatible with both old and new document formats)
    is_authorized = False
    
    # Check if user is recipient (support both formats)
    if document.get('to_user_id') == current_user['id'] or document.get('recipient_id') == current_user['id']:
        is_authorized = True
    
    # Check if user is sender (support both formats)
    if document.get('from_user_id') == current_user['id'] or document.get('teacher_id') == current_user['id']:
        is_authorized = True
    
    # Admin can delete any document
    if current_user['role'] == 'admin':
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    result = await db.documents.delete_one({"id": document_id})
    logger.info(f"Document {document_id} deleted by user {current_user['id']}")
    return {"message": "Document supprimé avec succès"}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    document = await db.documents.find_one({"id": document_id}, {"_id": 0})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has permission to delete
    if document['from_user_id'] != current_user['id'] and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    await db.documents.delete_one({"id": document_id})
    logger.info(f"Document {document_id} deleted by {current_user['id']}")
    return {"message": "Document deleted successfully"}

# Notification routes


@router.post("/contact/send")
async def send_contact_email(contact_data: dict):
    """
    Handle contact form submissions from homepage
    Sends email to mykalamaenglish@gmail.com
    """
    name = contact_data.get('name', '')
    email = contact_data.get('email', '')
    message = contact_data.get('message', '')
    
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    # Validate email format
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Send email to admin
    admin_email = "mykalamaenglish@gmail.com"
    subject = f"Nouveau message de contact - {name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); 
                      color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .message-box {{ background: white; padding: 20px; border-left: 4px solid #14b8a6; 
                           margin: 20px 0; border-radius: 5px; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📧 Nouveau Message de Contact</h1>
            </div>
            <div class="content">
                <p><strong>Vous avez reçu un nouveau message depuis le formulaire de contact du site web.</strong></p>
                
                <div class="message-box">
                    <p><strong>De :</strong> {name}</p>
                    <p><strong>Email :</strong> {email}</p>
                    <p><strong>Date :</strong> {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}</p>
                </div>
                
                <div class="message-box">
                    <h3>Message :</h3>
                    <p>{message}</p>
                </div>
                
                <p><strong>Pour répondre :</strong> Envoyez votre réponse directement à <a href="mailto:{email}">{email}</a></p>
                
                <p>Cordialement,<br>
                <strong>Système My KALAMA ENGLISH</strong></p>
            </div>
            <div class="footer">
                <p>My KALAMA ENGLISH - Système de notification automatique</p>
                <p>© 2025 MyKalamaenglish. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    NOUVEAU MESSAGE DE CONTACT - My KALAMA ENGLISH
    
    De: {name}
    Email: {email}
    Date: {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}
    
    MESSAGE:
    {message}
    
    Pour répondre, envoyez votre réponse directement à {email}
    """
    
    try:
        from email_service import email_service
        success = await email_service._send_email(admin_email, subject, html_body, text_body)
        
        if success:
            logger.info(f"Contact form email sent from {email}")
            return {"message": "Message sent successfully"}
        else:
            logger.warning(f"Contact form email logged (not sent) from {email}")
            return {"message": "Message received and will be processed"}
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending message")

# Admin annuaire (directory)


@router.get("/tests/{level}")
async def get_test(level: str):
    # Get questions from database
    db_questions = await db.test_questions.find({"level": level, "active": True}, {"_id": 0}).to_list(100)
    
    # If no questions in DB, fallback to hardcoded questions
    if not db_questions:
        if level not in TEST_QUESTIONS:
            raise HTTPException(status_code=404, detail="Test not found")
        questions = [{"id": q["id"], "question": q["question"], "options": q["options"]} 
                     for q in TEST_QUESTIONS[level]]
    else:
        # Return questions without correct answers
        questions = [{"id": q["id"], "question": q["question"], "options": q.get("options", [])} 
                     for q in db_questions]
    
    return {"level": level, "questions": questions}



@router.post("/tests/check-answer")
async def check_single_answer(data: dict = Body(...)):
    """Check a single answer and return if it's correct with the correct answer"""
    level = data.get("level")
    question_id = data.get("question_id")
    selected_option = data.get("selected_option")
    
    if not level or question_id is None or selected_option is None:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Get question from database first
    db_question = await db.test_questions.find_one(
        {"level": level, "id": question_id, "active": True}, 
        {"_id": 0}
    )
    
    if db_question:
        correct_answer = db_question.get("correct_answer")
        options = db_question.get("options", [])
        
        # Check if correct_answer is stored as text or index
        if isinstance(correct_answer, str) and correct_answer in options:
            # Stored as text, find the index
            correct_answer_index = options.index(correct_answer)
            correct_option = correct_answer
        else:
            # Stored as index
            try:
                correct_answer_index = int(correct_answer) if correct_answer is not None else 0
            except (ValueError, TypeError):
                correct_answer_index = 0
            correct_option = options[correct_answer_index] if correct_answer_index < len(options) else ""
        
        is_correct = int(correct_answer_index) == int(selected_option)
    else:
        # Fallback to hardcoded questions
        if level not in TEST_QUESTIONS:
            raise HTTPException(status_code=404, detail="Question not found")
        question = next((q for q in TEST_QUESTIONS[level] if q["id"] == question_id), None)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        correct_answer_index = question.get("correct")
        options = question.get("options", [])
        correct_option = options[correct_answer_index] if correct_answer_index is not None and correct_answer_index < len(options) else ""
        is_correct = int(correct_answer_index) == int(selected_option)
    
    return {
        "is_correct": is_correct,
        "correct_answer_index": correct_answer_index,
        "correct_option": correct_option
    }



@router.post("/tests/submit")
async def submit_test(submission: TestSubmission):
    # Get questions from database first
    db_questions = await db.test_questions.find({"level": submission.level, "active": True}, {"_id": 0}).to_list(100)
    
    # If no questions in DB, fallback to hardcoded questions
    if not db_questions:
        if submission.level not in TEST_QUESTIONS:
            raise HTTPException(status_code=404, detail="Test not found")
        correct_answers = TEST_QUESTIONS[submission.level]
        
        # Calculate score with hardcoded questions
        score = 0
        for answer in submission.answers:
            correct = next((q for q in correct_answers if q["id"] == answer["question_id"]), None)
            if correct and correct["correct"] == answer["selected_option"]:
                score += 1
    else:
        # Calculate score with database questions
        score = 0
        for answer in submission.answers:
            correct = next((q for q in db_questions if q["id"] == answer["question_id"]), None)
            if correct and str(correct.get("correct_answer")) == str(answer["selected_option"]):
                score += 1
    
    # Save result
    result = TestResult(
        user_id=None,
        level=submission.level,
        score=score,
        total_questions=len(submission.answers),
        answers=submission.answers
    )
    
    doc = result.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.test_results.insert_one(doc)
    
    return {
        "score": score,
        "total": len(submission.answers),
        "percentage": round((score / len(submission.answers)) * 100, 2),
        "level": submission.level
    }


@router.get("/tests/results/my")
async def get_my_test_results(current_user: dict = Depends(get_current_user)):
    results = await db.test_results.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return results


@router.get("/tests/results/all")
async def get_all_test_results(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = await db.test_results.find({}, {"_id": 0}).to_list(1000)
    
    # Enrichir avec les noms des candidats
    enriched_results = []
    for result in results:
        user = await db.users.find_one(
            {"id": result.get('user_id')},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        
        result_with_user = {**result}
        if user:
            result_with_user['candidate_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            result_with_user['candidate_email'] = user.get('email', '')
        else:
            result_with_user['candidate_name'] = 'Candidat anonyme'
            result_with_user['candidate_email'] = ''
        
        enriched_results.append(result_with_user)
    
    return enriched_results

# TEACHER ROUTES


@router.post("/upload")
async def upload_file_general(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a file (document, video, image, etc.) - stored in MongoDB for persistence"""
    import base64
    
    # File size limit: 15MB (MongoDB document limit)
    MAX_FILE_SIZE = 15 * 1024 * 1024
    contents = await file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 15MB)")
    
    # Generate unique file ID
    file_id = str(uuid4())
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'file'
    
    # Determine MIME type
    mime_types = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 
        'gif': 'image/gif', 'webp': 'image/webp', 'pdf': 'application/pdf',
        'doc': 'application/msword', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'mp4': 'video/mp4', 'mp3': 'audio/mpeg', 'wav': 'audio/wav'
    }
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    # Store file in MongoDB
    try:
        file_data = {
            "id": file_id,
            "filename": file.filename,
            "extension": file_ext,
            "mime_type": mime_type,
            "size": len(contents),
            "data": base64.b64encode(contents).decode('utf-8'),
            "uploaded_by": current_user['id'],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.file_storage.insert_one(file_data)
        
        file_url = f"/api/files/{file_id}"
        logger.info(f"File uploaded to MongoDB by {current_user['role']} {current_user['id']}: {file.filename}")
        
        return {
            "message": "File uploaded successfully",
            "file_url": file_url,
            "filename": file.filename,
            "file_id": file_id
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload du fichier")


@router.get("/group-courses")
async def get_all_group_courses(current_user: dict = Depends(get_current_user)):
    """Get all group courses - accessible by admin, secretary, teachers"""
    if current_user['role'] not in ['admin', 'secretary', 'teacher']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    courses = await db.group_courses.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrichir avec les noms des étudiants
    for course in courses:
        student_names = []
        for sid in course.get('student_ids', []):
            student = await db.users.find_one({"id": sid}, {"_id": 0, "first_name": 1, "last_name": 1})
            if student:
                student_names.append(f"{student['first_name']} {student['last_name']}")
        course['student_names'] = student_names
        course['enrolled_count'] = len(course.get('student_ids', []))
    
    return courses


@router.post("/group-courses")
async def create_group_course(course_data: GroupCourseCreate, current_user: dict = Depends(get_current_user)):
    """Create a new group course - admin/secretary only"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin/secrétaire")
    
    # Get teacher info
    teacher = await db.users.find_one({"id": course_data.teacher_id}, {"_id": 0, "first_name": 1, "last_name": 1})
    teacher_name = f"{teacher['first_name']} {teacher['last_name']}" if teacher else "Non assigné"
    
    group_course = {
        "id": str(uuid4()),
        "name": course_data.name,
        "description": course_data.description,
        "teacher_id": course_data.teacher_id,
        "teacher_name": teacher_name,
        "student_ids": [],
        "max_students": course_data.max_students,
        "price_per_person": course_data.price_per_person,
        "currency": course_data.currency,
        "level": course_data.level,
        "schedule": course_data.schedule,
        "meet_link": course_data.meet_link,
        "start_date": course_data.start_date,
        "end_date": course_data.end_date,
        "total_hours": course_data.total_hours,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.group_courses.insert_one(group_course)
    logger.info(f"Group course created: {course_data.name} by {current_user['id']}")
    
    return {"message": "Cours groupé créé avec succès", "group": group_course}


@router.put("/group-courses/{group_id}")
async def update_group_course(group_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    """Update a group course"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin/secrétaire")
    
    # Remove protected fields
    updates.pop('id', None)
    updates.pop('_id', None)
    updates.pop('created_at', None)
    
    result = await db.group_courses.update_one({"id": group_id}, {"$set": updates})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cours groupé non trouvé")
    
    return {"message": "Cours groupé mis à jour"}


@router.delete("/group-courses/{group_id}")
async def delete_group_course(group_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a group course"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin/secrétaire")
    
    result = await db.group_courses.delete_one({"id": group_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cours groupé non trouvé")
    
    # Also delete associated sessions
    await db.group_sessions.delete_many({"group_id": group_id})
    
    return {"message": "Cours groupé supprimé"}


@router.post("/group-courses/{group_id}/add-student")
async def add_student_to_group(group_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Add a student to a group course"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin/secrétaire")
    
    student_id = data.get('student_id')
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id requis")
    
    # Check if group exists and has space
    group = await db.group_courses.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Cours groupé non trouvé")
    
    if len(group.get('student_ids', [])) >= group.get('max_students', 10):
        raise HTTPException(status_code=400, detail="Le groupe est complet")
    
    if student_id in group.get('student_ids', []):
        raise HTTPException(status_code=400, detail="L'étudiant est déjà dans ce groupe")
    
    # Add student
    await db.group_courses.update_one(
        {"id": group_id},
        {"$push": {"student_ids": student_id}}
    )
    
    # Get student info for notification
    student = await db.users.find_one({"id": student_id}, {"_id": 0, "first_name": 1, "email": 1})
    
    # Create notification for student
    await create_notification(
        user_id=student_id,
        notification_type="group_course",
        data={
            "message": f"Vous avez été ajouté au cours groupé: {group['name']}",
            "group_id": group_id,
            "schedule": group.get('schedule', ''),
            "meet_link": group.get('meet_link', '')
        }
    )
    
    logger.info(f"Student {student_id} added to group {group_id}")
    return {"message": f"Étudiant ajouté au groupe avec succès", "student_name": student.get('first_name', '') if student else ''}


@router.post("/group-courses/{group_id}/remove-student")
async def remove_student_from_group(group_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Remove a student from a group course"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès réservé à l'admin/secrétaire")
    
    student_id = data.get('student_id')
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id requis")
    
    result = await db.group_courses.update_one(
        {"id": group_id},
        {"$pull": {"student_ids": student_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cours groupé non trouvé")
    
    return {"message": "Étudiant retiré du groupe"}


@router.get("/group-courses/{group_id}/sessions")
async def get_group_sessions(group_id: str, current_user: dict = Depends(get_current_user)):
    """Get all sessions for a group course"""
    sessions = await db.group_sessions.find({"group_id": group_id}, {"_id": 0}).sort("scheduled_date", 1).to_list(100)
    return sessions


@router.post("/group-courses/{group_id}/sessions")
async def create_group_session(group_id: str, session_data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new session for a group course"""
    if current_user['role'] not in ['admin', 'secretary', 'teacher']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Verify group exists
    group = await db.group_courses.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Cours groupé non trouvé")
    
    session = {
        "id": str(uuid4()),
        "group_id": group_id,
        "title": session_data.get('title', f"Session {group['name']}"),
        "scheduled_date": session_data.get('scheduled_date'),
        "duration_minutes": session_data.get('duration_minutes', 90),
        "meet_link": session_data.get('meet_link', group.get('meet_link', '')),
        "status": "scheduled",
        "attendees": [],
        "notes": session_data.get('notes', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.group_sessions.insert_one(session)
    
    # Notify all students in the group
    for student_id in group.get('student_ids', []):
        await create_notification(
            user_id=student_id,
            notification_type="group_session",
            data={
                "message": f"Nouvelle session programmée: {session['title']}",
                "session_id": session['id'],
                "scheduled_date": session['scheduled_date'],
                "meet_link": session['meet_link']
            }
        )
    
    return {"message": "Session créée", "session": session}


@router.put("/group-sessions/{session_id}/attendance")
async def update_session_attendance(session_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Mark attendance for a group session"""
    if current_user['role'] not in ['admin', 'secretary', 'teacher']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    attendees = data.get('attendees', [])
    status = data.get('status', 'completed')
    notes = data.get('notes', '')
    
    result = await db.group_sessions.update_one(
        {"id": session_id},
        {"$set": {"attendees": attendees, "status": status, "notes": notes}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    return {"message": "Présences enregistrées"}


@router.post("/messages/upload-attachment")
async def upload_message_attachment(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a file attachment for messages"""
    from pathlib import Path
    
    # File size limit: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    contents = await file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Create upload directory (persistent storage)
    upload_dir = Path("/app/uploads/messages")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'file'
    unique_filename = f"{str(uuid4())}.{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        file_url = f"/uploads/messages/{unique_filename}"
        
        # Determine file type
        file_type = "other"
        if file_ext.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
            file_type = "image"
        elif file_ext.lower() in ['pdf']:
            file_type = "pdf"
        elif file_ext.lower() in ['doc', 'docx']:
            file_type = "document"
        elif file_ext.lower() in ['xls', 'xlsx']:
            file_type = "spreadsheet"
        elif file_ext.lower() in ['mp4', 'avi', 'mov', 'webm']:
            file_type = "video"
        elif file_ext.lower() in ['mp3', 'wav', 'ogg']:
            file_type = "audio"
        
        logger.info(f"Message attachment uploaded by {current_user['id']}: {file.filename}")
        
        return {
            "file_url": file_url,
            "filename": file.filename,
            "file_type": file_type
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")


@router.post("/messages/send")
async def send_message(message_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    # Get sender info
    sender = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    message = Message(
        from_user_id=current_user['id'],
        to_user_id=message_data.to_user_id,
        content=message_data.content,
        attachment=message_data.attachment
    )
    
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('attachment'):
        doc['attachment'] = dict(doc['attachment'])
    await db.messages.insert_one(doc)
    
    # Create notification for recipient
    attachment_text = " avec une pièce jointe" if message_data.attachment else ""
    await create_notification(
        user_id=message_data.to_user_id,
        title=f"💬 Nouveau message",
        message=f"{sender['first_name']} {sender['last_name']} vous a envoyé un message{attachment_text}",
        notification_type="message"
    )
    
    return {"message": "Message sent", "attachment_sent": message_data.attachment is not None}


@router.get("/messages/conversation/{user_id}")
async def get_conversation(user_id: str, current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find(
        {
            "$or": [
                {"from_user_id": current_user['id'], "to_user_id": user_id},
                {"from_user_id": user_id, "to_user_id": current_user['id']}
            ]
        },
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    return messages


@router.delete("/messages/{message_id}/attachment")
async def delete_message_attachment(message_id: str, current_user: dict = Depends(get_current_user)):
    """Delete attachment from a message (only by sender)"""
    message = await db.messages.find_one({"id": message_id, "from_user_id": current_user['id']}, {"_id": 0})
    
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé ou non autorisé")
    
    if not message.get('attachment'):
        raise HTTPException(status_code=404, detail="Aucune pièce jointe à supprimer")
    
    # Remove attachment
    await db.messages.update_one(
        {"id": message_id},
        {"$unset": {"attachment": ""}}
    )
    
    logger.info(f"Attachment removed from message {message_id} by {current_user['id']}")
    return {"message": "Pièce jointe supprimée"}

# LIBRARY ROUTES


@router.get("/library/books")
async def get_library_books():
    books = await db.library_books.find({}, {"_id": 0}).to_list(1000)
    return books


@router.post("/library/books")
async def add_library_book(book_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = {
        "id": str(uuid.uuid4()),
        "title": book_data.get("title"),
        "author": book_data.get("author"),
        "description": book_data.get("description"),
        "level": book_data.get("level"),
        "type": book_data.get("type", "pdf"),  # pdf, audio
        "file_url": book_data.get("file_url"),
        "audio_url": book_data.get("audio_url"),
        "pages": book_data.get("pages", 0),
        "duration": book_data.get("duration", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.library_books.insert_one(book)
    return {"message": "Book added successfully", "book": book}


@router.delete("/library/books/{book_id}")
async def delete_library_book(book_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.library_books.delete_one({"id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": "Book deleted successfully"}


@router.get("/messages/my-conversations")
async def get_my_conversations(current_user: dict = Depends(get_current_user)):
    # Get all messages involving current user
    messages = await db.messages.find(
        {
            "$or": [
                {"from_user_id": current_user['id']},
                {"to_user_id": current_user['id']}
            ]
        },
        {"_id": 0}
    ).to_list(1000)
    
    # Get unique user IDs
    user_ids = set()
    for msg in messages:
        if msg['from_user_id'] != current_user['id']:
            user_ids.add(msg['from_user_id'])
        if msg['to_user_id'] != current_user['id']:
            user_ids.add(msg['to_user_id'])
    
    # Get user details
    users = []
    for uid in user_ids:
        user = await db.users.find_one({"id": uid}, {"_id": 0, "password_hash": 0})
        if user:
            users.append(user)
    
    return users

# ==================== DOCUMENTS ENDPOINTS ====================

# Collection pour stocker les fichiers en Base64 dans MongoDB (persistant)
# Cela résout le problème des fichiers perdus après déploiement


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a document file - stored in MongoDB for persistence"""
    import base64
    
    # File size limit: 15MB (MongoDB document limit)
    MAX_FILE_SIZE = 15 * 1024 * 1024
    contents = await file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 15MB)")
    
    # Generate unique file ID
    file_id = str(uuid4())
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'file'
    
    # Determine file type and MIME type
    mime_types = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 
        'gif': 'image/gif', 'webp': 'image/webp', 'svg': 'image/svg+xml',
        'pdf': 'application/pdf',
        'doc': 'application/msword', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel', 'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint', 'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'mp4': 'video/mp4', 'avi': 'video/x-msvideo', 'mov': 'video/quicktime', 'webm': 'video/webm',
        'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg',
        'txt': 'text/plain', 'csv': 'text/csv', 'json': 'application/json'
    }
    
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    file_type = "other"
    if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
        file_type = "image"
    elif file_ext == 'pdf':
        file_type = "pdf"
    elif file_ext in ['doc', 'docx']:
        file_type = "document"
    elif file_ext in ['xls', 'xlsx']:
        file_type = "spreadsheet"
    elif file_ext in ['ppt', 'pptx']:
        file_type = "presentation"
    elif file_ext in ['mp4', 'avi', 'mov', 'webm']:
        file_type = "video"
    elif file_ext in ['mp3', 'wav', 'ogg']:
        file_type = "audio"
    
    # Store file in MongoDB as Base64
    try:
        file_data = {
            "id": file_id,
            "filename": file.filename,
            "extension": file_ext,
            "mime_type": mime_type,
            "file_type": file_type,
            "size": len(contents),
            "data": base64.b64encode(contents).decode('utf-8'),
            "uploaded_by": current_user['id'],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.file_storage.insert_one(file_data)
        
        # URL points to our MongoDB file endpoint
        file_url = f"/api/files/{file_id}"
        
        logger.info(f"Document uploaded to MongoDB by {current_user['id']}: {file.filename} ({len(contents)} bytes)")
        
        return {
            "file_url": file_url,
            "file_name": file.filename,
            "file_type": file_type,
            "file_id": file_id
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload du fichier")


@router.get("/files/{file_id}")
async def get_file_from_mongodb(file_id: str):
    """Retrieve a file from MongoDB storage"""
    import base64
    from fastapi.responses import Response
    
    # Find file in MongoDB
    file_data = await db.file_storage.find_one({"id": file_id}, {"_id": 0})
    
    if not file_data:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    try:
        # Decode Base64 content
        content = base64.b64decode(file_data['data'])
        
        return Response(
            content=content,
            media_type=file_data.get('mime_type', 'application/octet-stream'),
            headers={
                "Content-Disposition": f'inline; filename="{file_data["filename"]}"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du fichier")


@router.post("/documents/send")
async def send_document(document_data: DocumentCreate, current_user: dict = Depends(get_current_user)):
    """Send a document to students"""
    # Verify sender is admin or teacher
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Only admins and teachers can send documents")
    
    sender = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    document = Document(
        title=document_data.title,
        description=document_data.description,
        file_url=document_data.file_url,
        file_name=document_data.file_name,
        file_type=document_data.file_type,
        sender_id=current_user['id'],
        sender_name=f"{sender['first_name']} {sender['last_name']}" if current_user['role'] == 'teacher' else "Admin KALAMA",
        sender_role=current_user['role'],
        recipient_ids=document_data.recipient_ids,
        read_by=[]
    )
    
    doc = document.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.documents.insert_one(doc)
    
    # Create notification for each recipient
    for recipient_id in document_data.recipient_ids:
        await create_notification(
            user_id=recipient_id,
            title=f"📄 Nouveau document",
            message=f"{document.sender_name} vous a envoyé un document: {document_data.title}",
            notification_type="document"
        )
    
    logger.info(f"Document sent by {current_user['id']} to {len(document_data.recipient_ids)} student(s)")
    
    return {"message": "Document sent successfully", "recipients_count": len(document_data.recipient_ids)}


@router.get("/documents/my-documents")
async def get_my_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents for current user (students receive, admin/teachers see sent)"""
    if current_user['role'] == 'student':
        # Students see documents sent to them
        documents = await db.documents.find(
            {"recipient_ids": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        # Add 'is_read' flag for each document
        for doc in documents:
            doc['is_read'] = current_user['id'] in doc.get('read_by', [])
        
        return documents
    else:
        # Admin and teachers see documents they sent
        documents = await db.documents.find(
            {"sender_id": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return documents


@router.put("/documents/{document_id}/mark-read")
async def mark_document_as_read(document_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a document as read by current student"""
    # Add current user to read_by list if not already there
    result = await db.documents.update_one(
        {"id": document_id, "recipient_ids": current_user['id']},
        {"$addToSet": {"read_by": current_user['id']}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found or already marked as read")
    
    return {"message": "Document marked as read"}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document (only sender can delete)"""
    # Find document
    document = await db.documents.find_one({"id": document_id}, {"_id": 0})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify sender
    if document['sender_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="You can only delete your own documents")
    
    # Delete from database
    await db.documents.delete_one({"id": document_id})
    
    # Optionally delete file from disk
    try:
        from pathlib import Path
        file_path = Path(f"/app/frontend/public{document['file_url']}")
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning(f"Could not delete file: {str(e)}")
    
    logger.info(f"Document deleted by {current_user['id']}: {document_id}")
    
    return {"message": "Document deleted successfully"}

# ==================== PROGRESSION & MEET LINKS ENDPOINTS ====================


@router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    badges = await db.badges.find({}, {"_id": 0}).to_list(100)
    return badges


@router.get("/challenges/current")
async def get_current_challenges():
    """Get current week's challenges"""
    now = datetime.now(timezone.utc)
    challenges = await db.weekly_challenges.find(
        {
            "active": True,
            "week_start": {"$lte": now},
            "week_end": {"$gte": now}
        },
        {"_id": 0}
    ).to_list(100)
    return challenges


@router.get("/group-courses")
async def get_group_courses():
    """Get all available group courses"""
    courses = await db.group_courses.find(
        {"status": {"$in": ["open", "in_progress"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with teacher info and student count
    for course in courses:
        teacher = await db.users.find_one(
            {"id": course['teacher_id']},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if teacher:
            course['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
        course['enrolled_count'] = len(course.get('current_students', []))
        course['spots_left'] = course['max_students'] - course['enrolled_count']
        # Apply discount for 4+ students
        if course['enrolled_count'] >= 4:
            course['discount_applied'] = True
            course['final_price_eur'] = course['price_per_person_eur'] * (1 - course['discount_4_plus'] / 100)
            course['final_price_fcfa'] = course['price_per_person_fcfa'] * (1 - course['discount_4_plus'] / 100)
        else:
            course['discount_applied'] = False
            course['final_price_eur'] = course['price_per_person_eur']
            course['final_price_fcfa'] = course['price_per_person_fcfa']
    
    return courses


@router.post("/group-courses")
async def create_group_course(course_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new group course (admin or teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    course = GroupCourse(
        title=course_data['title'],
        description=course_data.get('description', ''),
        teacher_id=course_data.get('teacher_id', current_user['id']),
        level=course_data['level'],
        max_students=course_data.get('max_students', 6),
        scheduled_days=course_data.get('scheduled_days', []),
        scheduled_time=course_data.get('scheduled_time', ''),
        price_per_person_eur=course_data.get('price_per_person_eur', 80.0),
        price_per_person_fcfa=course_data.get('price_per_person_fcfa', 50000.0),
        discount_4_plus=course_data.get('discount_4_plus', 10),
        meet_link=course_data.get('meet_link', ''),
        start_date=course_data.get('start_date')
    )
    
    doc = course.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.group_courses.insert_one(doc)
    
    logger.info(f"Group course created: {course.title} by {current_user['id']}")
    return {"message": "Cours groupé créé", "course_id": course.id}


@router.post("/group-courses/{course_id}/enroll")
async def enroll_in_group_course(course_id: str, current_user: dict = Depends(get_current_user)):
    """Enroll in a group course"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    course = await db.group_courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    if course['status'] == 'full':
        raise HTTPException(status_code=400, detail="Ce cours est complet")
    
    if current_user['id'] in course.get('current_students', []):
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit à ce cours")
    
    # Add student to course
    current_students = course.get('current_students', [])
    current_students.append(current_user['id'])
    
    # Update status if full
    new_status = 'full' if len(current_students) >= course['max_students'] else 'open'
    
    await db.group_courses.update_one(
        {"id": course_id},
        {"$set": {"current_students": current_students, "status": new_status}}
    )
    
    # Create enrollment record
    enrollment = GroupCourseEnrollment(
        group_course_id=course_id,
        student_id=current_user['id']
    )
    enrollment_doc = enrollment.model_dump()
    enrollment_doc['enrolled_at'] = enrollment_doc['enrolled_at'].isoformat()
    await db.group_course_enrollments.insert_one(enrollment_doc)
    
    # Notify student
    await create_notification(
        user_id=current_user['id'],
        title="✅ Inscription au cours groupé",
        message=f"Vous êtes inscrit au cours: {course['title']}",
        notification_type="group_course"
    )
    
    # 🎁 Coffre aux Trésors: +2 points pour inscription cours groupé
    await add_student_points(
        student_id=current_user['id'],
        points=2,
        reason=f"Inscription cours groupé: {course['title']}"
    )
    
    logger.info(f"Student {current_user['id']} enrolled in group course {course_id}")
    return {"message": "Inscription réussie", "enrollment_id": enrollment.id}


@router.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    """Generic file upload endpoint"""
    try:
        # Create uploads directory if not exists (persistent storage)
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_url = f"/uploads/{unique_filename}"
        logger.info(f"File uploaded: {file.filename} -> {file_url}")
        
        return {
            "message": "File uploaded successfully",
            "file_url": file_url,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")

# ============ KALAMATHÈQUE ROUTES ============


@router.post("/kalamatheque/verify-access")
async def verify_kalamatheque_access(data: dict):
    """Verify access code for Kalamathèque"""
    access_code = data.get('access_code')
    correct_code = os.environ.get('KALAMATHEQUE_ACCESS_CODE', 'Digika')
    
    if access_code == correct_code:
        return {"access": True, "message": "Accès accordé"}
    else:
        raise HTTPException(status_code=403, detail="Code d'accès incorrect")


@router.post("/kalamatheque/books")
async def create_book(book_data: dict, current_user: dict = Depends(get_current_user)):
    """Admin: Add a new book to Kalamathèque"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = {
        "id": str(uuid.uuid4()),
        "title": book_data['title'],
        "author": book_data.get('author', ''),
        "description": book_data.get('description', ''),
        "level": book_data['level'],  # beginner, intermediate, advanced
        "file_url": book_data['file_url'],
        "file_type": book_data['file_type'],  # pdf, epub, txt, html, docx
        "cover_image": book_data.get('cover_image', ''),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.kalamatheque_books.insert_one(book)
    logger.info(f"Book added to Kalamathèque: {book['title']} by admin {current_user['id']}")
    
    # Create notifications for all users (everyone can access Kalamathèque)
    all_users = await db.users.find(
        {"role": {"$in": ["teacher", "student"]}, "status": "approved"},
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in all_users:
        await create_notification(
            user_id=user["id"],
            title="📚 Nouveau livre dans la Kalamathèque !",
            message=f"Découvrez le nouveau livre : {book['title']}",
            notification_type="book"
        )
    
    return {"message": "Livre ajouté avec succès", "book_id": book['id']}


@router.get("/kalamatheque/books")
async def get_books(level: Optional[str] = None):
    """Get all books, optionally filtered by level"""
    query = {}
    if level:
        query['level'] = level
    
    books = await db.kalamatheque_books.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return books


@router.get("/kalamatheque/books/{book_id}")
async def get_book(book_id: str):
    """Get a specific book by ID"""
    book = await db.kalamatheque_books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return book


@router.delete("/kalamatheque/books/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Admin: Delete a book from Kalamathèque"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.kalamatheque_books.delete_one({"id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    logger.info(f"Book {book_id} deleted from Kalamathèque by admin {current_user['id']}")
    return {"message": "Livre supprimé avec succès"}


@router.post("/kalamatheque/ai-assistant")
async def kalamatheque_ai_assistant(data: dict):
    """AI Assistant for Kalamathèque - summarize, explain, or give examples (public access)"""
    action = data.get('action')  # 'summarize', 'explain', 'examples'
    selected_text = data.get('text')
    
    if not selected_text:
        raise HTTPException(status_code=400, detail="Texte requis")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        prompts = {
            'summarize': f"Résumez ce texte en français de manière concise :\n\n{selected_text}",
            'explain': f"Expliquez ce texte en français de manière claire et pédagogique :\n\n{selected_text}",
            'examples': f"Donnez 3 exemples concrets en français pour illustrer ce texte :\n\n{selected_text}"
        }
        
        prompt = prompts.get(action, prompts['explain'])
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id="kalamatheque_public",
            system_message="Vous êtes un assistant pédagogique qui aide les étudiants à comprendre les textes."
        )
        
        user_message = UserMessage(text=prompt)
        result = await chat.send_message(user_message)
        
        logger.info(f"AI Assistant used - action: {action}")
        return {"result": result}
        
    except Exception as e:
        logger.error(f"AI Assistant error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur de l'assistant IA")


@router.post("/kalamatheque/text-to-speech")
async def text_to_speech(data: dict):
    """Generate speech from text using OpenAI TTS (public access)"""
    text = data.get('text')
    
    if not text:
        raise HTTPException(status_code=400, detail="Texte requis")
    
    try:
        from emergentintegrations.llm.openai.text_to_speech import OpenAITextToSpeech
        
        tts = OpenAITextToSpeech(api_key=os.environ.get('EMERGENT_LLM_KEY'))
        
        # Generate speech and get base64 encoded audio
        audio_base64 = await tts.generate_speech_base64(
            text=text,
            model="tts-1",
            voice="alloy",
            response_format="mp3"
        )
        
        logger.info(f"TTS used for Kalamathèque")
        return {"audio_base64": audio_base64}
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur de synthèse vocale")

# ============ NEWS ROUTES ============


@router.get("/welcome-letter")
async def get_welcome_letter(current_user: dict = Depends(get_current_user)):
    """Get welcome letter for current user"""
    letter = await db.welcome_letters.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    if not letter:
        return None
    
    return letter


@router.put("/welcome-letter/mark-read")
async def mark_welcome_letter_read(current_user: dict = Depends(get_current_user)):
    """Mark welcome letter as read"""
    result = await db.welcome_letters.update_one(
        {"user_id": current_user['id']},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lettre non trouvée")
    
    return {"message": "Lettre marquée comme lue"}

# ============ KALAMA CLUB ROUTES ============


@router.post("/promo-codes/validate")
async def validate_promo_code(request: ValidatePromoCodeRequest):
    """Validate a promo code and return discount information"""
    code_upper = request.code.upper()
    
    # Find promo code
    promo = await db.promo_codes.find_one({"code": code_upper}, {"_id": 0})
    
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo invalide")
    
    # Check if active
    if not promo.get('is_active', False):
        raise HTTPException(status_code=400, detail="Ce code promo n'est plus actif")
    
    # Check expiration
    valid_until_str = promo.get('valid_until')
    if valid_until_str:
        # Parse the datetime string
        if isinstance(valid_until_str, str):
            valid_until = datetime.fromisoformat(valid_until_str.replace('Z', '+00:00'))
        else:
            valid_until = valid_until_str
        
        if datetime.now(timezone.utc) > valid_until:
            raise HTTPException(status_code=400, detail="Ce code promo a expiré")
    
    # Check max uses
    max_uses = promo.get('max_uses')
    current_uses = promo.get('current_uses', 0)
    
    if max_uses and current_uses >= max_uses:
        raise HTTPException(status_code=400, detail="Ce code promo a atteint sa limite d'utilisation")
    
    return {
        "valid": True,
        "code": promo['code'],
        "discount_percent": promo['discount_percent'],
        "message": f"Code promo valide ! {promo['discount_percent']}% de réduction"
    }


@router.post("/promo-codes/use")
async def use_promo_code(request: ValidatePromoCodeRequest, user_email: str):
    """Mark a promo code as used"""
    code_upper = request.code.upper()
    
    # Validate first
    promo = await db.promo_codes.find_one({"code": code_upper}, {"_id": 0})
    
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo invalide")
    
    # Check if user already used this code
    usage = await db.promo_code_usage.find_one({
        "promo_code": code_upper,
        "user_email": user_email
    })
    
    if usage:
        raise HTTPException(status_code=400, detail="Vous avez déjà utilisé ce code promo")
    
    # Increment usage count
    await db.promo_codes.update_one(
        {"code": code_upper},
        {"$inc": {"current_uses": 1}}
    )
    
    # Record usage
    usage_doc = {
        "id": str(uuid4()),
        "promo_code_id": promo['id'],
        "promo_code": code_upper,
        "user_email": user_email,
        "used_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promo_code_usage.insert_one(usage_doc)
    
    return {"message": "Code promo appliqué avec succès"}


@router.post("/payments/create-checkout")
async def create_checkout_session(payment: PaymentRequest):
    """Create a Stripe checkout session (returns hardcoded links for now)"""
    
    plan_name = payment.plan_name
    plan_level = payment.plan_level
    amount = payment.amount
    currency = payment.currency
    promo_code = payment.promo_code
    
    # Mapping des liens Stripe directs par pack (mis à jour avec les vrais liens)
    stripe_links = {
        'kkid': 'https://buy.stripe.com/9B64gz8rFaJD7RB4q0',
        'beginner_without_club': 'https://buy.stripe.com/fZufZheQ304Z5Jtg8IenS00',
        'beginner_with_club': 'https://buy.stripe.com/fZufZheQ304Z5Jtg8IenS00',
        'intermediate_without_club': 'https://buy.stripe.com/dRmdR96jx5pjdbVf4EenS01',
        'intermediate_with_club': 'https://buy.stripe.com/dRmdR96jx5pjdbVf4EenS01',
        'advanced_without_club': 'https://buy.stripe.com/00w14nazNg3XefZ2hSenS02',
        'advanced_with_club': 'https://buy.stripe.com/00w14nazNg3XefZ2hSenS02'
    }
    
    # Déterminer la clé du lien
    if plan_level == 'kkid':
        link_key = 'kkid'
    else:
        # Détecter si c'est avec ou sans club basé sur le nom du pack
        has_club = 'Club' in plan_name or 'club' in plan_name.lower()
        link_key = f"{plan_level}_{'with' if has_club else 'without'}_club"
    
    checkout_url = stripe_links.get(link_key)
    
    if not checkout_url:
        logger.error(f"No Stripe link found for key: {link_key}")
        raise HTTPException(
            status_code=400, 
            detail=f"Lien de paiement non trouvé pour le pack {plan_name}"
        )
    
    # Ajouter le code promo à l'URL si fourni
    # Code promo par défaut de l'utilisateur
    default_promo = "promo_1SYGM3I4faCc3GWYbdYRPXX8"
    promo_to_apply = promo_code if promo_code else default_promo
    
    if promo_to_apply:
        # Ajouter le code promo comme paramètre URL
        separator = '&' if '?' in checkout_url else '?'
        checkout_url = f"{checkout_url}{separator}prefilled_promo_code={promo_to_apply}"
    
    logger.info(f"Payment link generated: {link_key} -> {checkout_url}")
    
    return {
        "checkout_url": checkout_url,
        "plan_name": plan_name,
        "amount": amount,
        "currency": currency,
        "promo_applied": promo_to_apply
    }


