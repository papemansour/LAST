"""Auto-generated route module."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import Response
from config import db, logger, get_current_user, hash_password, verify_password, create_access_token, FRONTEND_URL, SECRET_KEY, ALGORITHM, security, pwd_context
from models.schemas import User, WelcomeLetter
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

@router.get("/secretary/meetings")
async def get_secretary_meetings(current_user: dict = Depends(get_current_user)):
    """Get all meetings created by secretary"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    meetings = await db.secretary_meetings.find({}, {"_id": 0}).sort("date", -1).to_list(100)
    return meetings


@router.post("/secretary/meetings")
async def create_secretary_meeting(meeting_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new meeting"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    meeting = {
        "id": str(uuid4()),
        "title": meeting_data.get("title"),
        "date": meeting_data.get("date"),
        "time": meeting_data.get("time"),
        "attendees": meeting_data.get("attendees", ""),
        "notes": meeting_data.get("notes", ""),
        "meeting_link": meeting_data.get("meetingLink", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.secretary_meetings.insert_one(meeting)
    logger.info(f"Meeting created by secretary: {meeting['title']}")
    return {"message": "Meeting created", "id": meeting['id']}


@router.delete("/secretary/meetings/{meeting_id}")
async def delete_secretary_meeting(meeting_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a meeting"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.secretary_meetings.delete_one({"id": meeting_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting deleted"}


@router.put("/secretary/meetings/{meeting_id}")
async def update_secretary_meeting(meeting_id: str, meeting_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update a meeting"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    update_data = {
        "title": meeting_data.get("title"),
        "date": meeting_data.get("date"),
        "time": meeting_data.get("time"),
        "attendees": meeting_data.get("attendees", ""),
        "notes": meeting_data.get("notes", ""),
        "meetingLink": meeting_data.get("meetingLink", ""),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.secretary_meetings.update_one(
        {"id": meeting_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting updated"}


@router.get("/secretary/reports")
async def get_secretary_reports(current_user: dict = Depends(get_current_user)):
    """Get all teacher reports"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    reports = await db.teacher_reports.find({}, {"_id": 0}).sort("date", -1).to_list(100)
    return reports


@router.post("/secretary/reports")
async def create_secretary_report(report_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new teacher report"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    report = {
        "id": str(uuid4()),
        "prof_name": report_data.get("profName"),
        "date": report_data.get("date"),
        "content": report_data.get("content"),
        "notes": report_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.teacher_reports.insert_one(report)
    logger.info(f"Teacher report created for: {report['prof_name']}")
    return {"message": "Report created", "id": report['id']}


@router.delete("/secretary/reports/{report_id}")
async def delete_secretary_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a teacher report"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.teacher_reports.delete_one({"id": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted"}

# SECRETARY BILLING ENDPOINTS


@router.get("/secretary/teacher-payments")
async def get_teacher_payments(current_user: dict = Depends(get_current_user)):
    """Get all teacher payments"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    payments = await db.teacher_payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments


@router.post("/secretary/teacher-payments")
async def create_teacher_payment(payment_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a teacher payment record with deductions system"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    # Support both camelCase and snake_case field names
    teacher_id = payment_data.get("teacherId") or payment_data.get("teacher_id", "")
    teacher_name = payment_data.get("teacherName") or payment_data.get("teacher_name", "")
    teacher_email = payment_data.get("teacherEmail") or payment_data.get("teacher_email", "")
    
    # Get deductions and bonus
    deductions = int(payment_data.get("deductions", 0))
    bonus = float(payment_data.get("bonus", 0))
    amount = float(payment_data.get("amount", 0))
    currency = payment_data.get("currency", "EUR")
    
    # Calculate net amount
    deduction_unit = 5 if currency == "EUR" else 1500
    deductions_amount = deductions * deduction_unit
    montant_initial = amount + bonus
    montant_net = max(0, montant_initial - deductions_amount)
    
    # Generate invoice reference: FAC-YYYY-XXX
    year = datetime.now(timezone.utc).year
    count = await db.teacher_payments.count_documents({"created_at": {"$gte": f"{year}-01-01"}})
    invoice_ref = f"FAC-{year}-{str(count + 1).zfill(3)}"
    
    # Determine visibility based on day of month
    # - Created 25-28: visible_from = 29th of month
    # - Created 29+: visible immediately
    now = datetime.now(timezone.utc)
    day_of_month = now.day
    
    if 25 <= day_of_month <= 28:
        # Bulletin visible from 29th
        if now.month == 12:
            visible_from = datetime(now.year + 1, 1, 29, tzinfo=timezone.utc).isoformat()
        else:
            visible_from = datetime(now.year, now.month, 29, tzinfo=timezone.utc).isoformat()
    else:
        # Visible immediately
        visible_from = now.isoformat()
    
    payment = {
        "id": str(uuid4()),
        "invoice_ref": invoice_ref,
        "teacher_id": teacher_id,
        "teacher_name": teacher_name,
        "teacher_email": teacher_email,
        "teacher_address": payment_data.get("teacherAddress") or payment_data.get("teacher_address", ""),
        "month": payment_data.get("month"),
        "period": payment_data.get("month"),
        "amount": amount,
        "currency": currency,
        "hours_worked": payment_data.get("hoursWorked") or payment_data.get("hours_worked") or payment_data.get("hours", ""),
        "hourly_rate": payment_data.get("hourlyRate") or payment_data.get("hourly_rate", ""),
        "bonus": bonus,
        "deductions": deductions,
        "deductions_amount": deductions_amount,
        "montant_initial": montant_initial,
        "montant_net": montant_net,
        "description": payment_data.get("description", "Cours de langue anglaise"),
        "notes": payment_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "visible_from": visible_from,
        "status": "pending" if 25 <= day_of_month <= 28 else "visible"
    }
    
    await db.teacher_payments.insert_one(payment)
    
    # Sync to Monday.com
    try:
        from monday_integration import create_invoice_in_monday
        create_invoice_in_monday(payment, "teacher")
    except Exception as e:
        logger.warning(f"Could not sync teacher payment to Monday: {e}")
    
    logger.info(f"Teacher payment created for: {payment['teacher_name']} - Net: {montant_net} {currency} - Ref: {invoice_ref} - Status: {payment['status']}")
    return {"message": "Payment created", "id": payment['id'], "montant_net": montant_net, "invoice_ref": invoice_ref}


@router.delete("/secretary/teacher-payments/{payment_id}")
async def delete_teacher_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a teacher payment"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.teacher_payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment deleted"}


@router.get("/secretary/student-receipts")
async def get_student_receipts(current_user: dict = Depends(get_current_user)):
    """Get all student receipts"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    receipts = await db.student_receipts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return receipts


@router.post("/secretary/student-receipts")
async def create_student_receipt(receipt_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a student receipt"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    # Handle both camelCase and snake_case field names from frontend
    student_id = receipt_data.get("student_id") or receipt_data.get("studentId")
    student_name = receipt_data.get("student_name") or receipt_data.get("studentName")
    pack_name = receipt_data.get("pack_name") or receipt_data.get("packType") or receipt_data.get("pack_type", "")
    
    receipt = {
        "id": str(uuid4()),
        "student_id": student_id,
        "student_name": student_name,
        "pack_name": pack_name,
        "amount": receipt_data.get("amount"),
        "currency": receipt_data.get("currency", "EUR"),
        "payment_method": receipt_data.get("payment_method") or receipt_data.get("paymentMethod", "Virement"),
        "notes": receipt_data.get("notes", ""),
        "email": receipt_data.get("email", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.student_receipts.insert_one(receipt)
    
    # Create notification for the student
    if student_id:
        await create_notification(
            user_id=student_id,
            title="Nouveau recu de paiement",
            message=f"Un recu de {receipt['amount']} {receipt['currency']} a ete genere pour vous.",
            notification_type="payment"
        )
    
    # Sync to Monday.com
    try:
        from monday_integration import create_invoice_in_monday
        create_invoice_in_monday(receipt, "student")
    except Exception as e:
        logger.warning(f"Could not sync student receipt to Monday: {e}")
    
    logger.info(f"Student receipt created for: {receipt['student_name']} - {receipt['amount']} {receipt['currency']}")
    return {"message": "Receipt created", "id": receipt['id']}


@router.delete("/secretary/student-receipts/{receipt_id}")
async def delete_student_receipt(receipt_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a student receipt"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.student_receipts.delete_one({"id": receipt_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return {"message": "Receipt deleted"}


# Communication Staff Payments endpoints

@router.get("/secretary/com-payments")
async def get_com_payments(current_user: dict = Depends(get_current_user)):
    """Get all communication staff payments"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    payments = await db.com_payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments


@router.post("/secretary/com-payments")
async def create_com_payment(payment_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a communication staff payment (like teacher payment with bonuses/deductions)"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    com_code = payment_data.get("comCode", "").upper()
    if com_code not in ['MBM', 'FZT']:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    currency = payment_data.get("currency", "EUR")
    deduction_rate = 1500 if currency == "FCFA" else 5
    
    amount = float(payment_data.get("amount", 0))
    bonus = float(payment_data.get("bonus", 0))
    deductions = int(payment_data.get("deductions", 0))
    deductions_amount = deductions * deduction_rate
    montant_net = max(0, amount + bonus - deductions_amount)
    
    # Generate invoice reference
    invoice_ref = f"COM-{com_code}-{datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"
    
    payment = {
        "id": str(uuid4()),
        "com_code": com_code,
        "comCode": com_code,
        "com_name": payment_data.get("comName", f"{com_code} - Chargé(e) de Com"),
        "month": payment_data.get("month", ""),
        "amount": amount,
        "currency": currency,
        "hours_worked": payment_data.get("hoursWorked", 0),
        "hourly_rate": payment_data.get("hourlyRate", 0),
        "bonus": bonus,
        "deductions": deductions,
        "deductions_amount": deductions_amount,
        "montant_net": montant_net,
        "description": payment_data.get("description", "Travail de communication"),
        "notes": payment_data.get("notes", ""),
        "invoice_ref": invoice_ref,
        "status": "pending",
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.com_payments.insert_one(payment)
    logger.info(f"Com payment created for: {com_code} - Net: {montant_net} {currency} - Ref: {invoice_ref}")
    return {"message": "Payment created", "id": payment['id'], "montant_net": montant_net, "invoice_ref": invoice_ref}


@router.delete("/secretary/com-payments/{payment_id}")
async def delete_com_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a communication staff payment"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.com_payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment deleted"}


# Prestataire invoices endpoints


@router.get("/secretary/prestataire-invoices")
async def get_prestataire_invoices(current_user: dict = Depends(get_current_user)):
    """Get all prestataire invoices"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    invoices = await db.prestataire_invoices.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return invoices


@router.post("/secretary/prestataire-invoices")
async def create_prestataire_invoice(invoice_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a prestataire invoice"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    invoice = {
        "id": str(uuid4()),
        "name": invoice_data.get("name"),
        "service": invoice_data.get("service"),
        "amount": invoice_data.get("amount"),
        "currency": invoice_data.get("currency", "EUR"),
        "description": invoice_data.get("description", ""),
        "notes": invoice_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.prestataire_invoices.insert_one(invoice)
    
    # Sync to Monday.com
    try:
        from monday_integration import create_invoice_in_monday
        create_invoice_in_monday(invoice, "prestataire")
    except Exception as e:
        logger.warning(f"Could not sync prestataire invoice to Monday: {e}")
    
    logger.info(f"Prestataire invoice created for: {invoice['name']} - {invoice['amount']} {invoice['currency']}")
    return {"message": "Invoice created", "id": invoice['id']}


@router.delete("/secretary/prestataire-invoices/{invoice_id}")
async def delete_prestataire_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a prestataire invoice"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.prestataire_invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"message": "Invoice deleted"}


@router.post("/secretary/send-invoice-email")
async def send_invoice_by_email(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Send invoice by email - Sans TVA, avec système de déductions pour professeurs"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    invoice_type = data.get("invoice_type", "student")
    recipient_email = data.get("recipient_email")
    recipient_name = data.get("recipient_name", "")
    amount = float(data.get("amount", 0))
    currency = data.get("currency", "EUR")
    bonus = float(data.get("bonus", 0))
    deductions = int(data.get("deductions", 0))
    period = data.get("period", "")
    
    # Calcul avec système de déductions (sans TVA)
    deduction_unit = 5 if currency == "EUR" else 1500  # 5€ ou 1500 FCFA par cours manqué
    deductions_amount = deductions * deduction_unit
    montant_initial = amount + bonus
    montant_net = max(0, montant_initial - deductions_amount)
    
    # Générer le contenu de l'email
    subject = f"Bulletin de Salaire MyKalama English - {recipient_name}" if invoice_type == 'teacher' else f"Reçu de Paiement MyKalama English - {recipient_name}"
    
    if invoice_type == 'teacher':
        # Email pour professeur avec système de déductions
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🎓 MyKalama English</h1>
                    <p style="color: rgba(255,255,255,0.9); margin-top: 10px;">Bulletin de Salaire</p>
                </div>
                <div style="padding: 30px;">
                    <p>Bonjour <strong>{recipient_name}</strong>,</p>
                    <p>Veuillez trouver ci-dessous votre bulletin de salaire{' pour ' + period if period else ''} :</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #f3f4f6;">
                            <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>Montant de base</strong></td>
                            <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right;">{amount:.2f} {currency}</td>
                        </tr>
                        {"<tr style='background: #d1fae5;'><td style='padding: 12px; border: 1px solid #e5e7eb;'><strong>+ Bonus</strong></td><td style='padding: 12px; border: 1px solid #e5e7eb; text-align: right; color: #059669;'>+{:.2f} {}</td></tr>".format(bonus, currency) if bonus > 0 else ""}
                        <tr style="background: #f9fafb;">
                            <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>Somme Initiale</strong></td>
                            <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right; font-weight: bold;">{montant_initial:.2f} {currency}</td>
                        </tr>
                        {"<tr style='background: #fef2f2;'><td style='padding: 12px; border: 1px solid #e5e7eb;'><strong>⚠️ Déductions ({} cours manqués × {} {})</strong></td><td style='padding: 12px; border: 1px solid #e5e7eb; text-align: right; color: #dc2626;'>-{:.2f} {}</td></tr>".format(deductions, deduction_unit, currency, deductions_amount, currency) if deductions > 0 else ""}
                        <tr style="background: #d1fae5;">
                            <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>💰 SOMME NETTE À RECEVOIR</strong></td>
                            <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right; font-weight: bold; font-size: 18px; color: #059669;">{montant_net:.2f} {currency}</td>
                        </tr>
                    </table>
                    
                    {"<p style='background: #fef2f2; padding: 10px; border-radius: 6px; color: #991b1b; font-size: 14px;'><strong>Note:</strong> {} déduction(s) appliquée(s) pour cours manqué(s) à {} {}/cours</p>".format(deductions, deduction_unit, currency) if deductions > 0 else ""}
                    
                    <p style="margin-top: 30px;">Cordialement,<br><strong>L'équipe MyKalama English</strong></p>
                </div>
                <div style="background: #1f2937; color: white; padding: 20px; text-align: center; font-size: 12px;">
                    <p>MyKalama English - Paris, France / Dakar, Sénégal</p>
                    <p>📞 +221 78 260 75 49 / 78 528 68 89</p>
                    <p>📧 mykalamaenglish@gmail.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Bulletin de Salaire MyKalama English - {recipient_name}
        
        Bonjour {recipient_name},
        
        Veuillez trouver ci-dessous votre bulletin de salaire{' pour ' + period if period else ''} :
        
        Montant de base: {amount:.2f} {currency}
        {"Bonus: +{:.2f} {}".format(bonus, currency) if bonus > 0 else ""}
        Somme Initiale: {montant_initial:.2f} {currency}
        {"Déductions ({} cours × {} {}): -{:.2f} {}".format(deductions, deduction_unit, currency, deductions_amount, currency) if deductions > 0 else ""}
        SOMME NETTE À RECEVOIR: {montant_net:.2f} {currency}
        
        Cordialement,
        L'équipe MyKalama English
        
        📞 +221 78 260 75 49 / 78 528 68 89
        📧 mykalamaenglish@gmail.com
        """
    else:
        # Email pour étudiant (reçu simple sans TVA)
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🎓 MyKalama English</h1>
                    <p style="color: rgba(255,255,255,0.9); margin-top: 10px;">Reçu de Paiement</p>
                </div>
                <div style="padding: 30px;">
                    <p>Bonjour <strong>{recipient_name}</strong>,</p>
                    <p>Nous vous confirmons la réception de votre paiement :</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #dbeafe;">
                            <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>💰 MONTANT PAYÉ</strong></td>
                            <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right; font-weight: bold; font-size: 18px; color: #3b82f6;">{amount:.2f} {currency}</td>
                        </tr>
                    </table>
                    
                    <p style="margin-top: 30px;">Merci pour votre confiance !<br><strong>L'équipe MyKalama English</strong></p>
                </div>
                <div style="background: #1f2937; color: white; padding: 20px; text-align: center; font-size: 12px;">
                    <p>MyKalama English - Paris, France / Dakar, Sénégal</p>
                    <p>📞 +221 78 260 75 49 / 78 528 68 89</p>
                    <p>📧 mykalamaenglish@gmail.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reçu de Paiement MyKalama English - {recipient_name}
        
        Bonjour {recipient_name},
        
        Nous vous confirmons la réception de votre paiement :
        
        MONTANT PAYÉ: {amount:.2f} {currency}
        
        Merci pour votre confiance !
        L'équipe MyKalama English
        
        📞 +221 78 260 75 49 / 78 528 68 89
        📧 mykalamaenglish@gmail.com
        """
    
    # Envoyer via le service email
    email_sent = await email_service.send_invoice_email(
        recipient_email,
        recipient_name,
        subject,
        html_content,
        text_content
    )
    
    # Sauvegarder l'email dans la base
    await db.pending_emails.insert_one({
        "id": str(uuid4()),
        "to": recipient_email,
        "subject": subject,
        "html_content": html_content,
        "invoice_type": invoice_type,
        "amount": amount,
        "bonus": bonus,
        "deductions": deductions,
        "deductions_amount": deductions_amount,
        "montant_net": montant_net,
        "currency": currency,
        "status": "sent" if email_sent else "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Invoice email {'sent' if email_sent else 'prepared'} for: {recipient_email} - Net: {montant_net:.2f} {currency}")
    return {"message": "Invoice email sent" if email_sent else "Invoice email queued", "recipient": recipient_email, "sent": email_sent, "montant_net": montant_net}


@router.post("/secretary/reset-billing-stats")
async def reset_billing_stats(current_user: dict = Depends(get_current_user)):
    """Reset all billing statistics (delete all payments, receipts, invoices)"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    # Delete all billing data
    deleted_payments = await db.teacher_payments.delete_many({})
    deleted_receipts = await db.student_receipts.delete_many({})
    deleted_invoices = await db.prestataire_invoices.delete_many({})
    
    logger.info(f"Billing stats reset by {current_user['id']}: {deleted_payments.deleted_count} payments, {deleted_receipts.deleted_count} receipts, {deleted_invoices.deleted_count} invoices")
    
    return {
        "message": "Statistiques de facturation remises à zéro",
        "deleted": {
            "teacher_payments": deleted_payments.deleted_count,
            "student_receipts": deleted_receipts.deleted_count,
            "prestataire_invoices": deleted_invoices.deleted_count
        }
    }


@router.get("/secretary/teachers-list")
async def get_teachers_list_for_secretary(current_user: dict = Depends(get_current_user)):
    """Get list of all teachers for secretary billing"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    teachers = await db.users.find(
        {"role": "teacher", "is_active": True}, 
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    ).to_list(100)
    return teachers


@router.get("/secretary/students-list")
async def get_students_list_for_secretary(current_user: dict = Depends(get_current_user)):
    """Get list of all students for secretary billing"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    students = await db.users.find(
        {"role": "student", "is_active": True}, 
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "level": 1}
    ).to_list(500)
    return students


@router.get("/secretary/admin-info")
async def get_admin_info_for_secretary(current_user: dict = Depends(get_current_user)):
    """Get admin info for secretary messaging"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    admin = await db.users.find_one(
        {"role": "admin", "is_active": True}, 
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    )
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


# ============ GENERIC STAFF MANAGEMENT ENDPOINTS ============
# For all staff: communication, secretary, and any admin-created staff

@router.get("/secretary/all-staff")
async def get_all_staff(current_user: dict = Depends(get_current_user)):
    """Get ALL staff members (admin, secretary, teachers, communication, and any user created by admin)"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    # Get ALL staff: admin, secretary, teachers, communication, staff (everyone except students)
    staff_users = await db.users.find(
        {
            "role": {"$in": ["admin", "secretary", "teacher", "communication", "staff"]},
            "is_active": True
        },
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "role": 1, "phone": 1}
    ).to_list(200)
    
    # Get all staff leaves to calculate used days
    all_leaves = await db.staff_leaves.find({}, {"_id": 0, "staff_id": 1, "days_used": 1, "daysUsed": 1}).to_list(500)
    
    # Calculate leaves used per staff
    leaves_by_staff = {}
    for leave in all_leaves:
        staff_id = leave.get("staff_id") or leave.get("staffId")
        days = leave.get("days_used") or leave.get("daysUsed") or 0
        if staff_id:
            leaves_by_staff[staff_id] = leaves_by_staff.get(staff_id, 0) + int(days)
    
    # Role labels for display
    role_labels = {
        "admin": "Admin",
        "secretary": "Secrétaire",
        "teacher": "Professeur",
        "communication": "Chargé(e) de Com",
        "staff": "Staff"
    }
    
    # Build staff list with name for display
    result = []
    for staff in staff_users:
        staff_id = staff.get("id")
        leaves_used = leaves_by_staff.get(staff_id, 0)
        result.append({
            "id": staff_id,
            "name": f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip(),
            "first_name": staff.get("first_name", ""),
            "last_name": staff.get("last_name", ""),
            "email": staff.get("email", ""),
            "role": staff.get("role", "staff"),
            "role_label": role_labels.get(staff.get("role", ""), staff.get("role", "")),
            "phone": staff.get("phone", ""),
            "leaves_used": leaves_used,
            "leaves_total": 30
        })
    
    return result


@router.get("/secretary/staff-payments")
async def get_staff_payments(current_user: dict = Depends(get_current_user)):
    """Get all staff payments"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    payments = await db.staff_payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments


@router.post("/secretary/staff-payments")
async def create_staff_payment(payment_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a staff payment (like teacher payment with bonuses/deductions)"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    staff_id = payment_data.get("staffId") or payment_data.get("staff_id", "")
    staff_name = payment_data.get("staffName") or payment_data.get("staff_name", "")
    staff_role = payment_data.get("staffRole") or payment_data.get("staff_role", "staff")
    
    currency = payment_data.get("currency", "EUR")
    deduction_rate = 1500 if currency == "FCFA" else 5
    
    amount = float(payment_data.get("amount", 0))
    bonus = float(payment_data.get("bonus", 0))
    deductions = int(payment_data.get("deductions", 0))
    deductions_amount = deductions * deduction_rate
    montant_net = max(0, amount + bonus - deductions_amount)
    
    # Generate invoice reference
    invoice_ref = f"STAFF-{staff_id[:3].upper() if staff_id else 'XXX'}-{datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"
    
    payment = {
        "id": str(uuid4()),
        "staff_id": staff_id,
        "staffId": staff_id,
        "staff_name": staff_name,
        "staffName": staff_name,
        "staff_role": staff_role,
        "staffRole": staff_role,
        "month": payment_data.get("month", ""),
        "amount": amount,
        "currency": currency,
        "hours_worked": payment_data.get("hoursWorked") or payment_data.get("hours_worked", 0),
        "hourly_rate": payment_data.get("hourlyRate") or payment_data.get("hourly_rate", 0),
        "bonus": bonus,
        "deductions": deductions,
        "deductions_amount": deductions_amount,
        "montant_net": montant_net,
        "description": payment_data.get("description", "Travail staff"),
        "notes": payment_data.get("notes", ""),
        "invoice_ref": invoice_ref,
        "status": "pending",
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.staff_payments.insert_one(payment)
    logger.info(f"Staff payment created for: {staff_name} ({staff_role}) - Net: {montant_net} {currency} - Ref: {invoice_ref}")
    return {"message": "Payment created", "id": payment['id'], "montant_net": montant_net, "invoice_ref": invoice_ref}


@router.delete("/secretary/staff-payments/{payment_id}")
async def delete_staff_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a staff payment"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.staff_payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment deleted"}


@router.get("/secretary/staff-leaves")
async def get_staff_leaves(current_user: dict = Depends(get_current_user)):
    """Get all staff leaves"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    leaves = await db.staff_leaves.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return leaves


@router.post("/secretary/staff-leaves")
async def create_staff_leave(leave_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a staff leave record"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    staff_id = leave_data.get("staffId") or leave_data.get("staff_id", "")
    staff_name = leave_data.get("staffName") or leave_data.get("staff_name", "")
    start_date = leave_data.get("startDate") or leave_data.get("start_date", "")
    end_date = leave_data.get("endDate") or leave_data.get("end_date", "")
    days_used = int(leave_data.get("daysUsed") or leave_data.get("days_used", 0))
    reason = leave_data.get("reason", "")
    
    leave = {
        "id": str(uuid4()),
        "staff_id": staff_id,
        "staffId": staff_id,
        "staff_name": staff_name,
        "staffName": staff_name,
        "start_date": start_date,
        "startDate": start_date,
        "end_date": end_date,
        "endDate": end_date,
        "days_used": days_used,
        "daysUsed": days_used,
        "reason": reason,
        "status": "approved",
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.staff_leaves.insert_one(leave)
    logger.info(f"Staff leave created for: {staff_name} - {days_used} days from {start_date} to {end_date}")
    return {"message": "Leave created", "id": leave['id'], "days_used": days_used}


@router.delete("/secretary/staff-leaves/{leave_id}")
async def delete_staff_leave(leave_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a staff leave"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.staff_leaves.delete_one({"id": leave_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Leave not found")
    
    return {"message": "Leave deleted"}


