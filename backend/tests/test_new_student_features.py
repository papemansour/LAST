"""
Test suite for MyKalamaEnglish new features:
1. Student receipt viewing (Paye tab)
2. Intermediate test questions (20 MCQ)
3. Backend refactoring verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-tracker-698.preview.emergentagent.com')

# Test credentials from review request
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"
TEACHER_EMAIL = "proftest.flashcards@mykalamaenglish.com"
TEACHER_PASSWORD = "Teacherba45cb1a"
SECRETARY_CODE = "secretaire2025"
SECRETARY_EMAIL = "secretaire@mykalamaenglish.com"
SECRETARY_PASSWORD = "kalamasecret"
STUDENT_EMAIL = "mouhamadbachirdiagne@gmail.com"
STUDENT_PASSWORD = "Student123test"


class TestIntermediateTestQuestions:
    """Test the intermediate test questions endpoint - 20 MCQ questions"""
    
    def test_intermediate_test_returns_20_questions(self):
        """Test /api/tests/intermediate returns 20 MCQ questions"""
        response = requests.get(f"{BASE_URL}/api/tests/intermediate")
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "level" in data
        assert data["level"] == "intermediate"
        
        questions = data["questions"]
        assert len(questions) == 20, f"Expected 20 questions, got {len(questions)}"
        
        # Verify question structure
        for q in questions:
            assert "id" in q
            assert "question" in q
            assert "options" in q
            assert isinstance(q["options"], list)
            assert len(q["options"]) >= 2, "Each question should have at least 2 options"
        
        print(f"✓ Intermediate test: {len(questions)} MCQ questions returned")
        print(f"  Sample question: {questions[0]['question'][:50]}...")
    
    def test_intermediate_questions_have_correct_answers(self):
        """Verify intermediate questions have proper answer options"""
        response = requests.get(f"{BASE_URL}/api/tests/intermediate")
        assert response.status_code == 200
        data = response.json()
        
        questions = data["questions"]
        
        # Check that all questions have 4 options (standard MCQ)
        for q in questions:
            assert len(q["options"]) == 4, f"Question '{q['question'][:30]}...' should have 4 options"
        
        print(f"✓ All {len(questions)} intermediate questions have 4 options each")


class TestBeginnerTestQuestions:
    """Test the beginner test questions endpoint - 20 MCQ questions"""
    
    def test_beginner_test_returns_20_questions(self):
        """Test /api/tests/beginner returns 20 MCQ questions"""
        response = requests.get(f"{BASE_URL}/api/tests/beginner")
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "level" in data
        assert data["level"] == "beginner"
        
        questions = data["questions"]
        assert len(questions) == 20, f"Expected 20 questions, got {len(questions)}"
        
        print(f"✓ Beginner test: {len(questions)} MCQ questions returned")


class TestStudentReceiptViewing:
    """Test student receipt viewing feature (Paye tab)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get student token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.user = response.json()["user"]
        else:
            pytest.skip("Student login failed")
    
    def test_student_my_receipts_endpoint(self):
        """Test GET /api/student/my-receipts returns receipts for logged-in student"""
        response = requests.get(f"{BASE_URL}/api/student/my-receipts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Student my-receipts: {len(data)} receipts found")
        
        # Verify receipt structure if any exist
        if len(data) > 0:
            receipt = data[0]
            assert "id" in receipt
            assert "student_id" in receipt
            assert "student_name" in receipt
            assert "amount" in receipt
            assert "currency" in receipt
            assert "created_at" in receipt
            
            # Verify receipt belongs to logged-in student
            assert receipt["student_id"] == self.user["id"], "Receipt should belong to logged-in student"
            
            print(f"  Receipt: {receipt['pack_name']} - {receipt['amount']} {receipt['currency']}")
    
    def test_student_receipts_requires_auth(self):
        """Test /api/student/my-receipts requires authentication"""
        response = requests.get(f"{BASE_URL}/api/student/my-receipts")
        assert response.status_code in [401, 403]
        print("✓ Student receipts endpoint correctly requires auth")
    
    def test_student_receipts_only_returns_own_receipts(self):
        """Verify student only sees their own receipts"""
        response = requests.get(f"{BASE_URL}/api/student/my-receipts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # All receipts should belong to the logged-in student
        for receipt in data:
            assert receipt["student_id"] == self.user["id"], "Student should only see their own receipts"
        
        print(f"✓ All {len(data)} receipts belong to logged-in student")


class TestSecretaryStudentReceipts:
    """Test secretary student receipt creation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get secretary token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": SECRETARY_CODE
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Secretary login failed")
    
    def test_secretary_get_student_receipts(self):
        """Test GET /api/secretary/student-receipts returns all receipts"""
        response = requests.get(f"{BASE_URL}/api/secretary/student-receipts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Secretary student-receipts: {len(data)} receipts found")
    
    def test_secretary_create_student_receipt(self):
        """Test POST /api/secretary/student-receipts creates receipt with correct fields"""
        # Get student ID first
        student_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        student_id = student_response.json()["user"]["id"]
        
        receipt_data = {
            "student_id": student_id,
            "student_name": "TEST_Student Receipt Test",
            "pack_name": "TEST_Pack Test",
            "amount": 100,
            "currency": "EUR",
            "payment_method": "Virement",
            "notes": "Test receipt for automated testing",
            "email": STUDENT_EMAIL
        }
        
        response = requests.post(
            f"{BASE_URL}/api/secretary/student-receipts",
            headers=self.headers,
            json=receipt_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "message" in data
        print(f"✓ Secretary created student receipt: {data['id']}")
        
        # Verify receipt was created with correct fields
        receipts_response = requests.get(f"{BASE_URL}/api/secretary/student-receipts", headers=self.headers)
        receipts = receipts_response.json()
        
        created_receipt = next((r for r in receipts if r["id"] == data["id"]), None)
        assert created_receipt is not None, "Created receipt should be in list"
        assert created_receipt["student_id"] == student_id, "student_id should be stored"
        assert created_receipt["student_name"] == "TEST_Student Receipt Test", "student_name should be stored"
        assert created_receipt["pack_name"] == "TEST_Pack Test", "pack_name should be stored"
        
        print(f"✓ Receipt fields verified: student_id={created_receipt['student_id']}, pack_name={created_receipt['pack_name']}")
        
        # Cleanup - delete test receipt
        delete_response = requests.delete(
            f"{BASE_URL}/api/secretary/student-receipts/{data['id']}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        print(f"✓ Test receipt cleaned up")


class TestAdminEndpoints:
    """Test admin dashboard endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed")
    
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
    
    def test_admin_analytics(self):
        """Test /api/admin/analytics returns analytics data"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        summary = data["summary"]
        assert "total_students" in summary
        assert "total_teachers" in summary
        
        print(f"✓ Admin analytics: {summary['total_students']} students, {summary['total_teachers']} teachers")


class TestTeacherEndpoints:
    """Test teacher login and endpoints"""
    
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
        print(f"✓ Teacher login successful: {data['user']['email']}")


class TestSecretaryLogin:
    """Test secretary login with code"""
    
    def test_secretary_login_with_code(self):
        """Test secretary login with secret code secretaire2025"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": SECRETARY_CODE
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["role"] == "secretary"
        print(f"✓ Secretary login with code successful: {data['user']['email']}")
    
    def test_secretary_login_wrong_code(self):
        """Test secretary login with wrong code"""
        response = requests.post(f"{BASE_URL}/api/auth/secretary-login", json={
            "code": "wrongcode"
        })
        assert response.status_code == 401
        print("✓ Secretary login with wrong code correctly rejected")


class TestPricingEndpoint:
    """Test public pricing endpoint"""
    
    def test_pricing_endpoint(self):
        """Test /api/pricing returns pricing data"""
        response = requests.get(f"{BASE_URL}/api/pricing")
        assert response.status_code == 200
        data = response.json()
        
        # Check pricing structure
        assert "beginner_eur" in data
        assert "intermediate_eur" in data
        assert "advanced_eur" in data
        assert "kkid_eur" in data
        
        print(f"✓ Pricing endpoint working")
        print(f"  Beginner: {data['beginner_eur']} EUR")
        print(f"  Intermediate: {data['intermediate_eur']} EUR")
        print(f"  Advanced: {data['advanced_eur']} EUR")


class TestBackendRefactoring:
    """Test that backend refactoring didn't break existing endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root: {data}")
    
    def test_api_health_check(self):
        """Test API is responding correctly"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API health check: {data}")
    
    def test_badges_endpoint(self):
        """Test public badges endpoint"""
        response = requests.get(f"{BASE_URL}/api/badges")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Badges endpoint: {len(data)} badges found")
    
    def test_news_endpoint(self):
        """Test public news endpoint"""
        response = requests.get(f"{BASE_URL}/api/news")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ News endpoint: {len(data)} news items found")
    
    def test_club_posts_endpoint(self):
        """Test public club posts endpoint"""
        response = requests.get(f"{BASE_URL}/api/club/posts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Club posts endpoint: {len(data)} posts found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
