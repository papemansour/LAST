"""Auto-generated route module."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import Response, StreamingResponse
from config import db, logger, get_current_user, hash_password, verify_password, create_access_token, FRONTEND_URL, SECRET_KEY, ALGORITHM, security, pwd_context
from models.schemas import (
    User, TeacherCreate, StudentCreateByAdmin, WelcomeLetter, BadgeCreate, Badge, StudentBadge
)
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

@router.post("/admin/cleanup-invalid-documents")
async def cleanup_invalid_documents(current_user: dict = Depends(get_current_user)):
    """Remove documents whose files no longer exist on disk"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check all documents
    docs = await db.documents.find({}, {"_id": 0, "id": 1, "file_url": 1, "title": 1}).to_list(1000)
    
    removed = []
    for doc in docs:
        file_url = doc.get('file_url', '')
        if file_url:
            file_path = Path("/app/uploads") / file_url.replace('/uploads/', '')
            if not file_path.exists():
                await db.documents.delete_one({"id": doc['id']})
                removed.append({"id": doc['id'], "title": doc.get('title', 'Unknown')})
                logger.info(f"Removed invalid document: {doc.get('title')} - {file_url}")
    
    return {
        "message": f"Nettoyage terminé: {len(removed)} document(s) supprimé(s)",
        "removed_documents": removed
    }


