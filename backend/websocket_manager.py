"""
WebSocket Manager for Real-time Notifications
Handles real-time push notifications for Q/R messages between students and teachers
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_notification(self, user_id: str, notification: dict):
        """Send notification to a specific user"""
        if user_id in self.active_connections:
            message = json.dumps(notification)
            dead_connections = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                    logger.info(f"Notification sent to user {user_id}: {notification.get('type')}")
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for dead in dead_connections:
                self.active_connections[user_id].discard(dead)
    
    async def broadcast_to_users(self, user_ids: list, notification: dict):
        """Send notification to multiple users"""
        for user_id in user_ids:
            await self.send_personal_notification(user_id, notification)
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has active WebSocket connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_online_users_count(self) -> int:
        """Get count of online users"""
        return len(self.active_connections)

# Global connection manager instance
ws_manager = ConnectionManager()
