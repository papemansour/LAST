"""
Test suite for Meet Links feature
- Teacher sends Google Meet links to students
- Students receive and view their meet links
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
TEACHER_EMAIL = "proftest.flashcards@mykalamaenglish.com"
TEACHER_PASSWORD = "Teacherba45cb1a"
STUDENT_EMAIL = "mouhamadbachirdiagne@gmail.com"
STUDENT_PASSWORD = "Kalama12d751"


class TestMeetLinksAPI:
    """Test Meet Links endpoints"""
    
    @pytest.fixture(scope="class")
    def teacher_token(self):
        """Get teacher authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def student_token(self):
        """Get student authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def student_id(self, student_token):
        """Get student ID from /auth/me"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_teacher_login_success(self):
        """Test teacher can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✅ Teacher login successful: {data['user']['first_name']} {data['user']['last_name']}")
    
    def test_student_login_success(self):
        """Test student can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        print(f"✅ Student login successful: {data['user']['first_name']} {data['user']['last_name']}")
    
    def test_teacher_send_meet_link(self, teacher_token, student_id):
        """Test teacher can send a meet link to student"""
        # Create a scheduled date for tomorrow
        scheduled_date = (datetime.now() + timedelta(days=1)).isoformat()
        
        payload = {
            "student_id": student_id,
            "meet_link": "https://meet.google.com/test-abc-xyz",
            "title": "TEST - Cours d'anglais - Grammaire",
            "scheduled_date": scheduled_date
        }
        
        response = requests.post(
            f"{BASE_URL}/api/teacher/send-meet-link",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200, f"Send meet link failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "meet_link_id" in data
        print(f"✅ Meet link sent successfully: {data['meet_link_id']}")
        return data["meet_link_id"]
    
    def test_teacher_send_meet_link_requires_auth(self):
        """Test that sending meet link requires authentication"""
        payload = {
            "student_id": "some-id",
            "meet_link": "https://meet.google.com/test",
            "title": "Test",
            "scheduled_date": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/api/teacher/send-meet-link",
            json=payload
        )
        
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ Send meet link correctly requires authentication")
    
    def test_student_cannot_send_meet_link(self, student_token, student_id):
        """Test that students cannot send meet links"""
        payload = {
            "student_id": student_id,
            "meet_link": "https://meet.google.com/test",
            "title": "Test",
            "scheduled_date": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/api/teacher/send-meet-link",
            json=payload,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403, "Students should not be able to send meet links"
        print("✅ Students correctly cannot send meet links")
    
    def test_student_get_my_meet_links(self, student_token):
        """Test student can retrieve their meet links"""
        response = requests.get(
            f"{BASE_URL}/api/student/my-meet-links",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200, f"Get meet links failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check structure of meet links
        if len(data) > 0:
            link = data[0]
            assert "id" in link
            assert "meet_link" in link
            assert "title" in link
            assert "scheduled_date" in link
            assert "teacher_id" in link
            print(f"✅ Student has {len(data)} meet links")
            print(f"   First link: {link.get('title')} - {link.get('meet_link')}")
        else:
            print("✅ Student meet links endpoint works (no links yet)")
        
        return data
    
    def test_student_get_meet_links_requires_auth(self):
        """Test that getting meet links requires authentication"""
        response = requests.get(f"{BASE_URL}/api/student/my-meet-links")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ Get meet links correctly requires authentication")
    
    def test_teacher_cannot_get_student_meet_links(self, teacher_token):
        """Test that teachers cannot access student meet links endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/student/my-meet-links",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 403, "Teachers should not access student endpoint"
        print("✅ Teachers correctly cannot access student meet links endpoint")
    
    def test_full_flow_teacher_sends_student_receives(self, teacher_token, student_token, student_id):
        """Test complete flow: teacher sends link, student receives it"""
        # 1. Teacher sends a new meet link
        scheduled_date = (datetime.now() + timedelta(days=2)).isoformat()
        unique_title = f"TEST_FLOW - Cours {datetime.now().strftime('%H%M%S')}"
        
        send_response = requests.post(
            f"{BASE_URL}/api/teacher/send-meet-link",
            json={
                "student_id": student_id,
                "meet_link": "https://meet.google.com/flow-test-123",
                "title": unique_title,
                "scheduled_date": scheduled_date
            },
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert send_response.status_code == 200, f"Send failed: {send_response.text}"
        meet_link_id = send_response.json()["meet_link_id"]
        print(f"✅ Step 1: Teacher sent meet link with ID: {meet_link_id}")
        
        # 2. Student retrieves their links
        get_response = requests.get(
            f"{BASE_URL}/api/student/my-meet-links",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert get_response.status_code == 200
        links = get_response.json()
        
        # 3. Verify the new link is in the list
        found_link = next((l for l in links if l.get("id") == meet_link_id), None)
        assert found_link is not None, f"New link not found in student's links"
        assert found_link["title"] == unique_title
        assert found_link["meet_link"] == "https://meet.google.com/flow-test-123"
        
        print(f"✅ Step 2: Student received the link: {found_link['title']}")
        print(f"✅ Full flow test PASSED!")


class TestMeetLinksValidation:
    """Test validation for meet links"""
    
    @pytest.fixture(scope="class")
    def teacher_token(self):
        """Get teacher authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Teacher login failed")
        return response.json()["access_token"]
    
    def test_send_meet_link_missing_fields(self, teacher_token):
        """Test that missing required fields return error"""
        # Missing student_id
        response = requests.post(
            f"{BASE_URL}/api/teacher/send-meet-link",
            json={
                "meet_link": "https://meet.google.com/test",
                "title": "Test",
                "scheduled_date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 422, "Should fail with missing student_id"
        print("✅ Validation correctly rejects missing student_id")
    
    def test_send_meet_link_invalid_date(self, teacher_token):
        """Test that invalid date format is rejected"""
        response = requests.post(
            f"{BASE_URL}/api/teacher/send-meet-link",
            json={
                "student_id": "some-id",
                "meet_link": "https://meet.google.com/test",
                "title": "Test",
                "scheduled_date": "invalid-date"
            },
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # Should fail with 422 or 500 due to invalid date
        assert response.status_code in [422, 500], "Should fail with invalid date"
        print("✅ Validation correctly rejects invalid date format")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
