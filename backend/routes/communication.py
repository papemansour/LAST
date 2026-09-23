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
    
    # availability format: { "monday": ["09:00", "10:00", "14:00"], "tuesday": [...], ... }
    availability_entry = {
        "id": str(uuid4()),
        "com_code": com_code,
        "availability": data.get('availability', {}),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Replace existing availability for this code
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
    
    availability = await db.communication_availability.find_one(
        {"com_code": code},
        {"_id": 0}
    )
    
    return availability or {"availability": {}, "com_code": code}


@router.get("/communication/all-availability")
async def get_all_com_availability(current_user: dict = Depends(get_current_user)):
    """Get availability for all communication managers (admin/secretary view)"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    availabilities = await db.communication_availability.find(
        {},
        {"_id": 0}
    ).to_list(10)
    
    # Ensure both codes have entries
    result = []
    codes_found = [a['com_code'] for a in availabilities]
    
    for code in VALID_COM_CODES:
        if code in codes_found:
            result.append(next(a for a in availabilities if a['com_code'] == code))
        else:
            result.append({"com_code": code, "availability": {}})
    
    return result


# ==================== PAYSLIPS (Fiches de paie) ====================
@router.get("/communication/payslips/{com_code}")
async def get_com_payslips(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get payslips for a communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    if code not in VALID_COM_CODES:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    payslips = await db.communication_payslips.find(
        {"com_code": code},
        {"_id": 0}
    ).sort("date", -1).to_list(50)
    
    return payslips


@router.post("/communication/payslips")
async def create_com_payslip(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a payslip for a communication manager (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    com_code = data.get("com_code", "").upper()
    if com_code not in VALID_COM_CODES:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    payslip = {
        "id": str(uuid4()),
        "com_code": com_code,
        "month": data.get("month", ""),
        "year": data.get("year", datetime.now().year),
        "amount": data.get("amount", 0),
        "currency": data.get("currency", "EUR"),
        "status": data.get("status", "pending"),  # pending, paid
        "date": data.get("date", datetime.now(timezone.utc).isoformat()),
        "notes": data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.communication_payslips.insert_one(payslip)
    logger.info(f"Payslip created for {com_code} by {current_user['email']}")
    
    return {"message": "Fiche de paie créée", "id": payslip['id']}


@router.put("/communication/payslips/{payslip_id}/status")
async def update_payslip_status(payslip_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update payslip status"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.communication_payslips.update_one(
        {"id": payslip_id},
        {"$set": {"status": data.get("status", "paid"), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    return {"message": "Statut mis à jour"}


# ==================== INTERNAL MESSAGES ====================
@router.get("/communication/messages/{com_code}")
async def get_com_messages(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get messages for a communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    code = com_code.upper()
    
    # Get messages where this code is sender or recipient
    messages = await db.internal_messages.find(
        {"$or": [
            {"sender_code": code},
            {"recipient_code": code},
            {"recipient_code": "ALL"}  # Broadcast messages
        ]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return messages


@router.post("/communication/messages")
async def send_internal_message(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Send an internal message"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sender_code = data.get("sender_code", "").upper()
    recipient_code = data.get("recipient_code", "").upper()
    
    # Validate codes
    valid_codes = VALID_COM_CODES + ['ADMIN', 'SECRETARY', 'ALL']
    if sender_code not in valid_codes:
        raise HTTPException(status_code=400, detail="Invalid sender code")
    if recipient_code not in valid_codes:
        raise HTTPException(status_code=400, detail="Invalid recipient code")
    
    message = {
        "id": str(uuid4()),
        "sender_code": sender_code,
        "sender_name": data.get("sender_name", ""),
        "sender_email": current_user['email'],
        "recipient_code": recipient_code,
        "content": data.get("content", ""),
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.internal_messages.insert_one(message)
    logger.info(f"Message sent from {sender_code} to {recipient_code}")
    
    return {"message": "Message envoyé", "id": message['id']}


@router.put("/communication/messages/{message_id}/read")
async def mark_message_read(message_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a message as read"""
    await db.internal_messages.update_one(
        {"id": message_id},
        {"$set": {"is_read": True}}
    )
    return {"message": "Message marqué comme lu"}


@router.get("/communication/unread-count/{com_code}")
async def get_unread_count(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get unread message count"""
    code = com_code.upper()
    
    count = await db.internal_messages.count_documents({
        "$or": [
            {"recipient_code": code},
            {"recipient_code": "ALL"}
        ],
        "is_read": False,
        "sender_code": {"$ne": code}  # Don't count own messages
    })
    
    return {"unread_count": count}
