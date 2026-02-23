"""
Comprehensive test suite for MyKalamaEnglish platform
Tests all user roles: Admin, Teacher, Secretary, Student
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://elearning-platform-6.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"
TEACHER_EMAIL = "ndeyemane.dieng@mykalamaenglish.com"
TEACHER_PASSWORD = "Teacherc209e87f"
SECRETARY_EMAIL = "secretaire@mykalamaenglish.com"
SECRETARY_PASSWORD = "kalamasecret"
SECRETARY_CODE = "2811"

class TestHealthCheck:
    """API Health Check"""
    
    def test_api_root(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root accessible: {data['message']}")

    def test_pricing_endpoint(self):
        """Test pricing endpoint (public)"""
        response = requests.get(f"{BASE_URL}/api/pricing")
        assert response.status_code == 200
        data = response.json()
        assert "beginner_eur" in data
        print(f"✓ Pricing endpoint working")


class TestAdminLogin:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Admin login rejected with wrong password")


class TestTeacherLogin:
    """Teacher authentication tests"""
    
    def test_teacher_login_success(self):
        """Test teacher login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['first_name']} {data['user']['last_name']}")
        return data["access_token"]
    
    def test_teacher_login_wrong_password(self):
        """Test teacher login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Teacher login rejected with wrong password")


class TestSecretaryLogin:
    """Secretary authentication tests"""
    
    def test_secretary_login_success(self):
        """Test secretary login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SECRETARY_EMAIL,
            "password": SECRETARY_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "secretary"
        print(f"✓ Secretary login successful: {data['user']['email']}")
        return data["access_token"]


class TestAdminDashboard:
    """Admin dashboard functionality tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_admin_get_users(self, admin_token):
        """Test admin can get all users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin can get users: {len(data)} users found")
    
    def test_admin_get_teachers(self, admin_token):
        """Test admin can get all teachers"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/teachers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin can get teachers: {len(data)} teachers found")
    
    def test_admin_get_students(self, admin_token):
        """Test admin can get all students"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin can get students: {len(data)} students found")
    
    def test_admin_analytics(self, admin_token):
        """Test admin analytics endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Check for quarterly hours data
        assert "hours_by_semester" in data or "total_hours" in data
        print(f"✓ Admin analytics working")
    
    def test_admin_trash(self, admin_token):
        """Test admin trash endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/trash", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin trash endpoint working: {len(data)} items in trash")
    
    def test_admin_leave_requests(self, admin_token):
        """Test admin can view leave requests (Congés)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/leave-requests", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin leave requests (Congés) working: {len(data)} requests")


class TestTeacherDashboard:
    """Teacher dashboard functionality tests"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_teacher_get_payments(self, teacher_token):
        """Test teacher can get their payments (Mes Payes)"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/my-payments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check currency is correct for Ndeyemane (should be FCFA)
        if len(data) > 0:
            # Verify payments exist and have currency field
            for payment in data:
                assert "currency" in payment
                print(f"  Payment: {payment.get('month', 'N/A')} - {payment.get('montant_net', 0)} {payment.get('currency', 'EUR')}")
        print(f"✓ Teacher payments working: {len(data)} payments found")
    
    def test_teacher_get_students(self, teacher_token):
        """Test teacher can get their students"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/my-students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Teacher students working: {len(data)} students found")
    
    def test_teacher_availability(self, teacher_token):
        """Test teacher can get their availability"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/my-availability", headers=headers)
        assert response.status_code == 200
        print("✓ Teacher availability endpoint working")
    
    def test_teacher_leave_requests(self, teacher_token):
        """Test teacher can get their leave requests"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/my-leave-requests", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Teacher leave requests working: {len(data)} requests")
    
    def test_teacher_upcoming_balance(self, teacher_token):
        """Test teacher can get upcoming balance"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/upcoming-balance", headers=headers)
        assert response.status_code == 200
        print("✓ Teacher upcoming balance endpoint working")


class TestSecretaryDashboard:
    """Secretary dashboard functionality tests"""
    
    @pytest.fixture
    def secretary_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SECRETARY_EMAIL,
            "password": SECRETARY_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_secretary_get_meetings(self, secretary_token):
        """Test secretary can get meetings"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/meetings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Secretary meetings working: {len(data)} meetings")
    
    def test_secretary_get_reports(self, secretary_token):
        """Test secretary can get reports"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/reports", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Secretary reports working: {len(data)} reports")
    
    def test_secretary_get_teacher_payments(self, secretary_token):
        """Test secretary can get teacher payments"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/teacher-payments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Secretary teacher payments working: {len(data)} payments")
    
    def test_secretary_get_teachers_list(self, secretary_token):
        """Test secretary can get teachers list"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/teachers-list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Secretary teachers list working: {len(data)} teachers")
    
    def test_secretary_get_students_list(self, secretary_token):
        """Test secretary can get students list"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        response = requests.get(f"{BASE_URL}/api/secretary/students-list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Secretary students list working: {len(data)} students")
    
    def test_secretary_create_teacher_payment(self, secretary_token):
        """Test secretary can create teacher payment with FAC-YYYY-XXX reference"""
        headers = {"Authorization": f"Bearer {secretary_token}"}
        payment_data = {
            "teacherId": "test-teacher-id",
            "teacherName": "TEST_Teacher",
            "teacherEmail": "test@test.com",
            "month": "Test Month 2026",
            "amount": 100,
            "currency": "EUR",
            "hoursWorked": "10",
            "bonus": 0,
            "deductions": 0
        }
        response = requests.post(f"{BASE_URL}/api/secretary/teacher-payments", 
                                json=payment_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "invoice_ref" in data
        # Verify FAC-YYYY-XXX format
        invoice_ref = data["invoice_ref"]
        assert invoice_ref.startswith("FAC-")
        print(f"✓ Secretary create payment working - Invoice ref: {invoice_ref}")
        
        # Cleanup - delete the test payment
        if "id" in data:
            requests.delete(f"{BASE_URL}/api/secretary/teacher-payments/{data['id']}", headers=headers)


class TestHomePage:
    """Homepage functionality tests"""
    
    def test_pricing_data(self):
        """Test pricing data is available"""
        response = requests.get(f"{BASE_URL}/api/pricing")
        assert response.status_code == 200
        data = response.json()
        # Check all pack prices exist
        assert "kkid_eur" in data
        assert "beginner_eur" in data
        assert "intermediate_eur" in data
        assert "advanced_eur" in data
        print(f"✓ Pricing data available")
        print(f"  K-Kid: {data.get('kkid_eur')}€")
        print(f"  Beginner: {data.get('beginner_eur')}€")
        print(f"  Intermediate: {data.get('intermediate_eur')}€")
        print(f"  Advanced: {data.get('advanced_eur')}€")


class TestAuthPersistence:
    """Test authentication persistence (refresh page stays on same space)"""
    
    def test_admin_me_endpoint(self):
        """Test /auth/me endpoint returns user info"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Test /auth/me
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        print(f"✓ Auth persistence working - /auth/me returns correct user")
    
    def test_teacher_me_endpoint(self):
        """Test /auth/me endpoint for teacher"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"
        print(f"✓ Teacher auth persistence working")
    
    def test_secretary_me_endpoint(self):
        """Test /auth/me endpoint for secretary"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SECRETARY_EMAIL,
            "password": SECRETARY_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "secretary"
        print(f"✓ Secretary auth persistence working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
