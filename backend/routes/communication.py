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
    total_testimonials = await db.testimonials.count_documents({})
    
    return {
        "totalStudents": total_students,
        "totalTeachers": total_teachers,
        "totalNews": total_news,
        "totalTestimonials": total_testimonials
    }


# ==================== TESTIMONIALS ====================
@router.get("/communication/testimonials")
async def get_testimonials(current_user: dict = Depends(get_current_user)):
    """Get all testimonials"""
    if current_user['role'] not in ['admin', 'communication', 'secretary']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    testimonials = await db.testimonials.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return testimonials


@router.post("/communication/testimonials")
async def create_testimonial(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new testimonial"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    testimonial = {
        "id": str(uuid4()),
        "name": data.get("name", ""),
        "role": data.get("role", ""),
        "content": data.get("content", ""),
        "rating": data.get("rating", 5),
        "image_url": data.get("image_url", ""),
        "is_active": True,
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.testimonials.insert_one(testimonial)
    logger.info(f"Testimonial created by {current_user['email']}: {testimonial['name']}")
    
    return {"message": "Testimonial created", "id": testimonial['id']}


@router.delete("/communication/testimonials/{testimonial_id}")
async def delete_testimonial(testimonial_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a testimonial"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.testimonials.delete_one({"id": testimonial_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    
    logger.info(f"Testimonial {testimonial_id} deleted by {current_user['email']}")
    return {"message": "Testimonial deleted"}


# ==================== SOCIAL POSTS ====================
@router.get("/communication/social-posts")
async def get_social_posts(current_user: dict = Depends(get_current_user)):
    """Get all social media posts"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    posts = await db.social_posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return posts


@router.post("/communication/social-posts")
async def create_social_post(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new social media post"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    post = {
        "id": str(uuid4()),
        "platform": data.get("platform", "facebook"),
        "content": data.get("content", ""),
        "image_url": data.get("image_url", ""),
        "scheduled_date": data.get("scheduled_date", ""),
        "status": data.get("status", "draft"),  # draft, scheduled, published
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.social_posts.insert_one(post)
    logger.info(f"Social post created by {current_user['email']}: {post['platform']}")
    
    return {"message": "Social post created", "id": post['id']}


@router.put("/communication/social-posts/{post_id}")
async def update_social_post(post_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update a social media post"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {
        "platform": data.get("platform"),
        "content": data.get("content"),
        "scheduled_date": data.get("scheduled_date"),
        "status": data.get("status"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    result = await db.social_posts.update_one(
        {"id": post_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": "Post updated"}


@router.delete("/communication/social-posts/{post_id}")
async def delete_social_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a social media post"""
    if current_user['role'] not in ['admin', 'communication']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.social_posts.delete_one({"id": post_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    logger.info(f"Social post {post_id} deleted by {current_user['email']}")
    return {"message": "Post deleted"}


# ==================== PUBLIC TESTIMONIALS (for homepage) ====================
@router.get("/public/testimonials")
async def get_public_testimonials():
    """Get active testimonials for public display"""
    testimonials = await db.testimonials.find(
        {"is_active": True},
        {"_id": 0, "created_by": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    return testimonials
