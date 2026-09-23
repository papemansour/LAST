"""Communication routes for the communication manager role."""
from fastapi import APIRouter, HTTPException, Depends, Body
from config import db, logger, get_current_user
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter()

# Valid communication codes
VALID_COM_CODES = ['MBM', 'FZT']

# ==================== STATS ====================
@router.get("/communication/stats")
async def get_communication_stats(current_user: dict = Depends(get_current_user)):
    """Get communication statistics"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    total_students = await db.users.count_documents({"role": "student", "is_active": True})
    total_teachers = await db.users.count_documents({"role": "teacher", "is_active": True})
    total_news = await db.news.count_documents({})
    
    return {
        "totalStudents": total_students,
        "totalTeachers": total_teachers,
        "totalNews": total_news
    }


# ==================== AVAILABILITY (like teachers) ====================
@router.post("/communication/set-availability")
async def set_com_availability(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Set availability for a communication manager (same format as teachers)"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    com_code = data.get("com_code", "").upper()
    if com_code not in VALID_COM_CODES:
        raise HTTPException(status_code=400, detail="Invalid communication code (MBM or FZT)")
    
    availability_entry = {
        "id": str(uuid4()),
        "com_code": com_code,
        "availability": data.get('availability', {}),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.communication_availability.delete_many({"com_code": com_code})
    await db.communication_availability.insert_one(availability_entry)
    
    logger.info(f"Availability set by {com_code}")
    return {"message": "Disponibilités mises à jour"}


@router.get("/communication/my-availability/{com_code}")
async def get_com_availability(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get availability for a specific communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    if code not in VALID_COM_CODES:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    availability = await db.communication_availability.find_one({"com_code": code}, {"_id": 0})
    return availability or {"availability": {}, "com_code": code}


@router.get("/communication/all-availability")
async def get_all_com_availability(current_user: dict = Depends(get_current_user)):
    """Get availability for all communication managers (admin/secretary view)"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    availabilities = await db.communication_availability.find({}, {"_id": 0}).to_list(10)
    
    result = []
    codes_found = [a['com_code'] for a in availabilities]
    
    for code in VALID_COM_CODES:
        if code in codes_found:
            result.append(next(a for a in availabilities if a['com_code'] == code))
        else:
            result.append({"com_code": code, "availability": {}})
    
    return result


