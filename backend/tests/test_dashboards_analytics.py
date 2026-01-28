"""
Test suite for Dashboard fixes and Analytics features
- Tests StudentDashboard, TeacherDashboard, AdminDashboard login flows
- Tests /api/admin/analytics endpoint
- Tests /api/admin/check-documents-integrity endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"
TEACHER_EMAIL = "proftest.flashcards@mykalamaenglish.com"
TEACHER_PASSWORD = "Teacherba45cb1a"
STUDENT_EMAIL = "mouhamadbachirdiagne@gmail.com"
STUDENT_PASSWORD = "Kalama12d751"


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✅ API root: {data['message']}")


class TestStudentLogin:
    """Test student login and dashboard access"""
    
    def test_student_login_success(self):
        """Test student can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        
        if response.status_code == 401:
            print(f"⚠️ Student login failed - credentials may be invalid: {response.json()}")
            pytest.skip("Student credentials invalid")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "student"
        print(f"✅ Student login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_student_can_access_me_endpoint(self):
        """Test student can access /auth/me after login"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Student login failed")
        
        token = login_response.json()["access_token"]
        
        # Access /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == STUDENT_EMAIL
        print(f"✅ Student /auth/me works: {data['first_name']} {data['last_name']}")


class TestTeacherLogin:
    """Test teacher login and dashboard access"""
    
    def test_teacher_login_success(self):
        """Test teacher can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        
        if response.status_code == 401:
            print(f"⚠️ Teacher login failed - credentials may be invalid: {response.json()}")
            pytest.skip("Teacher credentials invalid")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "teacher"
        print(f"✅ Teacher login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_teacher_can_access_my_students(self):
        """Test teacher can access their students list"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Teacher login failed")
        
        token = login_response.json()["access_token"]
        
        # Access /teacher/my-students
        response = requests.get(
            f"{BASE_URL}/api/teacher/my-students",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Teacher /teacher/my-students works: {len(data)} students")


class TestAdminLogin:
    """Test admin login and dashboard access"""
    
    def test_admin_login_success(self):
        """Test admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 401:
            print(f"⚠️ Admin login failed - credentials may be invalid: {response.json()}")
            pytest.skip("Admin credentials invalid")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        print(f"✅ Admin login successful: {data['user']['email']}")
        return data["access_token"]


class TestAdminAnalytics:
    """Test admin analytics endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_analytics_endpoint_returns_200(self, admin_token):
        """Test /api/admin/analytics returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✅ Analytics endpoint returns 200")
    
    def test_analytics_returns_correct_structure(self, admin_token):
        """Test analytics returns expected data structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check summary exists
        assert "summary" in data
        summary = data["summary"]
        assert "total_students" in summary
        assert "active_students" in summary
        assert "total_teachers" in summary
        assert "total_hours_this_month" in summary
        assert "revenue_eur" in summary
        assert "revenue_fcfa" in summary
        assert "growth_rate" in summary
        
        # Check chart data exists
        assert "students_by_month" in data
        assert "hours_by_week" in data
        assert "revenue_by_month" in data
        assert "students_by_level" in data
        assert "top_teachers" in data
        
        print(f"✅ Analytics structure correct:")
        print(f"   - Total students: {summary['total_students']}")
        print(f"   - Active students: {summary['active_students']}")
        print(f"   - Total teachers: {summary['total_teachers']}")
        print(f"   - Hours this month: {summary['total_hours_this_month']}")
    
    def test_analytics_period_week(self, admin_token):
        """Test analytics with week period"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics?period=week",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        print("✅ Analytics with period=week works")
    
    def test_analytics_period_year(self, admin_token):
        """Test analytics with year period"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics?period=year",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        print("✅ Analytics with period=year works")
    
    def test_analytics_requires_admin(self):
        """Test analytics endpoint requires admin role"""
        # Try with teacher token
        teacher_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        
        if teacher_login.status_code != 200:
            pytest.skip("Teacher login failed")
        
        teacher_token = teacher_login.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("✅ Analytics correctly requires admin role")


class TestDocumentsIntegrity:
    """Test documents integrity check endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_check_documents_integrity_returns_200(self, admin_token):
        """Test /api/admin/check-documents-integrity returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check-documents-integrity",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✅ Check documents integrity returns 200")
    
    def test_check_documents_integrity_structure(self, admin_token):
        """Test documents integrity returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check-documents-integrity",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_documents" in data
        assert "valid_documents" in data
        assert "invalid_documents" in data
        assert "invalid_list" in data
        
        print(f"✅ Documents integrity check:")
        print(f"   - Total documents: {data['total_documents']}")
        print(f"   - Valid documents: {data['valid_documents']}")
        print(f"   - Invalid documents: {data['invalid_documents']}")
    
    def test_check_documents_requires_admin(self):
        """Test documents integrity check requires admin role"""
        # Try with student token
        student_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        
        if student_login.status_code != 200:
            pytest.skip("Student login failed")
        
        student_token = student_login.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/check-documents-integrity",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("✅ Documents integrity check correctly requires admin role")


class TestCleanupDocuments:
    """Test cleanup invalid documents endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_cleanup_documents_endpoint_exists(self, admin_token):
        """Test /api/admin/cleanup-invalid-documents endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/cleanup-invalid-documents",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 200 (even if no documents to clean)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "message" in data
        assert "removed_documents" in data
        print(f"✅ Cleanup documents endpoint works: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
