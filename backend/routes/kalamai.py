"""
Kalamai - AI English Tutor powered by OpenAI
Conversational AI assistant available 24/7 for English learning
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4
import os
import logging
import json
import asyncio

from emergentintegrations.llm.chat import LlmChat, UserMessage
from config import db, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Load API key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Kalamai system prompt - English tutor personality
KALAMAI_SYSTEM_PROMPT = """Tu es Kalamai, un tuteur d'anglais intelligent et bienveillant de MyKalama English School.

Ton rôle:
- Aider les étudiants à améliorer leur anglais de manière conversationnelle
- Adapter ton niveau de langue au niveau de l'étudiant (débutant, intermédiaire, avancé, K-Kid pour les enfants)
- Corriger les erreurs grammaticales avec tact et pédagogie
- Proposer des exercices interactifs et des jeux de vocabulaire
- Encourager et motiver les étudiants dans leur apprentissage
- Répondre en anglais par défaut, mais tu peux utiliser le français pour les explications si nécessaire

Personnalité:
- Patient et encourageant
- Utilise des exemples concrets et ludiques
- Célèbre les progrès des étudiants
- Pose des questions pour engager la conversation
- Utilise des emojis occasionnellement pour rendre les échanges plus vivants

Niveaux:
- K-Kid: Enfants 4-10 ans - vocabulaire simple, jeux, chansons
- Beginner: Débutants - bases de grammaire, phrases simples
- Intermediate: Intermédiaires - conversations, temps verbaux complexes
- Advanced: Avancés - idiomes, nuances, discussions approfondies

Tu es disponible 24h/24, 7j/7 pour aider les étudiants de MyKalama!"""


@router.post("/kalamai/chat")
async def kalamai_chat(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Chat with Kalamai AI tutor - Streaming response"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    message = data.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    session_id = data.get("session_id") or f"kalamai_{current_user['id']}_{datetime.now().strftime('%Y%m%d')}"
    user_level = current_user.get("level", "intermediate")
    
    # Customize system message based on user level
    level_context = {
        "kkid": "L'étudiant est un enfant (K-Kid). Utilise un langage simple, ludique et encourageant.",
        "beginner": "L'étudiant est débutant. Utilise des phrases simples et des explications claires.",
        "intermediate": "L'étudiant est de niveau intermédiaire. Tu peux avoir des conversations plus complexes.",
        "advanced": "L'étudiant est de niveau avancé. Utilise des expressions idiomatiques et un vocabulaire riche."
    }
    
    system_message = f"{KALAMAI_SYSTEM_PROMPT}\n\nContexte actuel: {level_context.get(user_level, level_context['intermediate'])}"
    
    # Get chat history from database
    history = await db.kalamai_conversations.find_one(
        {"user_id": current_user['id'], "session_id": session_id},
        {"_id": 0}
    )
    
    messages_history = history.get("messages", []) if history else []
    
    # Build context from history (last 6 messages for context)
    context_messages = messages_history[-6:] if messages_history else []
    
    async def generate():
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-5.4")
            
            # Add history context
            for msg in context_messages:
                if msg["role"] == "user":
                    chat.add_user_message(msg["content"])
                else:
                    chat.add_assistant_message(msg["content"])
            
            user_message = UserMessage(text=message)
            
            # Get response (async call)
            full_response = await chat.send_message(user_message)
            
            # Simulate streaming by sending chunks
            words = full_response.split(' ')
            for i in range(0, len(words), 3):  # Send 3 words at a time
                chunk = ' '.join(words[i:i+3]) + ' '
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.03)  # Small delay for streaming effect
            
            # Save conversation to database
            new_messages = [
                {"role": "user", "content": message, "timestamp": datetime.now(timezone.utc).isoformat()},
                {"role": "assistant", "content": full_response, "timestamp": datetime.now(timezone.utc).isoformat()}
            ]
            
            await db.kalamai_conversations.update_one(
                {"user_id": current_user['id'], "session_id": session_id},
                {
                    "$push": {"messages": {"$each": new_messages}},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                    "$setOnInsert": {
                        "id": str(uuid4()),
                        "user_id": current_user['id'],
                        "session_id": session_id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
            
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Kalamai chat error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/kalamai/history")
async def get_kalamai_history(
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get chat history with Kalamai"""
    query = {"user_id": current_user['id']}
    if session_id:
        query["session_id"] = session_id
    
    conversations = await db.kalamai_conversations.find(
        query,
        {"_id": 0}
    ).sort("updated_at", -1).limit(10).to_list(length=10)
    
    return conversations


@router.get("/kalamai/sessions")
async def get_kalamai_sessions(current_user: dict = Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    sessions = await db.kalamai_conversations.find(
        {"user_id": current_user['id']},
        {"_id": 0, "session_id": 1, "created_at": 1, "updated_at": 1}
    ).sort("updated_at", -1).limit(20).to_list(length=20)
    
    return sessions


@router.delete("/kalamai/session/{session_id}")
async def delete_kalamai_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a chat session"""
    result = await db.kalamai_conversations.delete_one({
        "user_id": current_user['id'],
        "session_id": session_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session supprimée"}


@router.post("/kalamai/new-session")
async def create_new_session(current_user: dict = Depends(get_current_user)):
    """Create a new chat session"""
    session_id = f"kalamai_{current_user['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return {"session_id": session_id}