# ==================== BALANCE/PAYSLIPS (like teachers) ====================
@router.get("/communication/balance/{com_code}")
async def get_com_balance(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get balance and payment history for a communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    if code not in VALID_COM_CODES:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    # Get all payments for this code
    payments = await db.communication_payments.find(
        {"com_code": code},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Calculate totals
    pending_amount = sum(p.get('amount', 0) for p in payments if p.get('status') == 'pending')
    paid_amount = sum(p.get('amount', 0) for p in payments if p.get('status') == 'paid')
    total_hours = sum(p.get('hours', 0) for p in payments)
    
    return {
        "pendingAmount": pending_amount,
        "paidAmount": paid_amount,
        "totalHours": total_hours,
        "payments": payments
    }


@router.post("/communication/payments")
async def create_com_payment(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a payment entry for a communication manager (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    com_code = data.get("com_code", "").upper()
    if com_code not in VALID_COM_CODES:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    # Validate amount and hours
    try:
        amount = float(data.get("amount", 0))
        hours = float(data.get("hours", 0))
        if amount < 0:
            raise HTTPException(status_code=400, detail="Le montant doit être positif")
        if hours < 0:
            raise HTTPException(status_code=400, detail="Les heures doivent être positives")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Montant ou heures invalides")
    
    # Validate status
    valid_statuses = ['pending', 'paid']
    status = data.get("status", "pending")
    if status not in valid_statuses:
        status = "pending"
    
    payment = {
        "id": str(uuid4()),
        "com_code": com_code,
        "month": data.get("month", ""),
        "year": data.get("year", datetime.now().year),
        "amount": amount,
        "hours": hours,
        "status": status,
        "notes": data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.communication_payments.insert_one(payment)
    logger.info(f"Payment created for {com_code} by {current_user['email']}: {payment['amount']}€")
    
    return {"message": "Paiement créé", "id": payment['id']}


@router.put("/communication/payments/{payment_id}/status")
async def update_payment_status(payment_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update payment status"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.communication_payments.update_one(
        {"id": payment_id},
        {"$set": {"status": data.get("status", "paid"), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Statut mis à jour"}


@router.get("/communication/all-payments")
async def get_all_payments(current_user: dict = Depends(get_current_user)):
    """Get all payments for admin view"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    payments = await db.communication_payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return payments


# ==================== NOTES ====================
@router.get("/communication/notes/{com_code}")
async def get_com_notes(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get notes for a communication manager"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    notes = await db.communication_notes.find({"com_code": code}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notes


@router.post("/communication/notes")
async def create_com_note(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a note"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    com_code = data.get("com_code", "").upper()
    
    note = {
        "id": str(uuid4()),
        "com_code": com_code,
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.communication_notes.insert_one(note)
    return {"message": "Note créée", "id": note['id']}


@router.delete("/communication/notes/{note_id}")
async def delete_com_note(note_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a note"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.communication_notes.delete_one({"id": note_id})
    return {"message": "Note supprimée"}


# ==================== LEAVES/CONGÉS ====================
@router.get("/communication/leaves/{com_code}")
async def get_com_leaves(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get leave requests for a communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    leaves = await db.communication_leaves.find({"com_code": code}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return leaves


@router.post("/communication/leaves")
async def create_com_leave(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a leave request"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    com_code = data.get("com_code", "").upper()
    
    leave = {
        "id": str(uuid4()),
        "com_code": com_code,
        "start_date": data.get("start_date", ""),
        "end_date": data.get("end_date", ""),
        "reason": data.get("reason", ""),
        "status": "pending",  # pending, approved, rejected
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.communication_leaves.insert_one(leave)
    logger.info(f"Leave request created by {com_code}")
    return {"message": "Demande de congé envoyée", "id": leave['id']}


@router.put("/communication/leaves/{leave_id}/status")
async def update_leave_status(leave_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update leave request status (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.communication_leaves.update_one(
        {"id": leave_id},
        {"$set": {"status": data.get("status", "approved"), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave not found")
    
    return {"message": "Statut mis à jour"}


@router.get("/communication/all-leaves")
async def get_all_leaves(current_user: dict = Depends(get_current_user)):
    """Get all leave requests for admin view"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    leaves = await db.communication_leaves.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return leaves


# ==================== INTERNAL MESSAGES ====================
@router.get("/communication/messages/{com_code}")
async def get_com_messages(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get messages for a communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    
    messages = await db.internal_messages.find(
        {"$or": [
            {"sender_code": code},
            {"recipient_code": code}
        ]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return messages


@router.post("/communication/messages")
async def send_internal_message(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Send an internal message"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    message = {
        "id": str(uuid4()),
        "sender_code": data.get("sender_code", "").upper(),
        "sender_name": data.get("sender_name", ""),
        "sender_email": current_user['email'],
        "recipient_code": data.get("recipient_code", "").upper(),
        "content": data.get("content", ""),
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.internal_messages.insert_one(message)
    logger.info(f"Message sent from {message['sender_code']} to {message['recipient_code']}")
    
    return {"message": "Message envoyé", "id": message['id']}


@router.put("/communication/messages/{message_id}/read")
async def mark_message_read(message_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a message as read"""
    await db.internal_messages.update_one({"id": message_id}, {"$set": {"is_read": True}})
    return {"message": "Message marqué comme lu"}


@router.get("/communication/unread-count/{com_code}")
async def get_unread_count(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get unread message count"""
    code = com_code.upper()
    
    count = await db.internal_messages.count_documents({
        "recipient_code": code,
        "is_read": False,
        "sender_code": {"$ne": code}
    })
    
    return {"unread_count": count}