@router.get("/admin/check-documents-integrity")
async def check_documents_integrity(current_user: dict = Depends(get_current_user)):
    """Check which documents have missing files"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    docs = await db.documents.find({}, {"_id": 0, "id": 1, "file_url": 1, "title": 1}).to_list(1000)
    
    valid = []
    invalid = []
    
    for doc in docs:
        file_url = doc.get('file_url', '')
        if file_url:
            file_path = Path("/app/uploads") / file_url.replace('/uploads/', '')
            if file_path.exists():
                valid.append({"id": doc['id'], "title": doc.get('title', 'Unknown')})
            else:
                invalid.append({"id": doc['id'], "title": doc.get('title', 'Unknown'), "file_url": file_url})
    
    return {
        "total_documents": len(docs),
        "valid_documents": len(valid),
        "invalid_documents": len(invalid),
        "invalid_list": invalid
    }


@router.get("/admin/pending-registrations")
async def get_pending_registrations(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    registrations = await db.users.find(
        {"role": "student", "is_active": False},
        {"_id": 0}
    ).to_list(1000)
    
    return registrations

# Email sending is now handled by email_service.py


@router.post("/admin/change-student-teacher")
async def change_student_teacher(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Change the assigned teacher for a student"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student_id = data.get('student_id')
    new_teacher_id = data.get('new_teacher_id')
    
    if not student_id:
        raise HTTPException(status_code=400, detail="Student ID required")
    
    # Update student's assigned teacher
    update_data = {"assigned_teacher": new_teacher_id} if new_teacher_id else {"assigned_teacher": None}
    
    result = await db.users.update_one(
        {"id": student_id, "role": "student"},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # If new teacher assigned, update teacher's students list
    if new_teacher_id:
        await db.users.update_one(
            {"id": new_teacher_id, "role": "teacher"},
            {"$addToSet": {"students": student_id}}
        )
    
    logger.info(f"Admin {current_user['id']} changed teacher for student {student_id} to {new_teacher_id}")
    
    return {"message": "Teacher changed successfully"}


@router.post("/admin/approve-registration/{user_id}")
async def approve_registration(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate temporary password
    temp_password = f"Kalama{user_id[:6]}"
    password_hash = hash_password(temp_password)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": True, "password_hash": password_hash, "temporary_password": temp_password}}
    )
    
    # Générer le mot de passe Digika pour la bibliothèque
    digika_password = f"DIGIKA{user_id[:4].upper()}"
    
    # Sauvegarder le Digika dans la base
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"digika_password": digika_password}}
    )
    
    # Envoyer les infos à Monday.com CRM avec mot de passe et Digika
    try:
        from monday_integration import create_monday_item, generate_welcome_email_html
        
        # Créer l'item dans Monday.com avec le mot de passe et Digika
        monday_item_id = create_monday_item({
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'level': user.get('level', 'beginner'),
            'temporary_password': temp_password,
            'digika_password': digika_password,
        })
        
        if monday_item_id:
            logger.info(f"Student {user_id} added to Monday.com with credentials: {monday_item_id}")
            
            # Sauvegarder l'ID Monday.com dans la base
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"monday_item_id": monday_item_id}}
            )
            
            # Générer le contenu HTML de l'email de bienvenue
            welcome_email_html = generate_welcome_email_html({
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'email': user.get('email', ''),
                'level': user.get('level', 'beginner'),
                'temporary_password': temp_password,
                'digika_password': digika_password,
            })
            
            # Sauvegarder l'email HTML pour envoi via Monday automation
            await db.pending_welcome_emails.insert_one({
                "id": str(uuid4()),
                "user_id": user_id,
                "email": user.get('email', ''),
                "html_content": welcome_email_html,
                "subject": f"Hello and Welcome to MyKalama - {user.get('first_name', '')}!",
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
    except Exception as e:
        logger.error(f"Monday.com integration error: {e}")
    
    # Send level-based welcome email
    await email_service.send_level_based_welcome_email(
        user['email'],
        user['first_name'],
        user.get('level', 'beginner'),
        temp_password,
        user.get('last_name', '')
    )
    
    # Create welcome letter in database
    letter_content = generate_welcome_letter_content(
        user['first_name'],
        user.get('level', 'beginner'),
        'student',
        user['email'],
        temp_password
    )
    
    welcome_letter = WelcomeLetter(
        user_id=user_id,
        user_email=user['email'],
        user_name=f"{user['first_name']} {user['last_name']}",
        user_level=user.get('level', 'beginner'),
        user_role='student',
        temp_password=temp_password,
        content=letter_content
    )
    
    letter_doc = welcome_letter.model_dump()
    letter_doc['created_at'] = letter_doc['created_at'].isoformat()
    await db.welcome_letters.insert_one(letter_doc)
    
    logger.info(f"User {user_id} approved, email and welcome letter created (Level: {user.get('level', 'beginner')}). Monday.com integration attempted.")
    
    return {
        "message": "User approved, welcome email and letter created",
        "email": user['email'],
        "temporary_password": temp_password,
        "level": user.get('level', 'beginner')
    }


@router.post("/admin/create-teacher")
async def create_teacher(teacher_data: TeacherCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Create teacher email
    email = f"{teacher_data.first_name.lower()}.{teacher_data.last_name.lower()}@mykalamaenglish.com"
    
    # Check if exists
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Teacher email already exists")
    
    # Generate password
    temp_password = f"Teacher{uuid.uuid4().hex[:8]}"
    password_hash = hash_password(temp_password)
    
    teacher = User(
        email=email,
        first_name=teacher_data.first_name,
        last_name=teacher_data.last_name,
        phone="",
        role="teacher",
        is_active=True,
        password_hash=password_hash,
        temporary_password=temp_password
    )
    
    doc = teacher.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Create welcome letter for teacher
    letter_content = generate_welcome_letter_content(
        teacher_data.first_name,
        'teacher',  # level parameter, but not used for teachers
        'teacher',
        email,
        temp_password
    )
    
    welcome_letter = WelcomeLetter(
        user_id=teacher.id,
        user_email=email,
        user_name=f"{teacher_data.first_name} {teacher_data.last_name}",
        user_level='teacher',
        user_role='teacher',
        temp_password=temp_password,
        content=letter_content
    )
    
    letter_doc = welcome_letter.model_dump()
    letter_doc['created_at'] = letter_doc['created_at'].isoformat()
    await db.welcome_letters.insert_one(letter_doc)
    
    logger.info(f"Teacher {teacher.id} created with welcome letter")
    
    return {
        "message": "Teacher created with welcome letter",
        "email": email,
        "temporary_password": temp_password
    }


@router.post("/admin/create-student")
async def create_student_by_admin(student_data: StudentCreateByAdmin, current_user: dict = Depends(get_current_user)):
    """Créer un étudiant directement par l'admin sans inscription"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Vérifier si l'email existe déjà
    existing = await db.users.find_one({"email": student_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    # Générer un mot de passe si non fourni
    temp_password = student_data.password if student_data.password else f"Kalama{uuid.uuid4().hex[:6]}"
    password_hash = hash_password(temp_password)
    
    # Générer le code Digika
    digika_code = f"DIGIKA{uuid.uuid4().hex[:4].upper()}"
    
    # Mapper le niveau
    level_map = {
        'beginner': 'beginner',
        'intermediate': 'intermediate', 
        'advanced': 'advanced',
        'kkid': 'kkid',
        'K-Débutant': 'beginner',
        'K-Intermédiaire': 'intermediate',
        'K-Professionnel': 'advanced',
        'K-Kids': 'kkid'
    }
    level = level_map.get(student_data.level, 'beginner')
    
    # Créer l'étudiant
    student = User(
        email=student_data.email,
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        phone=f"{student_data.phone_country_code}{student_data.phone}",
        role="student",
        level=level,
        is_active=True,
        password_hash=password_hash,
        temporary_password=temp_password
    )
    
    doc = student.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['digika_password'] = digika_code
    doc['price'] = student_data.price
    doc['currency'] = student_data.currency
    doc['phone_country_code'] = student_data.phone_country_code
    doc['created_by_admin'] = True
    
    await db.users.insert_one(doc)
    
    # Créer la lettre de bienvenue
    level_names = {
        'beginner': 'Débutant',
        'intermediate': 'Intermédiaire',
        'advanced': 'Professionnel',
        'kkid': 'K-Kid'
    }
    
    letter_content = generate_welcome_letter_content(
        student_data.first_name,
        level_names.get(level, 'Débutant'),
        'student',
        student_data.email,
        temp_password
    )
    
    welcome_letter = WelcomeLetter(
        user_id=student.id,
        user_email=student_data.email,
        user_name=f"{student_data.first_name} {student_data.last_name}",
        user_level=level,
        user_role='student',
        temp_password=temp_password,
        content=letter_content
    )
    
    letter_doc = welcome_letter.model_dump()
    letter_doc['created_at'] = letter_doc['created_at'].isoformat()
    await db.welcome_letters.insert_one(letter_doc)
    
    logger.info(f"Student {student.id} created by admin {current_user['id']}")
    
    return {
        "message": "Étudiant créé avec succès",
        "student": {
            "id": student.id,
            "email": student_data.email,
            "first_name": student_data.first_name,
            "last_name": student_data.last_name,
            "phone": f"{student_data.phone_country_code}{student_data.phone}",
            "level": level,
            "price": student_data.price,
            "currency": student_data.currency
        },
        "temporary_password": temp_password,
        "digika_code": digika_code
    }


@router.post("/admin/import-students-csv")
async def import_students_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Importer des étudiants en masse depuis un fichier CSV"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")
    
    content = await file.read()
    try:
        # Essayer d'abord UTF-8, sinon latin-1
        try:
            decoded = content.decode('utf-8')
        except UnicodeDecodeError:
            decoded = content.decode('latin-1')
        
        csv_reader = csv.DictReader(io.StringIO(decoded), delimiter=';')
        
        results = {
            "imported": [],
            "errors": [],
            "skipped": []
        }
        
        # Mapper les niveaux
        level_map = {
            'beginner': 'beginner', 'debutant': 'beginner', 'débutant': 'beginner',
            'intermediate': 'intermediate', 'intermédiaire': 'intermediate', 'intermediaire': 'intermediate',
            'advanced': 'advanced', 'professionnel': 'advanced', 'avancé': 'advanced', 'avance': 'advanced',
            'kkid': 'kkid', 'k-kid': 'kkid', 'kid': 'kkid', 'enfant': 'kkid',
            'k-débutant': 'beginner', 'k-intermédiaire': 'intermediate', 'k-professionnel': 'advanced', 'k-kids': 'kkid'
        }
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Nettoyer les clés (trim whitespace)
                row = {k.strip().lower(): v.strip() if v else '' for k, v in row.items() if k}
                
                # Extraire les champs (avec plusieurs noms possibles)
                email = row.get('email', row.get('e-mail', row.get('mail', ''))).strip()
                first_name = row.get('prenom', row.get('prénom', row.get('first_name', row.get('firstname', '')))).strip()
                last_name = row.get('nom', row.get('last_name', row.get('lastname', row.get('name', '')))).strip()
                phone = row.get('telephone', row.get('téléphone', row.get('phone', row.get('tel', '')))).strip()
                level_raw = row.get('niveau', row.get('level', 'beginner')).strip().lower()
                price_str = row.get('prix', row.get('price', row.get('tarif', '0'))).strip()
                currency = row.get('devise', row.get('currency', 'EUR')).strip().upper()
                
                # Validation basique
                if not email:
                    results["errors"].append({"row": row_num, "reason": "Email manquant"})
                    continue
                    
                if not first_name:
                    results["errors"].append({"row": row_num, "email": email, "reason": "Prénom manquant"})
                    continue
                
                # Vérifier si l'email existe déjà
                existing = await db.users.find_one({"email": email}, {"_id": 0})
                if existing:
                    results["skipped"].append({"row": row_num, "email": email, "reason": "Email déjà existant"})
                    continue
                
                # Mapper le niveau
                level = level_map.get(level_raw, 'beginner')
                
                # Parser le prix
                try:
                    price = float(price_str.replace(',', '.').replace(' ', '')) if price_str else 0
                except (ValueError, TypeError):
                    price = 0
                
                # Normaliser la devise
                if currency in ['FCFA', 'XOF', 'CFA']:
                    currency = 'FCFA'
                else:
                    currency = 'EUR'
                
                # Générer mot de passe et code
                temp_password = f"Kalama{uuid.uuid4().hex[:6]}"
                password_hash = hash_password(temp_password)
                digika_code = f"DIGIKA{uuid.uuid4().hex[:4].upper()}"
                
                # Créer l'étudiant
                student = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name or first_name,
                    phone=phone or "",
                    role="student",
                    level=level,
                    is_active=True,
                    password_hash=password_hash,
                    temporary_password=temp_password
                )
                
                doc = student.model_dump()
                doc['created_at'] = doc['created_at'].isoformat()
                doc['digika_password'] = digika_code
                doc['price'] = price
                doc['currency'] = currency
                doc['created_by_admin'] = True
                doc['imported_from_csv'] = True
                
                await db.users.insert_one(doc)
                
                results["imported"].append({
                    "row": row_num,
                    "email": email,
                    "name": f"{first_name} {last_name}",
                    "level": level,
                    "password": temp_password,
                    "digika_code": digika_code
                })
                
            except Exception as e:
                results["errors"].append({"row": row_num, "reason": str(e)})
        
        logger.info(f"CSV Import by admin {current_user['id']}: {len(results['imported'])} imported, {len(results['skipped'])} skipped, {len(results['errors'])} errors")
        
        return {
            "message": f"{len(results['imported'])} étudiant(s) importé(s) avec succès",
            "summary": {
                "total_imported": len(results["imported"]),
                "total_skipped": len(results["skipped"]),
                "total_errors": len(results["errors"])
            },
            "details": results
        }
        
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        raise HTTPException(status_code=400, detail=f"Erreur lors du parsing du CSV: {str(e)}")


@router.get("/admin/csv-template")
async def get_csv_template(current_user: dict = Depends(get_current_user)):
    """Télécharger un modèle CSV pour l'import d'étudiants"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    csv_content = """prenom;nom;email;telephone;niveau;prix;devise
