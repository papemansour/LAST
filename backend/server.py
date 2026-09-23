"""
MyKalamaEnglish API - Main Server
Slim orchestrator: creates app, includes route modules, handles startup/shutdown.
"""
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
import os
import mimetypes
import logging

from config import db, logger, hash_password, client
from models.schemas import User
from websocket_manager import ws_manager

# Route modules
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.secretary import router as secretary_router
from routes.teacher import router as teacher_router
from routes.student import router as student_router
from routes.club import router as club_router
from routes.news import router as news_router
from routes.notifications import router as notifications_router
from routes.misc import router as misc_router
from routes.prestataire import router as prestataire_router
from routes.communication import router as communication_router
from routes.kalamai import router as kalamai_router

app = FastAPI()

# ==================== API ROUTER ====================
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(secretary_router)
api_router.include_router(teacher_router)
api_router.include_router(student_router)
api_router.include_router(club_router)
api_router.include_router(news_router)
api_router.include_router(notifications_router)
api_router.include_router(misc_router)
api_router.include_router(prestataire_router)
api_router.include_router(communication_router)
api_router.include_router(kalamai_router)

# Root API endpoint
@api_router.get("/")
async def api_root():
    return {"message": "KALAMAENGLISH API"}

app.include_router(api_router)

# ==================== UPLOADS DIRECTORY ====================
uploads_base_path = Path("/app/uploads")
uploads_base_path.mkdir(parents=True, exist_ok=True)
(uploads_base_path / "documents").mkdir(exist_ok=True)
(uploads_base_path / "messages").mkdir(exist_ok=True)

# ==================== STATIC FILE SERVING ====================
@app.get("/uploads/{file_path:path}")
async def serve_uploaded_file(file_path: str):
    """Serve uploaded files from persistent storage with proper headers for iframe embedding."""
    file_full_path = Path("/app/uploads") / file_path

    try:
        file_full_path.resolve().relative_to(Path("/app/uploads").resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access forbidden")

    if not file_full_path.exists() or not file_full_path.is_file():
        logger.warning(f"File not found: {file_full_path}")
        raise HTTPException(status_code=404, detail="File not found")

    mime_type, _ = mimetypes.guess_type(str(file_full_path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    logger.info(f"Serving file: {file_path} ({mime_type})")

    with open(file_full_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{file_full_path.name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=3600"
        }
    )

# ==================== CORS MIDDLEWARE ====================
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== STARTUP / SHUTDOWN ====================
@app.on_event("startup")
async def create_admin():
    admin_email = "admin@mykalamaenglish.com"
    existing_admin = await db.users.find_one({"email": admin_email}, {"_id": 0})

    if not existing_admin:
        admin = User(
            email=admin_email,
            first_name="Admin",
            last_name="KALAMA",
            phone="",
            role="admin",
            is_active=True,
            password_hash=hash_password("adminco")
        )
        doc = admin.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logger.info("Admin user created")

    existing_badges = await db.badges.count_documents({})
    if existing_badges == 0:
        default_badges = [
            {"id": str(uuid4()), "name": "Debutant", "icon": "rocket", "description": "Premiere connexion", "condition_type": "first_login", "condition_value": 1, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid4()), "name": "Etudiant Assidu", "icon": "book", "description": "5 cours completes", "condition_type": "courses_completed", "condition_value": 5, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid4()), "name": "Expert", "icon": "star", "description": "10 cours completes", "condition_type": "courses_completed", "condition_value": 10, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid4()), "name": "Champion", "icon": "trophy", "description": "Niveau complete", "condition_type": "level_completed", "condition_value": 1, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.badges.insert_many(default_badges)
        logger.info("Default badges created")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# ==================== HEALTH CHECKS ====================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mykalamaenglish-backend"}


@app.get("/readiness")
async def readiness_check():
    try:
        await db.command('ping')
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}


@app.get("/")
async def root():
    return {"message": "MyKalamaEnglish API", "version": "2.0", "status": "running"}

# ==================== WEBSOCKET ====================
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: str):
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)


@app.get("/api/ws/online-status")
async def get_online_status():
    return {"online_users": ws_manager.get_online_users_count()}
