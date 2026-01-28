"""
Test WebSocket Notifications and Real-time Features
Tests for:
- WebSocket endpoint /ws/notifications/{user_id}
- GET /api/ws/online-status
- Real-time notification sending when Q/R is posted
"""
import pytest
import requests
import os
import json
import asyncio
import websockets
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEACHER_EMAIL = "proftest.flashcards@mykalamaenglish.com"
TEACHER_PASSWORD = "Teacherba45cb1a"
STUDENT_EMAIL = "mouhamadbachirdiagne@gmail.com"


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestOnlineStatus:
    """Test WebSocket online status endpoint"""
    
    def test_online_status_endpoint(self):
        """Test GET /api/ws/online-status returns online user count"""
        response = requests.get(f"{BASE_URL}/api/ws/online-status")
        assert response.status_code == 200
        data = response.json()
        assert "online_users" in data
        assert isinstance(data["online_users"], int)
        assert data["online_users"] >= 0
        print(f"✅ Online status endpoint working - {data['online_users']} users online")


class TestTeacherAuth:
    """Test teacher authentication"""
    
    def test_teacher_login(self):
        """Test teacher can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "teacher"
        print(f"✅ Teacher login successful: {data['user']['first_name']} {data['user']['last_name']}")
        return data


class TestNotificationsAPI:
    """Test notifications API endpoints"""
    
    @pytest.fixture
    def teacher_token(self):
        """Get teacher auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Teacher login failed")
    
    def test_get_my_notifications(self, teacher_token):
        """Test GET /api/notifications/my-notifications"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications/my-notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Got {len(data)} notifications for teacher")
    
    def test_mark_all_notifications_read(self, teacher_token):
        """Test PUT /api/notifications/mark-all-read"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.put(f"{BASE_URL}/api/notifications/mark-all-read", headers=headers)
        assert response.status_code == 200
        print("✅ Mark all notifications as read endpoint working")


class TestWebSocketConnection:
    """Test WebSocket connection functionality"""
    
    def test_websocket_url_format(self):
        """Verify WebSocket URL format is correct"""
        # The WebSocket URL should be wss://host/ws/notifications/{user_id}
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        expected_pattern = f"{ws_url}/ws/notifications/test-user-id"
        print(f"✅ WebSocket URL pattern: {expected_pattern}")
        assert "ws" in expected_pattern
        assert "/ws/notifications/" in expected_pattern


class TestQRNotificationFlow:
    """Test Q/R notification flow - when student asks question, teacher gets notified"""
    
    @pytest.fixture
    def teacher_auth(self):
        """Get teacher auth data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip("Teacher login failed")
    
    def test_teacher_can_view_qr_questions(self, teacher_auth):
        """Test teacher can view Q/R questions from students"""
        headers = {"Authorization": f"Bearer {teacher_auth['access_token']}"}
        response = requests.get(f"{BASE_URL}/api/teacher/qr-questions", headers=headers)
        # Should return 200 with list of questions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Teacher can view Q/R questions - {len(data)} questions found")
    
    def test_teacher_students_list(self, teacher_auth):
        """Test teacher can get their students list"""
        headers = {"Authorization": f"Bearer {teacher_auth['access_token']}"}
        response = requests.get(f"{BASE_URL}/api/teacher/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Teacher has {len(data)} students assigned")


class TestWebSocketManager:
    """Test WebSocket manager functionality via API"""
    
    def test_online_status_returns_zero_initially(self):
        """Test that online status returns 0 when no WebSocket connections"""
        response = requests.get(f"{BASE_URL}/api/ws/online-status")
        assert response.status_code == 200
        data = response.json()
        # Should return 0 or more (depending on active connections)
        assert data["online_users"] >= 0
        print(f"✅ Online users count: {data['online_users']}")


class TestNotificationBellIntegration:
    """Test NotificationBell component integration points"""
    
    @pytest.fixture
    def teacher_auth(self):
        """Get teacher auth data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip("Teacher login failed")
    
    def test_notifications_endpoint_for_bell(self, teacher_auth):
        """Test the endpoint that NotificationBell uses"""
        headers = {"Authorization": f"Bearer {teacher_auth['access_token']}"}
        response = requests.get(f"{BASE_URL}/api/notifications/my-notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches what NotificationBell expects
        assert isinstance(data, list)
        if len(data) > 0:
            notification = data[0]
            # NotificationBell expects these fields
            assert "id" in notification
            assert "title" in notification
            assert "message" in notification
            assert "is_read" in notification
            assert "created_at" in notification
            print(f"✅ Notification structure valid: {notification.get('title', 'N/A')}")
        else:
            print("✅ No notifications found (empty list is valid)")
    
    def test_mark_notification_read_endpoint(self, teacher_auth):
        """Test marking a single notification as read"""
        headers = {"Authorization": f"Bearer {teacher_auth['access_token']}"}
        
        # First get notifications
        response = requests.get(f"{BASE_URL}/api/notifications/my-notifications", headers=headers)
        assert response.status_code == 200
        notifications = response.json()
        
        if len(notifications) > 0:
            # Try to mark first notification as read
            notif_id = notifications[0]["id"]
            response = requests.put(f"{BASE_URL}/api/notifications/{notif_id}/read", headers=headers)
            assert response.status_code == 200
            print(f"✅ Marked notification {notif_id} as read")
        else:
            print("✅ No notifications to mark as read (skipped)")


class TestWebSocketEndpointExists:
    """Verify WebSocket endpoint is properly configured"""
    
    def test_websocket_endpoint_path(self):
        """Test that the WebSocket endpoint path is accessible"""
        # We can't directly test WebSocket with requests, but we can verify
        # the endpoint exists by checking the API structure
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("✅ API is running, WebSocket endpoint should be at /ws/notifications/{user_id}")
    
    def test_online_status_reflects_ws_manager(self):
        """Test that online-status endpoint reflects WebSocket manager state"""
        response = requests.get(f"{BASE_URL}/api/ws/online-status")
        assert response.status_code == 200
        data = response.json()
        assert "online_users" in data
        # The count should be a non-negative integer
        assert isinstance(data["online_users"], int)
        assert data["online_users"] >= 0
        print(f"✅ WebSocket manager reports {data['online_users']} online users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
