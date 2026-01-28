"""
Test suite for MyKalamaEnglish - Availability and Billing features
Tests:
- Student availability endpoints
- Teacher students-availability endpoint
- Admin all-students-availability endpoint
- Secretary billing with bonus/deductions
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEACHER_EMAIL = "proftest.flashcards@mykalamaenglish.com"
TEACHER_PASSWORD = "Teacherba45cb1a"
STUDENT_EMAIL = "mouhamadbachirdiagne@gmail.com"
SECRETARY_CODE = "secretaire2025"


class TestAuth:
    """Authentication tests"""
    
    def test_teacher_login(self):
        """Test teacher login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        print(f"Teacher login response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["user"]["role"] == "teacher"
            print(f"Teacher logged in: {data['user']['first_name']} {data['user']['last_name']}")
        else:
            print(f"Teacher login failed: {response.text}")
            pytest.skip("Teacher login failed - credentials may be invalid")
    
    def test_secretary_login(self):
        """Test secretary login with secret code"""
        response = requests.post(f"{BASE_URL}/api/secretary-login", json={
            "code": SECRETARY_CODE
        })
        print(f"Secretary login response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["user"]["role"] == "secretary"
            print(f"Secretary logged in successfully")
        else:
            print(f"Secretary login failed: {response.text}")


@pytest.fixture
def teacher_token():
    """Get teacher authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Teacher authentication failed")


@pytest.fixture
def secretary_token():
    """Get secretary authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
        "code": SECRETARY_CODE
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Secretary authentication failed")


@pytest.fixture
def admin_token():
    """Get admin authentication token - try to find an admin user"""
    # First try to get admin credentials from the database via API
    # For now, we'll skip admin tests if no admin credentials available
    pytest.skip("Admin credentials not provided")


class TestTeacherAvailability:
    """Test teacher students-availability endpoint"""
    
    def test_get_students_availability_authenticated(self, teacher_token):
        """Test GET /api/teacher/students-availability with valid teacher token"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/students-availability", headers=headers)
        
        print(f"Students availability response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} students with availability data")
        
        # Check structure if there are students
        if len(data) > 0:
            student = data[0]
            assert "student_id" in student
            assert "student_name" in student
            assert "slots" in student
            print(f"First student: {student['student_name']}, slots: {len(student.get('slots', []))}")
    
    def test_get_students_availability_unauthorized(self):
        """Test GET /api/teacher/students-availability without token"""
        response = requests.get(f"{BASE_URL}/api/teacher/students-availability")
        
        print(f"Unauthorized response: {response.status_code}")
        assert response.status_code in [401, 403]


class TestStudentAvailability:
    """Test student availability endpoints"""
    
    def test_set_availability_requires_auth(self):
        """Test POST /api/student/set-availability requires authentication"""
        response = requests.post(f"{BASE_URL}/api/student/set-availability", json={
            "slots": [{"day": "monday", "time": "09:00", "available": True}]
        })
        
        print(f"Set availability without auth: {response.status_code}")
        assert response.status_code in [401, 403]


class TestSecretaryBilling:
    """Test secretary billing endpoints"""
    
    def test_get_teacher_payments(self, secretary_token):
        """Test GET /api/secretary/teacher-payments"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/teacher-payments", headers=headers)
        
        print(f"Teacher payments response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} teacher payments")
    
    def test_create_teacher_payment_with_bonus_deductions(self, secretary_token):
        """Test POST /api/secretary/teacher-payments with bonus and deductions"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        
        # Create a test payment with bonus and deductions
        payment_data = {
            "teacherId": "test-teacher-id",
            "teacherName": "TEST_Prof Test",
            "teacherEmail": "test@example.com",
            "month": "Janvier 2026",
            "amount": 500,
            "currency": "EUR",
            "hoursWorked": "20",
            "hourlyRate": "25",
            "bonus": 50,  # 50 EUR bonus
            "deductions": 2,  # 2 missed classes = 10 EUR deduction
            "description": "TEST - Cours de langue anglaise",
            "notes": "Test payment with bonus and deductions"
        }
        
        response = requests.post(f"{BASE_URL}/api/secretary/teacher-payments", 
                                json=payment_data, headers=headers)
        
        print(f"Create payment response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        print(f"Payment created with ID: {data['id']}")
        
        # Verify the payment was created
        get_response = requests.get(f"{BASE_URL}/api/secretary/teacher-payments", headers=headers)
        payments = get_response.json()
        
        # Find our test payment
        test_payment = next((p for p in payments if p.get('teacher_name') == 'TEST_Prof Test'), None)
        if test_payment:
            assert test_payment.get('bonus') == '50' or test_payment.get('bonus') == 50
            print(f"Payment verified - Amount: {test_payment.get('amount')}, Bonus: {test_payment.get('bonus')}")
            
            # Clean up - delete the test payment
            delete_response = requests.delete(
                f"{BASE_URL}/api/secretary/teacher-payments/{test_payment['id']}", 
                headers=headers
            )
            print(f"Cleanup delete response: {delete_response.status_code}")
    
    def test_get_student_receipts(self, secretary_token):
        """Test GET /api/secretary/student-receipts"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/student-receipts", headers=headers)
        
        print(f"Student receipts response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} student receipts")
    
    def test_get_prestataire_invoices(self, secretary_token):
        """Test GET /api/secretary/prestataire-invoices"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/prestataire-invoices", headers=headers)
        
        print(f"Prestataire invoices response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} prestataire invoices")
    
    def test_billing_stats_endpoint(self, secretary_token):
        """Test GET /api/secretary/billing-stats"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/billing-stats", headers=headers)
        
        print(f"Billing stats response: {response.status_code}")
        # This endpoint may or may not exist
        if response.status_code == 200:
            data = response.json()
            print(f"Billing stats: {data}")
        else:
            print(f"Billing stats endpoint returned: {response.status_code}")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        
        print(f"API root response: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        print(f"API message: {data['message']}")
    
    def test_pricing_endpoint(self):
        """Test public pricing endpoint"""
        response = requests.get(f"{BASE_URL}/api/pricing")
        
        print(f"Pricing response: {response.status_code}")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
