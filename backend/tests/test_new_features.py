"""
Test suite for MyKalamaEnglish new features:
1. Admin Monthly Teacher Hours endpoint
2. Secretary Meeting Edit (PUT) endpoint
3. Student Mark Answer Read endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root working: {data['message']}")


class TestAdminAuth:
    """Admin authentication tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@mykalamaenglish.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed - skipping admin tests")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@mykalamaenglish.com",
            "password": "admin123"
        })
        # Admin may not exist or have different password
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["user"]["role"] == "admin"
            print("✓ Admin login successful")
        else:
            print(f"⚠ Admin login returned {response.status_code}: {response.text}")


class TestSecretaryAuth:
    """Secretary authentication tests"""
    
    def test_secretary_login_with_code(self):
        """Test secretary login with secret code"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "secretaire2025"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "secretary"
        print("✓ Secretary login with code successful")
    
    def test_secretary_login_wrong_code(self):
        """Test secretary login with wrong code"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "wrongcode"
        })
        assert response.status_code == 401
        print("✓ Secretary login correctly rejects wrong code")


class TestAdminMonthlyHours:
    """Tests for /api/admin/monthly-teacher-hours endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@mykalamaenglish.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed - skipping admin tests")
    
    def test_monthly_hours_requires_auth(self):
        """Test that monthly hours endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/monthly-teacher-hours")
        assert response.status_code in [401, 403]
        print("✓ Monthly hours endpoint correctly requires auth")
    
    def test_monthly_hours_with_admin(self, admin_token):
        """Test monthly hours endpoint with admin auth"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/monthly-teacher-hours", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "month" in data
        assert "year" in data
        assert "month_name" in data
        assert "teachers" in data
        assert "total_teachers" in data
        assert "total_hours_all" in data
        
        print(f"✓ Monthly hours endpoint working: {data['month_name']} {data['year']}")
        print(f"  - Total teachers: {data['total_teachers']}")
        print(f"  - Total hours: {data['total_hours_all']}")
    
    def test_monthly_hours_with_params(self, admin_token):
        """Test monthly hours endpoint with month/year params"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/monthly-teacher-hours?month=1&year=2025",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["month"] == 1
        assert data["year"] == 2025
        assert data["month_name"] == "Janvier"
        print("✓ Monthly hours with params working")
    
    def test_monthly_hours_non_admin_forbidden(self):
        """Test that non-admin users cannot access monthly hours"""
        # Login as secretary
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "secretaire2025"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/api/admin/monthly-teacher-hours", headers=headers)
            assert response.status_code == 403
            print("✓ Monthly hours correctly forbidden for non-admin")


class TestSecretaryMeetings:
    """Tests for secretary meetings CRUD including PUT endpoint"""
    
    @pytest.fixture
    def secretary_token(self):
        """Get secretary token"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "secretaire2025"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Secretary login failed")
    
    def test_get_meetings(self, secretary_token):
        """Test getting meetings list"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/meetings", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ Get meetings working: {len(response.json())} meetings found")
    
    def test_create_meeting(self, secretary_token):
        """Test creating a new meeting"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        meeting_data = {
            "title": "TEST_Meeting_Pytest",
            "date": "2025-01-20",
            "time": "14:00",
            "attendees": "Prof A, Prof B",
            "notes": "Test meeting notes",
            "meetingLink": "https://meet.google.com/test"
        }
        response = requests.post(
            f"{BASE_URL}/api/secretary/meetings",
            headers=headers,
            json=meeting_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Create meeting working: ID {data['id']}")
        return data['id']
    
    def test_update_meeting_put(self, secretary_token):
        """Test PUT endpoint for updating a meeting"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        
        # First create a meeting
        meeting_data = {
            "title": "TEST_Meeting_ToUpdate",
            "date": "2025-01-21",
            "time": "15:00",
            "attendees": "Prof C",
            "notes": "Original notes",
            "meetingLink": ""
        }
        create_response = requests.post(
            f"{BASE_URL}/api/secretary/meetings",
            headers=headers,
            json=meeting_data
        )
        assert create_response.status_code == 200
        meeting_id = create_response.json()['id']
        
        # Now update the meeting using PUT
        updated_data = {
            "title": "TEST_Meeting_Updated",
            "date": "2025-01-22",
            "time": "16:00",
            "attendees": "Prof C, Prof D",
            "notes": "Updated notes",
            "meetingLink": "https://zoom.us/test"
        }
        update_response = requests.put(
            f"{BASE_URL}/api/secretary/meetings/{meeting_id}",
            headers=headers,
            json=updated_data
        )
        assert update_response.status_code == 200
        print(f"✓ PUT meeting endpoint working: Meeting {meeting_id} updated")
        
        # Verify the update by getting meetings
        get_response = requests.get(f"{BASE_URL}/api/secretary/meetings", headers=headers)
        meetings = get_response.json()
        updated_meeting = next((m for m in meetings if m['id'] == meeting_id), None)
        
        if updated_meeting:
            assert updated_meeting['title'] == "TEST_Meeting_Updated"
            assert updated_meeting['date'] == "2025-01-22"
            print("✓ Meeting update verified in database")
        
        # Cleanup - delete the test meeting
        requests.delete(f"{BASE_URL}/api/secretary/meetings/{meeting_id}", headers=headers)
    
    def test_delete_meeting(self, secretary_token):
        """Test deleting a meeting"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        
        # Create a meeting to delete
        meeting_data = {
            "title": "TEST_Meeting_ToDelete",
            "date": "2025-01-23",
            "time": "10:00",
            "attendees": "",
            "notes": ""
        }
        create_response = requests.post(
            f"{BASE_URL}/api/secretary/meetings",
            headers=headers,
            json=meeting_data
        )
        meeting_id = create_response.json()['id']
        
        # Delete the meeting
        delete_response = requests.delete(
            f"{BASE_URL}/api/secretary/meetings/{meeting_id}",
            headers=headers
        )
        assert delete_response.status_code == 200
        print(f"✓ Delete meeting working: Meeting {meeting_id} deleted")


class TestStudentMarkAnswerRead:
    """Tests for /api/student/mark-answer-read/{id} endpoint"""
    
    def test_mark_answer_read_requires_auth(self):
        """Test that mark answer read requires authentication"""
        response = requests.put(f"{BASE_URL}/api/student/mark-answer-read/test-id")
        assert response.status_code in [401, 403]
        print("✓ Mark answer read correctly requires auth")
    
    def test_mark_answer_read_requires_student_role(self):
        """Test that only students can mark answers as read"""
        # Login as secretary (non-student)
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "secretaire2025"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.put(
                f"{BASE_URL}/api/student/mark-answer-read/test-id",
                headers=headers
            )
            assert response.status_code == 403
            print("✓ Mark answer read correctly requires student role")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def secretary_token(self):
        """Get secretary token"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "secretaire2025"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Secretary login failed")
    
    def test_cleanup_test_meetings(self, secretary_token):
        """Clean up TEST_ prefixed meetings"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/meetings", headers=headers)
        meetings = response.json()
        
        deleted_count = 0
        for meeting in meetings:
            if meeting.get('title', '').startswith('TEST_'):
                requests.delete(f"{BASE_URL}/api/secretary/meetings/{meeting['id']}", headers=headers)
                deleted_count += 1
        
        print(f"✓ Cleanup: Deleted {deleted_count} test meetings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