Jean;Dupont;jean.dupont@gmail.com;+33612345678;beginner;76;EUR
Marie;Martin;marie.martin@gmail.com;+221771234567;intermediate;60000;FCFA
"""
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=modele_import_etudiants.csv"}
    )


@router.get("/admin/all-users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users


@router.post("/admin/assign-teacher/{student_id}/{teacher_id}")
async def assign_teacher(student_id: str, teacher_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.users.update_one(
        {"id": student_id},
        {"$set": {"assigned_teacher": teacher_id}}
    )
    
    return {"message": "Teacher assigned successfully"}


@router.delete("/admin/delete-student/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(get_current_user)):
    """Admin soft-deletes a student - moves to trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = await db.users.find_one({"id": student_id, "role": "student"}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Add deletion metadata
    student['deleted_at'] = datetime.now(timezone.utc).isoformat()
    student['deleted_by'] = current_user['id']
    
    # Move to trash collection
    await db.deleted_users.insert_one(student)
    
    # Delete from main collection
    await db.users.delete_one({"id": student_id})
    
    # NOTE: We keep related data for potential restoration
    
    logger.info(f"Student soft-deleted: {student['email']}")
    return {"message": "Student moved to trash successfully"}


@router.post("/admin/restrict-student/{student_id}")
async def restrict_student(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = await db.users.find_one({"id": student_id, "role": "student"}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Toggle restriction status
    new_status = not student.get('is_restricted', False)
    await db.users.update_one(
        {"id": student_id},
        {"$set": {"is_restricted": new_status}}
    )
    
    action = "restricted" if new_status else "unrestricted"
    logger.info(f"Student {action}: {student['email']}")
    
    return {
        "message": f"Student access {'restricted' if new_status else 'restored'} successfully",
        "is_restricted": new_status
    }


@router.post("/admin/restrict-user/{user_id}")
async def restrict_user_generic(user_id: str, current_user: dict = Depends(get_current_user)):
    """Generic endpoint to restrict/unrestrict any user (student or teacher)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot restrict admin")
    
    # Toggle restriction status
    new_status = not user.get('is_restricted', False)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_restricted": new_status}}
    )
    
    action = "restricted" if new_status else "unrestricted"
    logger.info(f"{user['role'].title()} {action}: {user['email']}")
    
    return {
        "message": f"Access {'restricted' if new_status else 'restored'} successfully",
        "is_restricted": new_status
    }


@router.get("/admin/session-notifications")
async def get_session_notifications(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    notifications = await db.admin_notifications.find(
        {"type": "session_completed"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)


@router.post("/admin/update-prices")
async def update_prices(prices: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Store prices in database with discount support
    prices_doc = {
        "id": "pricing",
        **prices,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user['id']
    }
    
    await db.pricing.replace_one({"id": "pricing"}, prices_doc, upsert=True)
    logger.info(f"Prices updated by admin {current_user['id']}")
    return {"message": "Prices updated successfully"}


@router.post("/admin/send-document")
async def admin_send_document(doc_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    document = {
        "id": str(uuid.uuid4()),
        "from_user_id": current_user['id'],
        "from_user_role": "admin",
        "to_user_id": doc_data['recipient_id'],
        "to_user_role": doc_data['recipient_type'],
        "title": doc_data['title'],
        "description": doc_data.get('description', ''),
        "file_url": doc_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(document)
    
    # Create notification
    await create_notification(
        user_id=doc_data['recipient_id'],
        notification_type="new_document",
        data={"message": f"Nouveau document de l'admin: {doc_data['title']}"}
    )
    
    logger.info(f"Document sent by admin to {doc_data['recipient_type']}: {doc_data['recipient_id']}")
    return {"message": "Document sent successfully"}


@router.get("/admin/documents-from-teachers")
async def get_admin_documents_from_teachers(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    documents = await db.documents.find(
        {"to_user_role": "admin", "from_user_role": "teacher"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with teacher info
    for doc in documents:
        teacher = await db.users.find_one(
            {"id": doc['from_user_id']},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        if teacher:
            doc['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
            doc['teacher_email'] = teacher['email']


@router.get("/admin/received-documents")
async def get_admin_received_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents sent to admin from teachers and students"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    documents = await db.documents.find(
        {"to_user_role": "admin"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with sender info
    for doc in documents:
        sender = await db.users.find_one(
            {"id": doc['from_user_id']},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "role": 1}
        )
        if sender:
            doc['sender_name'] = f"{sender['first_name']} {sender['last_name']}"
            doc['sender_email'] = sender['email']
            doc['sender_role'] = sender['role']
    
    return documents


@router.delete("/admin/delete-document/{document_id}")
async def delete_admin_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document received by admin"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.documents.delete_one({"id": document_id, "to_user_role": "admin"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    logger.info(f"Document {document_id} deleted by admin {current_user['id']}")
    return {"message": "Document supprimé avec succès"}


@router.delete("/admin/delete-user/{user_id}")
async def admin_delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Admin soft-deletes a user (student/teacher) - moves to trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get the user first
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot delete admin")
    
    # Add deletion metadata
    user['deleted_at'] = datetime.now(timezone.utc).isoformat()
    user['deleted_by'] = current_user['id']
    
    # Move to trash collection
    await db.deleted_users.insert_one(user)
    
    # Delete from main collection
    await db.users.delete_one({"id": user_id})
    
    # NOTE: We keep related data for potential restoration
    
    logger.info(f"User soft-deleted by admin: {user['email']}")
    return {"message": f"{user['role'].capitalize()} moved to trash successfully"}


@router.get("/admin/trash")
async def get_trash(current_user: dict = Depends(get_current_user)):
    """Get all deleted users (trash)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deleted_users = await db.deleted_users.find({}, {"_id": 0}).to_list(1000)
    return deleted_users


@router.post("/admin/restore-user/{user_id}")
async def restore_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Restore a deleted user from trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find user in trash
    user = await db.deleted_users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found in trash")
    
    # Remove deletion metadata
    user.pop('deleted_at', None)
    user.pop('deleted_by', None)
    
    # Restore to main collection
    await db.users.insert_one(user)
    
    # Remove from trash
    await db.deleted_users.delete_one({"id": user_id})
    
    logger.info(f"User restored by admin: {user['email']}")
    return {"message": f"{user['role'].capitalize()} restored successfully"}


@router.delete("/admin/permanent-delete/{user_id}")
async def permanent_delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Permanently delete a user from trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Delete from trash
    result = await db.deleted_users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found in trash")
    
    logger.info(f"User permanently deleted by admin: {user_id}")
    return {"message": "User permanently deleted"}


@router.delete("/admin/empty-trash")
async def empty_trash(current_user: dict = Depends(get_current_user)):
    """Empty the entire trash - permanently delete all users in trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count how many users will be deleted
    count = await db.deleted_users.count_documents({})
    
    if count == 0:
        return {"message": "La poubelle est déjà vide", "deleted_count": 0}
    
    # Delete all users in trash
    result = await db.deleted_users.delete_many({})
    
    logger.info(f"Trash emptied by admin: {result.deleted_count} users permanently deleted")
    return {"message": f"{result.deleted_count} utilisateur(s) supprimé(s) définitivement", "deleted_count": result.deleted_count}


@router.get("/admin/users")
async def get_users_by_role(role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all users, optionally filtered by role"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

# Endpoint en doublon supprimé - le changement de mot de passe se fait via la route ligne 339

# ADMIN: Reset user password (SECURE)


@router.post("/admin/reset-user-password/{user_id}")
async def admin_reset_user_password(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot reset admin password")
    
    # Generate a secure temporary password
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    temporary_password = ''.join(secrets.choice(alphabet) for i in range(10))
    
    # Hash the temporary password
    hashed = hash_password(temporary_password)
    
    # Update user with temporary password
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": hashed,
            "temporary_password": temporary_password,
            "password_reset_at": datetime.now(timezone.utc).isoformat(),
            "password_reset_by": current_user['id']
        }}
    )
    
    # Send email to user with the temporary password
    try:
        from email_service import send_password_reset_email
        await send_password_reset_email(
            to_email=user['email'],
            user_name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            temporary_password=temporary_password
        )
        email_sent = True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        email_sent = False
    
    # Create notification for user
    # (notification logic can be added here if needed)

# ADMIN: Generate Magic Code for Group Registration


@router.post("/admin/generate-magic-code/{user_id}")
async def admin_generate_magic_code(
    user_id: str,
    teacher_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Admin generates a magic code for a group registration and assigns to teacher"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find the group registration
    group_reg = await db.users.find_one({"id": user_id, "course_type": "group"}, {"_id": 0})
    if not group_reg:
        raise HTTPException(status_code=404, detail="Inscription de groupe non trouvée")
    
    if group_reg.get('magic_code_generated'):
        raise HTTPException(status_code=400, detail="Un code magique a déjà été généré pour ce groupe")
    
    # Verify teacher exists
    teacher = await db.users.find_one({"id": teacher_id, "role": "teacher"}, {"_id": 0})
    if not teacher:
        raise HTTPException(status_code=404, detail="Professeur non trouvé")
    
    # Generate unique magic code (8 characters)
    magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure code is unique
    while await db.users.find_one({"temporary_password": magic_code}, {"_id": 0}):
        magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Get the main member's name from the members array
    main_member = next((m for m in group_reg['members'] if m.get('is_main')), group_reg['members'][0])
    
    # Update the group registration
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_active": True,  # Activate the account
            "is_approved": True,  # Mark as approved
            "password_hash": pwd_context.hash(magic_code),  # Hash the magic code
            "temporary_password": magic_code,  # Store for display
            "assigned_teacher": teacher_id,
            "magic_code_generated": True,
            "magic_code_generated_at": datetime.now(timezone.utc).isoformat(),
            "magic_code_generated_by": current_user['id'],
            # Add the main member's name for login compatibility
            "first_name": main_member['first_name'],
            "last_name": main_member['last_name']
        }}
    )
    
    logger.info(f"Magic code {magic_code} generated for group {user_id} by admin {current_user['id']}")
    
    # Get member names for response
    members_names = ", ".join([f"{m['first_name']} {m['last_name']}" for m in group_reg['members']])
    
    return {
        "message": "Code magique généré avec succès",
        "magic_code": magic_code,
        "group_id": user_id,
        "email": group_reg['email'],
        "total_members": group_reg['total_members'],
        "members_names": members_names,
        "teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
        "teacher_email": teacher['email']
    }

# ADMIN: Get pending group registrations


@router.get("/admin/pending-group-registrations")
async def get_pending_group_registrations(current_user: dict = Depends(get_current_user)):
    """Get all pending group registrations waiting for magic code"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pending_groups = await db.users.find(
        {
            "course_type": "group",
            "is_approved": False,
            "magic_code_generated": False
        },
        {"_id": 0}
    ).to_list(1000)
    
    return pending_groups


@router.post("/admin/reset-password/{user_id}")
async def admin_reset_password(user_id: str, current_user: dict = Depends(get_current_user)):
    """Admin resets password for a user"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate temporary password
    import secrets
    temporary_password = f"Temp{secrets.token_hex(4)}"
    hashed_password = pwd_context.hash(temporary_password)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": hashed_password, "hashed_password": hashed_password}}
    )
    
    # Try to send email
    email_sent = False
    try:
        from email_service import email_service
        await email_service.send_password_reset_email(user['email'], temporary_password)
        email_sent = True
    except Exception as e:
        logger.warning(f"Could not send password reset email: {e}")
    
    logger.info(f"Password reset by admin {current_user['email']} for user {user['email']}")
    
    return {
        "message": "Password reset successfully",
        "temporary_password": temporary_password,
        "email_sent": email_sent,
        "note": "User will receive email with temporary password. They should change it after login."
    }

# News routes (admin only can create, everyone can read)


@router.post("/admin/create-news")
async def create_news(news_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    news_item = {
        "id": str(uuid.uuid4()),
        "title": news_data['title'],
        "content": news_data['content'],
        "type": news_data.get('type', 'article'),  # article, video, link, publication
        "url": news_data.get('url', ''),
        "image_url": news_data.get('image_url', ''),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.news.insert_one(news_item)
    
    # Notify all users
    all_users = await db.users.find({"role": {"$in": ["student", "teacher"]}}, {"_id": 0, "id": 1}).to_list(1000)
    for user in all_users:
        await create_notification(user['id'], 'new_news', {
            "title": news_data['title'],
            "message": f"Nouvelle actualité: {news_data['title']}"
        })
    
    logger.info(f"News created by admin: {news_data['title']}")
    return {"message": "News published successfully"}


@router.delete("/admin/delete-news/{news_id}")
async def delete_news(news_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.news.delete_one({"id": news_id})
    return {"message": "News deleted"}

# Contact form route (public)


@router.get("/admin/directory")
async def get_directory(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find(
        {"role": {"$in": ["teacher", "student"]}, "is_active": True},
        {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1, "phone": 1, "role": 1}
    ).to_list(1000)
    
    return users

# Teacher availability routes


@router.get("/admin/leave-requests")
async def get_all_leave_requests(current_user: dict = Depends(get_current_user)):
    """Admin gets all leave requests"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    leaves = await db.leave_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return leaves


@router.post("/admin/leave-request/{leave_id}/approve")
async def approve_leave_request(leave_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Admin approves a leave request"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    leave = await db.leave_requests.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    comment = data.get('comment', '')
    
    await db.leave_requests.update_one(
        {"id": leave_id},
        {"$set": {
            "status": "approved",
            "admin_comment": comment,
            "approved_by": current_user['id'],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify teacher
    notification = {
        "id": str(uuid4()),
        "user_id": leave['teacher_id'],
        "message": f"✅ Votre demande de congé ({leave['start_date']} → {leave['end_date']}) a été approuvée !",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    # Deduct leave days from balance
    try:
        from dateutil import parser as dt_parser
        start = dt_parser.parse(leave['start_date'])
        end = dt_parser.parse(leave['end_date'])
        days_taken = max(1, (end - start).days + 1)
        # Exclude weekends (approximate)
        working_days = 0
        current = start
        while current <= end:
            if current.weekday() < 5:  # Monday to Friday
                working_days += 1
            current += timedelta(days=1)
        if working_days == 0:
            working_days = days_taken
        
        await db.leave_balances.update_one(
            {"user_id": leave['teacher_id']},
            {"$inc": {"total_taken": working_days, "remaining": -working_days}},
            upsert=False
        )
        logger.info(f"Deducted {working_days} leave days from {leave['teacher_id']}")
    except Exception as e:
        logger.warning(f"Could not deduct leave days: {e}")
    
    logger.info(f"Leave request {leave_id} approved by admin")
    return {"message": "Leave request approved"}


@router.post("/admin/leave-request/{leave_id}/reject")
async def reject_leave_request(leave_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Admin rejects a leave request"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    leave = await db.leave_requests.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    comment = data.get('comment', '')
    
    await db.leave_requests.update_one(
        {"id": leave_id},
        {"$set": {
            "status": "rejected",
            "admin_comment": comment,
            "rejected_by": current_user['id'],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify teacher
    notification = {
        "id": str(uuid4()),
        "user_id": leave['teacher_id'],
        "message": f"❌ Votre demande de congé ({leave['start_date']} → {leave['end_date']}) a été refusée.{' Motif: ' + comment if comment else ''}",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    logger.info(f"Leave request {leave_id} rejected by admin")
    return {"message": "Leave request rejected"}


@router.post("/admin/leave-request/{leave_id}/unapprove")
async def unapprove_leave_request(leave_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Admin unapproves (cancels) a previously approved leave request - restores leave balance"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    leave = await db.leave_requests.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.get('status') != 'approved':
        raise HTTPException(status_code=400, detail="Only approved leave requests can be unapproved")
    
    comment = data.get('comment', '')
    
    # Calculate working days to restore
    try:
        from dateutil import parser as dt_parser
        start = dt_parser.parse(leave['start_date'])
        end = dt_parser.parse(leave['end_date'])
        working_days = 0
        current = start
        while current <= end:
            if current.weekday() < 5:  # Monday to Friday
                working_days += 1
            current += timedelta(days=1)
        if working_days == 0:
            working_days = max(1, (end - start).days + 1)
        
        # Restore leave balance
        await db.leave_balances.update_one(
            {"user_id": leave['teacher_id']},
            {"$inc": {"total_taken": -working_days, "remaining": working_days}},
            upsert=False
        )
        logger.info(f"Restored {working_days} leave days to {leave['teacher_id']}")
    except Exception as e:
        logger.warning(f"Could not restore leave days: {e}")
    
    # Update leave request status
    await db.leave_requests.update_one(
        {"id": leave_id},
        {"$set": {
            "status": "cancelled",
            "admin_comment": comment,
            "cancelled_by": current_user['id'],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify employee
    notification = {
        "id": str(uuid4()),
        "user_id": leave['teacher_id'],
        "message": f"⚠️ Votre congé approuvé ({leave['start_date']} → {leave['end_date']}) a été annulé.{' Motif: ' + comment if comment else ''}",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    logger.info(f"Leave request {leave_id} unapproved by admin")
    return {"message": "Leave request cancelled, balance restored"}


@router.get("/admin/availability-calendar")
async def get_availability_calendar(current_user: dict = Depends(get_current_user)):
    """Get calendar of all employees showing days they are NOT on leave"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Admin or secretary access required")
    
    # Get all employees
    employees = await db.users.find(
        {"role": {"$in": ["teacher", "admin", "secretary"]}, "is_active": True},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "role": 1, "email": 1, "phone": 1, "created_at": 1}
    ).to_list(200)
    
    # Get all approved leave requests
    leaves = await db.leave_requests.find(
        {"status": "approved"},
        {"_id": 0, "teacher_id": 1, "start_date": 1, "end_date": 1, "reason": 1}
    ).to_list(500)
    
    # Build leave periods per employee
    leave_by_employee = {}
    for leave in leaves:
        emp_id = leave.get('teacher_id')
        if emp_id not in leave_by_employee:
            leave_by_employee[emp_id] = []
        leave_by_employee[emp_id].append({
            "start": leave.get('start_date'),
            "end": leave.get('end_date'),
            "reason": leave.get('reason', 'Congé')
        })
    
    # Build result
    result = []
    for emp in employees:
        emp_leaves = leave_by_employee.get(emp['id'], [])
        result.append({
            "user_id": emp['id'],
            "first_name": emp.get('first_name', ''),
            "last_name": emp.get('last_name', ''),
            "role": emp.get('role', ''),
            "email": emp.get('email', ''),
            "phone": emp.get('phone', ''),
            "created_at": emp.get('created_at', ''),
            "leave_periods": emp_leaves
        })
    
    return result


@router.get("/admin/all-students")
async def get_all_students_detailed(current_user: dict = Depends(get_current_user)):
    """Get all students with their details including level/pack"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Admin or secretary access required")
    
    students = await db.users.find(
        {"role": "student", "is_active": True},
        {"_id": 0, "password_hash": 0, "temporary_password": 0}
    ).to_list(500)
    
    result = []
    for student in students:
        result.append({
            "user_id": student.get('id', ''),
            "first_name": student.get('first_name', ''),
            "last_name": student.get('last_name', ''),
            "email": student.get('email', ''),
            "phone": student.get('phone', ''),
            "level": student.get('level', student.get('pack', 'beginner')),
            "pack": student.get('pack', student.get('level', 'beginner')),
            "created_at": student.get('created_at', ''),
            "is_active": student.get('is_active', True)
        })
    
    return result


@router.get("/admin/export-students-excel")
async def export_students_excel(current_user: dict = Depends(get_current_user)):
    """Export all students to Excel file (prénom, nom, email, téléphone, niveau)"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Admin or secretary access required")
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    
    # Get all students
    students = await db.users.find(
        {"role": "student"},
        {"_id": 0}
    ).sort("last_name", 1).to_list(1000)
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Liste des Étudiants"
    
    # Define styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")  # Teal color
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Headers
    headers = ["Prénom", "Nom", "Email", "Téléphone", "Niveau", "Statut", "Date d'inscription"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Level mapping for display
    level_display = {
        "kkid": "K-Kid (Enfant)",
        "beginner": "Débutant",
        "intermediate": "Intermédiaire",
        "advanced": "Avancé/Professionnel"
    }
    
    # Data rows
    for row_num, student in enumerate(students, 2):
        level = student.get('level', student.get('pack', 'beginner'))
        level_text = level_display.get(level, level.capitalize() if level else "Non défini")
        
        status = "Actif" if student.get('is_active', True) else "Inactif"
        
        # Format date
        created_at = student.get('created_at', '')
        if created_at:
            try:
                if isinstance(created_at, str):
                    from dateutil import parser as dt_parser
                    created_date = dt_parser.parse(created_at)
                    created_at = created_date.strftime("%d/%m/%Y")
                else:
                    created_at = created_at.strftime("%d/%m/%Y")
            except Exception:
                pass
        
        row_data = [
            student.get('first_name', ''),
            student.get('last_name', ''),
            student.get('email', ''),
            student.get('phone', ''),
            level_text,
            status,
            created_at
        ]
        
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left", vertical="center")
    
    # Adjust column widths
    column_widths = [15, 15, 30, 18, 20, 10, 15]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = width
    
    # Save to buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Generate filename with date
    filename = f"etudiants_kalama_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    logger.info(f"Excel export generated by {current_user['email']}: {len(students)} students")
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/admin/all-teachers-detailed")
async def get_all_teachers_detailed(current_user: dict = Depends(get_current_user)):
    """Get all teachers with their details including seniority"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Admin or secretary access required")
    
    teachers = await db.users.find(
        {"role": "teacher", "is_active": True},
        {"_id": 0, "password_hash": 0, "temporary_password": 0}
    ).to_list(200)
    
    result = []
    for teacher in teachers:
        # Calculate seniority (months worked)
        created_at = teacher.get('created_at')
        months_worked = 0
        if created_at:
            try:
                from dateutil import parser as dt_parser
                if isinstance(created_at, str):
                    created_date = dt_parser.parse(created_at)
                else:
                    created_date = created_at
                now = datetime.now(timezone.utc)
                if created_date.tzinfo is None:
                    created_date = created_date.replace(tzinfo=timezone.utc)
                months_worked = max(0, (now.year - created_date.year) * 12 + (now.month - created_date.month))
            except Exception:
                pass
        
        result.append({
            "user_id": teacher.get('id', ''),
            "first_name": teacher.get('first_name', ''),
            "last_name": teacher.get('last_name', ''),
            "email": teacher.get('email', ''),
            "phone": teacher.get('phone', ''),
            "months_worked": months_worked,
            "created_at": teacher.get('created_at', ''),
            "is_active": teacher.get('is_active', True)
        })
    
    return result



# ============ GROUP CODE ENDPOINTS ============

def generate_unique_code():
    """Generate a unique 6-character alphanumeric code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@router.get("/admin/all-teacher-availability")
async def get_all_teacher_availability(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all teachers with their availability
    teachers = await db.users.find({"role": "teacher"}, {"_id": 0}).to_list(1000)
    
    result = []
    for teacher in teachers:
        availability = await db.teacher_availability.find_one(
            {"teacher_id": teacher['id']},
            {"_id": 0}
        )
        result.append({
            "teacher_id": teacher['id'],
            "teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
            "email": teacher['email'],
            "availability": availability.get('availability', {}) if availability else {}
        })
    
    return result


# Teacher features


# TEST ROUTES


@router.get("/admin/teacher-sessions")
async def get_teacher_sessions(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sessions = await db.teacher_sessions.find(
        {"status": "completed"},
        {"_id": 0}
    ).sort("end_time", -1).to_list(1000)
    
    # Enrich with teacher info
    for session in sessions:
        teacher = await db.users.find_one(
            {"id": session['teacher_id']},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        if teacher:
            session['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
            session['teacher_email'] = teacher['email']
    
    return sessions


@router.delete("/admin/teacher-sessions/{session_id}")
async def delete_teacher_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a specific teacher attendance session"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.teacher_sessions.delete_one({"id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    # Also delete the notification if exists
    await db.admin_notifications.delete_one({"session_id": session_id})
    
    logger.info(f"Session {session_id} deleted by admin {current_user['id']}")
    return {"message": "Session supprimée avec succès"}


@router.delete("/admin/teacher-sessions")
async def delete_all_teacher_sessions(current_user: dict = Depends(get_current_user)):
    """Delete all teacher attendance sessions"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.teacher_sessions.delete_many({})
    await db.admin_notifications.delete_many({"type": "session_completed"})
    
    logger.info(f"All {result.deleted_count} sessions deleted by admin {current_user['id']}")
    return {"message": f"{result.deleted_count} sessions supprimées"}


@router.get("/admin/monthly-teacher-hours")
async def get_monthly_teacher_hours(month: int = None, year: int = None, current_user: dict = Depends(get_current_user)):
    """Get monthly summary of hours worked by each teacher based on attendance"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Use current month if not specified
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year
    
    # Get start and end of month
    start_date = datetime(target_year, target_month, 1, tzinfo=timezone.utc)
    if target_month == 12:
        end_date = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(target_year, target_month + 1, 1, tzinfo=timezone.utc)
    
    # Get all completed sessions for this month
    sessions = await db.teacher_sessions.find({
        "status": "completed",
        "end_time": {
            "$gte": start_date.isoformat(),
            "$lt": end_date.isoformat()
        }
    }, {"_id": 0}).to_list(10000)
    
    # Group by teacher
    teacher_hours = {}
    for session in sessions:
        teacher_id = session['teacher_id']
        if teacher_id not in teacher_hours:
            # Get teacher info if not in session
            teacher_name = session.get('teacher_name')
            teacher_email = session.get('teacher_email')
            
            if not teacher_name or teacher_name == 'Inconnu':
                teacher = await db.users.find_one(
                    {"id": teacher_id},
                    {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
                )
                if teacher:
                    teacher_name = f"{teacher.get('first_name', '')} {teacher.get('last_name', '')}".strip()
                    teacher_email = teacher.get('email', '')
                else:
                    teacher_name = 'Inconnu'
                    teacher_email = ''
            
            teacher_hours[teacher_id] = {
                "teacher_id": teacher_id,
                "teacher_name": teacher_name,
                "teacher_email": teacher_email,
                "total_minutes": 0,
                "total_sessions": 0,
                "sessions": []
            }
        
        # Calculate duration from total_time_seconds (primary) or total_time (legacy) or from times
        duration_minutes = session.get('total_time_seconds', 0) / 60
        if duration_minutes == 0:
            duration_minutes = session.get('total_time', 0) / 60
        if duration_minutes == 0 and session.get('start_time') and session.get('end_time'):
            try:
                start = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(session['end_time'].replace('Z', '+00:00'))
                duration_minutes = (end - start).total_seconds() / 60
            except (ValueError, TypeError):
                pass
        
        teacher_hours[teacher_id]['total_minutes'] += duration_minutes
        teacher_hours[teacher_id]['total_sessions'] += 1
        teacher_hours[teacher_id]['sessions'].append({
            "date": session.get('end_time', session.get('created_at')),
            "duration_minutes": round(duration_minutes, 2)
        })
    
    # Convert to list and format
    result = []
    for data in teacher_hours.values():
        total_hours = data['total_minutes'] / 60
        result.append({
            "teacher_id": data['teacher_id'],
            "teacher_name": data['teacher_name'],
            "teacher_email": data['teacher_email'],
            "total_hours": round(total_hours, 2),
            "total_minutes": round(data['total_minutes'], 2),
            "total_sessions": data['total_sessions'],
            "sessions": data['sessions'][-10:]  # Last 10 sessions
        })
    
    # Sort by total hours descending
    result.sort(key=lambda x: x['total_hours'], reverse=True)
    
    return {
        "month": target_month,
        "year": target_year,
        "month_name": ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                       "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"][target_month],
        "teachers": result,
        "total_teachers": len(result),
        "total_hours_all": round(sum(t['total_hours'] for t in result), 2)
    }

# ==================== COURS GROUPÉS ENDPOINTS ====================


@router.get("/admin/analytics")
async def get_admin_analytics(period: str = "month", current_user: dict = Depends(get_current_user)):
    """Get comprehensive analytics for admin dashboard"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    
    # Calculate date ranges based on period
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # month
        start_date = now - timedelta(days=30)
    
    # Get student counts
    total_students = await db.users.count_documents({"role": "student"})
    active_students = await db.users.count_documents({"role": "student", "is_active": True})
    total_teachers = await db.users.count_documents({"role": "teacher"})
    
    # Get students by level
    levels = await db.users.aggregate([
        {"$match": {"role": "student"}},
        {"$group": {"_id": "$level", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    students_by_level = [
        {"name": l['_id'] or "Non défini", "value": l['count']} 
        for l in levels if l['_id']
    ]
    
    # Get monthly student growth (last 6 months)
    students_by_month = []
    month_names = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
    for i in range(5, -1, -1):
        target_date = now - timedelta(days=i*30)
        month_start = datetime(target_date.year, target_date.month, 1, tzinfo=timezone.utc)
        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1, tzinfo=timezone.utc)
        
        count = await db.users.count_documents({
            "role": "student",
            "created_at": {"$lt": month_end.isoformat()}
        })
        students_by_month.append({
            "month": month_names[target_date.month],
            "count": count
        })
    
    # Get hours by week (last 4 weeks)
    hours_by_week = []
    for i in range(3, -1, -1):
        week_start = now - timedelta(days=(i+1)*7)
        week_end = now - timedelta(days=i*7)
        
        sessions = await db.teacher_sessions.find({
            "status": "completed",
            "end_time": {"$gte": week_start.isoformat(), "$lt": week_end.isoformat()}
        }, {"_id": 0, "total_time_seconds": 1}).to_list(1000)
        
        total_hours = sum(s.get('total_time_seconds', 0) for s in sessions) / 3600
        hours_by_week.append({
            "week": f"Sem {4-i}",
            "hours": round(total_hours, 1)
        })
    
    # Get revenue by month (incoming from student_receipts, outgoing from teacher_payments)
    revenue_by_month = []
    for i in range(5, -1, -1):
        target_date = now - timedelta(days=i*30)
        month_start = datetime(target_date.year, target_date.month, 1, tzinfo=timezone.utc)
        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1, tzinfo=timezone.utc)
        
        # Incoming revenue: student receipts (EUR)
        incoming_eur = await db.student_receipts.find({
            "currency": "EUR",
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        }, {"_id": 0, "amount": 1}).to_list(1000)
        
        # Incoming revenue: student receipts (FCFA)
        incoming_fcfa = await db.student_receipts.find({
            "currency": "FCFA",
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        }, {"_id": 0, "amount": 1}).to_list(1000)
        
        # Outgoing expenses: teacher payments (EUR)
        outgoing_eur = await db.teacher_payments.find({
            "currency": "EUR",
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        }, {"_id": 0, "amount": 1}).to_list(1000)
        
        # Outgoing expenses: teacher payments (FCFA)
        outgoing_fcfa = await db.teacher_payments.find({
            "currency": "FCFA",
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        }, {"_id": 0, "amount": 1}).to_list(1000)
        
        # Helper to safely convert amount to float (handles string amounts from DB)
        def safe_amount(val):
            try:
                return float(val) if val else 0
            except (ValueError, TypeError):
                return 0
        
        revenue_by_month.append({
            "month": month_names[target_date.month],
            "incoming_eur": sum(safe_amount(p.get('amount', 0)) for p in incoming_eur),
            "incoming_fcfa": sum(safe_amount(p.get('amount', 0)) for p in incoming_fcfa),
            "outgoing_eur": sum(safe_amount(p.get('amount', 0)) for p in outgoing_eur),
            "outgoing_fcfa": sum(safe_amount(p.get('amount', 0)) for p in outgoing_fcfa)
        })
    
    # Get top teachers by hours this month
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    teacher_sessions = await db.teacher_sessions.find({
        "status": "completed",
        "end_time": {"$gte": month_start.isoformat()}
    }, {"_id": 0, "teacher_id": 1, "teacher_name": 1, "total_time_seconds": 1}).to_list(1000)
    
    teacher_hours = {}
    for s in teacher_sessions:
        tid = s.get('teacher_id')
        if tid:
            if tid not in teacher_hours:
                teacher_hours[tid] = {"name": s.get('teacher_name', 'Unknown'), "hours": 0, "students": 0}
            teacher_hours[tid]['hours'] += s.get('total_time_seconds', 0) / 3600
    
    # Count students per teacher
    for tid in teacher_hours:
        count = await db.users.count_documents({"assigned_teacher": tid, "role": "student"})
        teacher_hours[tid]['students'] = count
    
    top_teachers = sorted(
        [{"name": v['name'], "hours": round(v['hours'], 1), "students": v['students']} 
         for v in teacher_hours.values()],
        key=lambda x: x['hours'],
        reverse=True
    )[:5]
    
    # Calculate total hours this month
    total_hours_this_month = sum(t['hours'] for t in top_teachers)
    
    # Calculate growth rate
    prev_month_students = await db.users.count_documents({
        "role": "student",
        "created_at": {"$lt": month_start.isoformat()}
    })
    growth_rate = ((total_students - prev_month_students) / max(prev_month_students, 1)) * 100 if prev_month_students > 0 else 0
    
    # Total revenue (net = incoming - outgoing)
    total_incoming_eur = sum(r['incoming_eur'] for r in revenue_by_month[-1:])
    total_incoming_fcfa = sum(r['incoming_fcfa'] for r in revenue_by_month[-1:])
    total_outgoing_eur = sum(r['outgoing_eur'] for r in revenue_by_month[-1:])
    total_outgoing_fcfa = sum(r['outgoing_fcfa'] for r in revenue_by_month[-1:])
    
    return {
        "summary": {
            "total_students": total_students,
            "active_students": active_students,
            "total_teachers": total_teachers,
            "total_hours_this_month": round(total_hours_this_month, 1),
            "incoming_eur": total_incoming_eur,
            "incoming_fcfa": total_incoming_fcfa,
            "outgoing_eur": total_outgoing_eur,
            "outgoing_fcfa": total_outgoing_fcfa,
            "net_eur": total_incoming_eur - total_outgoing_eur,
            "net_fcfa": total_incoming_fcfa - total_outgoing_fcfa,
            "growth_rate": round(growth_rate, 1)
        },
        "students_by_month": students_by_month,
        "hours_by_week": hours_by_week,
        "hours_by_semester": await get_hours_by_semester(),
        "revenue_by_month": revenue_by_month,
        "students_by_level": students_by_level,
        "top_teachers": top_teachers
    }

async def get_hours_by_semester():
    """Calculate teaching hours grouped by quarter/semester"""
    now = datetime.now(timezone.utc)
    semesters = []
    
    # Define quarters for the last 5 quarters
    quarters = [
        {"start_month": 1, "end_month": 3, "label": "T1"},
        {"start_month": 4, "end_month": 6, "label": "T2"},
        {"start_month": 7, "end_month": 9, "label": "T3"},
        {"start_month": 10, "end_month": 12, "label": "T4"},
    ]
    
    # Calculate for current year and previous year
    for year in [now.year - 1, now.year]:
        for q in quarters:
            start = datetime(year, q["start_month"], 1, tzinfo=timezone.utc)
            if q["end_month"] == 12:
                end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(year, q["end_month"] + 1, 1, tzinfo=timezone.utc)
            
            # Skip future quarters
            if start > now:
                continue
            
            # Get all course links sent in this period (each link = 1 session)
            course_links = await db.course_links.count_documents({
                "created_at": {"$gte": start.isoformat(), "$lt": end.isoformat()}
            })
            
            # Get completed sessions in this period
            sessions = await db.teacher_sessions.find({
                "status": "completed",
                "end_time": {"$gte": start.isoformat(), "$lt": end.isoformat()}
            }, {"_id": 0, "total_time_seconds": 1}).to_list(1000)
            
            total_hours = sum(s.get('total_time_seconds', 0) for s in sessions) / 3600
            
            # If no session data, estimate from course links (assume 1h per link)
            if total_hours == 0 and course_links > 0:
                total_hours = course_links  # 1 hour per course link sent
            
            month_names = {1: "Jan", 4: "Avr", 7: "Juil", 10: "Oct"}
            end_month_names = {3: "Mar", 6: "Juin", 9: "Sept", 12: "Déc"}
            
            semesters.append({
                "semester": f"{month_names[q['start_month']]}-{end_month_names[q['end_month']]} {year}",
                "hours": round(total_hours, 1),
                "label": f"{q['label']} {year}"
            })
    
    # Return last 5 quarters
    return semesters[-5:] if len(semesters) > 5 else semesters


@router.post("/admin/update-revenue")
async def update_revenue(data: dict, current_user: dict = Depends(get_current_user)):
    """Update revenue data for a specific month (for corrections)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    month = data.get('month')
    if not month:
        raise HTTPException(status_code=400, detail="Month is required")
    
    # Store the correction in a dedicated collection
    correction = {
        "id": str(uuid.uuid4()),
        "month": month,
        "incoming_eur": data.get('incoming_eur', 0),
        "incoming_fcfa": data.get('incoming_fcfa', 0),
        "outgoing_eur": data.get('outgoing_eur', 0),
        "outgoing_fcfa": data.get('outgoing_fcfa', 0),
        "corrected_by": current_user['id'],
        "corrected_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert - update if exists, insert if not
    await db.revenue_corrections.update_one(
        {"month": month},
        {"$set": correction},
        upsert=True
    )
    
    logger.info(f"Revenue correction for {month} by admin {current_user['email']}")
    return {"message": f"Revenus de {month} mis à jour", "correction": correction}


@router.post("/admin/manual-session")
async def create_manual_session(session_data: dict, current_user: dict = Depends(get_current_user)):
    """Enregistrer manuellement les heures d'un professeur"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Créer une session manuelle complète
    manual_session = {
        "id": session_data.get('id', str(uuid4())),
        "teacher_id": session_data['teacher_id'],
        "teacher_name": session_data['teacher_name'],
        "teacher_email": session_data['teacher_email'],
        "start_time": session_data['start_time'],
        "end_time": session_data['end_time'],
        "total_time_seconds": session_data['total_time_seconds'],
        "paused_duration_seconds": session_data.get('paused_duration_seconds', 0),
        "status": "completed",
        "is_manual": True,
        "created_at": session_data.get('created_at', datetime.now(timezone.utc).isoformat()),
        "created_by_admin": current_user['id']
    }
    
    await db.teacher_sessions.insert_one(manual_session)
    logger.info(f"Manual session created by admin {current_user['id']} for teacher {session_data['teacher_email']}")
    
    return {"message": "Session enregistrée avec succès", "session_id": manual_session['id']}


@router.get("/admin/all-students-availability")
async def get_all_students_availability(current_user: dict = Depends(get_current_user)):
    """Admin gets availability of all students"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all students
    students = await db.users.find(
        {"role": "student"},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "assigned_teacher": 1}
    ).to_list(1000)
    
    # Get all availabilities
    availabilities = await db.student_availability.find({}, {"_id": 0}).to_list(1000)
    
    # Merge
    result = []
    for student in students:
        avail = next((a for a in availabilities if a['student_id'] == student['id']), {"slots": []})
        
        # Get teacher name if assigned
        teacher_name = None
        if student.get('assigned_teacher'):
            teacher = await db.users.find_one({"id": student['assigned_teacher']}, {"_id": 0, "first_name": 1, "last_name": 1})
            if teacher:
                teacher_name = f"{teacher['first_name']} {teacher['last_name']}"
        
        result.append({
            "student_id": student['id'],
            "student_name": f"{student['first_name']} {student['last_name']}",
            "email": student.get('email'),
            "teacher_name": teacher_name,
            "slots": avail.get('slots', []),
            "updated_at": avail.get('updated_at')
        })
    
    return result


@router.post("/admin/create-badge")
async def create_badge(data: BadgeCreate, current_user: dict = Depends(get_current_user)):
    """Admin creates a new badge"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    badge = Badge(
        name=data.name,
        icon=data.icon,
        description=data.description,
        condition_type=data.condition_type,
        condition_value=data.condition_value
    )
    
    doc = badge.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.badges.insert_one(doc)
    
    logger.info(f"Badge created by admin: {badge.name}")
    return {"message": "Badge créé", "badge_id": badge.id}


@router.post("/admin/award-badge")
async def award_badge(data: dict, current_user: dict = Depends(get_current_user)):
    """Admin awards a badge to a student"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student_id = data['student_id']
    badge_id = data['badge_id']
    
    # Check if student already has this badge
    existing = await db.student_badges.find_one({
        "student_id": student_id,
        "badge_id": badge_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Badge déjà attribué")
    
    student_badge = StudentBadge(
        student_id=student_id,
        badge_id=badge_id
    )
    
    doc = student_badge.model_dump()
    doc['awarded_at'] = doc['awarded_at'].isoformat()
    await db.student_badges.insert_one(doc)
    
    # Get badge info for notification
    badge = await db.badges.find_one({"id": badge_id}, {"_id": 0})
    
    # Create notification
    await create_notification(
        user_id=student_id,
        title=f"🏆 Nouveau badge obtenu !",
        message=f"Félicitations ! Vous avez reçu le badge '{badge['name']}'",
        notification_type="badge"
    )
    
    logger.info(f"Badge {badge_id} awarded to student {student_id}")
    return {"message": "Badge attribué"}


@router.delete("/admin/remove-badge/{student_id}/{badge_id}")
async def remove_badge(student_id: str, badge_id: str, current_user: dict = Depends(get_current_user)):
    """Admin removes a badge from a student"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.student_badges.delete_one({
        "student_id": student_id,
        "badge_id": badge_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Badge non trouvé")
    
    return {"message": "Badge retiré"}

# ==================== WEEKLY CHALLENGES & POINTS ENDPOINTS ====================


@router.get("/test-questions/{level}")
async def get_test_questions(level: str):
    """Get test questions for a specific level (public endpoint)"""
    questions = await db.test_questions.find({"level": level, "active": True}, {"_id": 0}).to_list(100)
    return questions


@router.get("/admin/all-test-questions")
async def get_all_test_questions(current_user: dict = Depends(get_current_user)):
    """Get all test questions (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    questions = await db.test_questions.find({}, {"_id": 0}).to_list(1000)
    return questions


@router.post("/admin/create-test-question")
async def create_test_question(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new test question"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    question = {
        "id": str(uuid4()),
        "level": data['level'],  # beginner, intermediate, advanced
        "question_type": data['question_type'],  # 'mcq' or 'true_false'
        "question": data['question'],
        "options": data.get('options', []),  # for MCQ
        "correct_answer": data['correct_answer'],
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.test_questions.insert_one(question)
    return {"message": "Question created", "question_id": question['id']}


@router.put("/admin/update-test-question/{question_id}")
async def update_test_question(question_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Update a test question"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {
        "question": data['question'],
        "options": data.get('options', []),
        "correct_answer": data['correct_answer'],
        "active": data.get('active', True)
    }
    
    result = await db.test_questions.update_one(
        {"id": question_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question updated"}


@router.delete("/admin/delete-test-question/{question_id}")
async def delete_test_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a test question"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.test_questions.delete_one({"id": question_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question deleted"}

# ============ VIDEOS FOR KIDS ============


@router.post("/admin/promo-codes")
async def create_promo_code(
    code: str,
    discount_percent: int,
    valid_until: str,
    max_uses: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a new promo code - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    code_upper = code.upper()
    
    # Check if code already exists
    existing = await db.promo_codes.find_one({"code": code_upper})
    if existing:
        raise HTTPException(status_code=400, detail="Ce code promo existe déjà")
    
    # Parse date
    valid_until_dt = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
    
    promo = {
        "id": str(uuid4()),
        "code": code_upper,
        "discount_percent": discount_percent,
        "valid_until": valid_until_dt.isoformat(),
        "max_uses": max_uses,
        "current_uses": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promo_codes.insert_one(promo)
    logger.info(f"Promo code created by admin {current_user['id']}: {code_upper}")
    
    return {"message": "Code promo créé", "code": code_upper}


@router.get("/admin/promo-codes")
async def get_promo_codes(current_user: dict = Depends(get_current_user)):
    """Get all promo codes - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    codes = await db.promo_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return codes



# ============ LEAVE BALANCE (CONGES PAYES) ============

@router.get("/admin/leave-balances")
async def get_all_leave_balances(current_user: dict = Depends(get_current_user)):
    """Get leave balances for all employees (teachers, secretary, admin)"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Admin or secretary access required")
    
    employees = await db.users.find(
        {"role": {"$in": ["teacher", "secretary", "admin"]}, "is_active": True},
        {"_id": 0, "password_hash": 0, "temporary_password": 0}
    ).to_list(200)
    
    results = []
    for emp in employees:
        balance = await db.leave_balances.find_one({"user_id": emp['id']}, {"_id": 0})
        
        if not balance:
            # Calculate from creation date
            created_at = emp.get('created_at')
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
            
            balance = {
                "id": str(uuid4()),
                "user_id": emp['id'],
                "total_earned": total_earned,
                "total_taken": 0,
                "remaining": total_earned,
                "start_date": created_at if isinstance(created_at, str) else created_at.isoformat() if created_at else datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.leave_balances.insert_one({**balance})
        else:
            # Recalculate earned days
            start = balance.get('start_date', emp.get('created_at'))
            if isinstance(start, str):
                try:
                    from dateutil import parser as dt_parser
                    start_date = dt_parser.parse(start)
                except Exception:
                    start_date = datetime.now(timezone.utc)
            else:
                start_date = start or datetime.now(timezone.utc)
            
            now = datetime.now(timezone.utc)
            if start_date.tzinfo is None:
                from datetime import timezone as tz
                start_date = start_date.replace(tzinfo=tz.utc)
            
            months_worked = max(0, (now.year - start_date.year) * 12 + (now.month - start_date.month))
            total_earned = round(months_worked * 2.5, 1)
            if total_earned > 30:
                total_earned = 30.0
            
            total_taken = balance.get('total_taken', 0)
            remaining = total_earned - total_taken
            
            await db.leave_balances.update_one(
                {"user_id": emp['id']},
                {"$set": {"total_earned": total_earned, "remaining": remaining, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            balance['total_earned'] = total_earned
            balance['remaining'] = remaining
        
        results.append({
            "user_id": emp['id'],
            "first_name": emp.get('first_name', ''),
            "last_name": emp.get('last_name', ''),
            "email": emp.get('email', ''),
            "role": emp.get('role', ''),
            "total_earned": balance.get('total_earned', 0),
            "total_taken": balance.get('total_taken', 0),
            "remaining": balance.get('remaining', 0),
            "start_date": balance.get('start_date', '')
        })
    
    return results


@router.get("/admin/leave-balance/{user_id}")
async def get_user_leave_balance(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get leave balance for a specific user"""
    if current_user['role'] not in ['admin', 'secretary'] and current_user['id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    balance = await db.leave_balances.find_one({"user_id": user_id}, {"_id": 0})
    
    created_at = user.get('created_at')
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
    
    total_taken = 0
    if balance:
        total_taken = balance.get('total_taken', 0)
    
    remaining = total_earned - total_taken
    
    # Update or create balance
    if balance:
        await db.leave_balances.update_one(
            {"user_id": user_id},
            {"$set": {"total_earned": total_earned, "remaining": remaining, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.leave_balances.insert_one({
            "id": str(uuid4()),
            "user_id": user_id,
            "total_earned": total_earned,
            "total_taken": total_taken,
            "remaining": remaining,
            "start_date": created_at if isinstance(created_at, str) else created_at.isoformat() if created_at else now.isoformat(),
            "updated_at": now.isoformat()
        })
    
    # Get approved leaves
    approved_leaves = await db.leave_requests.find(
        {"teacher_id": user_id, "status": "approved"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "user_id": user_id,
        "first_name": user.get('first_name', ''),
        "last_name": user.get('last_name', ''),
        "role": user.get('role', ''),
        "months_worked": months_worked,
        "total_earned": total_earned,
        "total_taken": total_taken,
        "remaining": remaining,
        "approved_leaves": approved_leaves
    }
