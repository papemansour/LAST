"""Communication routes for the communication manager role."""
from fastapi import APIRouter, HTTPException, Depends, Body
from config import db, logger, get_current_user
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter()

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


# ==================== AVAILABILITY ====================
@router.get("/communication/availability/{com_code}")
async def get_availability(com_code: str, current_user: dict = Depends(get_current_user)):
    """Get availability for a specific communication manager"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate com_code
    if com_code.upper() not in ['MBM', 'FZT']:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    availability = await db.communication_availability.find(
        {"com_code": com_code.upper()},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    
    return availability


@router.post("/communication/availability")
async def create_availability(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new availability entry"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    com_code = data.get("com_code", "").upper()
    if com_code not in ['MBM', 'FZT']:
        raise HTTPException(status_code=400, detail="Invalid communication code")
    
    # Check if already exists for this date
    existing = await db.communication_availability.find_one({
        "com_code": com_code,
        "date": data.get("date")
    })
    
    if existing:
        # Update existing
        await db.communication_availability.update_one(
            {"id": existing['id']},
            {"$set": {
                "start_time": data.get("start_time", "09:00"),
                "end_time": data.get("end_time", "17:00"),
                "status": data.get("status", "available"),
                "note": data.get("note", ""),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Availability updated for {com_code} on {data.get('date')}")
        return {"message": "Availability updated", "id": existing['id']}
    
    availability_entry = {
        "id": str(uuid4()),
        "com_code": com_code,
        "date": data.get("date", ""),
        "start_time": data.get("start_time", "09:00"),
        "end_time": data.get("end_time", "17:00"),
        "status": data.get("status", "available"),  # available, busy, tentative
        "note": data.get("note", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.communication_availability.insert_one(availability_entry)
    logger.info(f"Availability created for {com_code} on {data.get('date')}: {data.get('status')}")
    
    return {"message": "Availability created", "id": availability_entry['id']}


@router.delete("/communication/availability/{availability_id}")
async def delete_availability(availability_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an availability entry"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.communication_availability.delete_one({"id": availability_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    logger.info(f"Availability {availability_id} deleted by {current_user['email']}")
    return {"message": "Availability deleted"}


# ==================== ALL AVAILABILITY (for admin view) ====================
@router.get("/communication/availability-all")
async def get_all_availability(current_user: dict = Depends(get_current_user)):
    """Get availability for all communication managers (admin view)"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    availability = await db.communication_availability.find(
        {},
        {"_id": 0}
    ).sort("date", 1).to_list(200)
    
    return availability
