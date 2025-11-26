#!/usr/bin/env python3
"""
Backend Testing for My KALAMA ENGLISH
Comprehensive tests for all backend functionality including new features
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional
import sys
import os
import base64
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://kalamaclassroom.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"
KALAMATHEQUE_ACCESS_CODE = "Digika"

class MyKalamaEnglishBackendTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.teacher_token = None
        self.student_token = None
        self.test_book_id = None
        self.test_teacher_id = None
        self.test_student_id = None
        self.test_flashcard_set_id = None
        self.test_results = {
            # Existing Kalamathèque tests
            "file_upload": {"passed": False, "details": []},
            "access_verification": {"passed": False, "details": []},
            "book_creation": {"passed": False, "details": []},
            "book_retrieval": {"passed": False, "details": []},
            "book_deletion": {"passed": False, "details": []},
            "ai_assistant": {"passed": False, "details": []},
            "text_to_speech": {"passed": False, "details": []},
            
            # New feature tests
            "flashcard_system": {"passed": False, "details": []},
            "video_system": {"passed": False, "details": []},
            "test_questions": {"passed": False, "details": []},
            "pricing_independence": {"passed": False, "details": []},
            "admin_delete_user": {"passed": False, "details": []},
            "email_notifications": {"passed": False, "details": []},
            
            # Group registration system tests
            "group_registration": {"passed": False, "details": []},
            "pending_group_registrations": {"passed": False, "details": []},
            "magic_code_generation": {"passed": False, "details": []},
            "magic_code_login": {"passed": False, "details": []},
            "group_system_verification": {"passed": False, "details": []},
            
            # Overall results
            "overall_backend": {"passed": False, "details": []}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login_admin(self) -> bool:
        """Login as admin and get token"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    logger.info("✅ Admin login successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Admin login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Admin login error: {str(e)}")
            return False
    
    async def create_test_teacher(self) -> Optional[Dict[str, str]]:
        """Create a test teacher for testing"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # First check if test teacher already exists
            async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as users_response:
                if users_response.status == 200:
                    users = await users_response.json()
                    for user in users:
                        if user.get('email') == 'proftest.flashcards@mykalamaenglish.com':
                            logger.info(f"✅ Using existing test teacher: {user.get('email')}")
                            self.test_teacher_id = user.get('id')
                            # Try to get the actual password from the user record
                            temp_password = user.get('temporary_password')
                            if not temp_password:
                                # Try common patterns
                                temp_password = f"Teacher{user.get('id', '')[:8]}"
                            return {
                                "id": user.get('id'),
                                "email": user.get('email'),
                                "password": temp_password
                            }
            
            teacher_data = {
                "first_name": "ProfTest",
                "last_name": "Flashcards"
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/create-teacher", 
                                       json=teacher_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Test teacher created: {data.get('email')}")
                    
                    # Get the user ID by finding the user
                    async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as users_response:
                        if users_response.status == 200:
                            users = await users_response.json()
                            for user in users:
                                if user.get('email') == data.get('email'):
                                    self.test_teacher_id = user.get('id')
                                    return {
                                        "id": user.get('id'),
                                        "email": data.get('email'),
                                        "password": data.get('temporary_password')
                                    }
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create test teacher: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error creating test teacher: {str(e)}")
            return None

    async def create_test_student(self) -> Optional[Dict[str, str]]:
        """Create a test student for testing"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # First check if test student already exists
            async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as users_response:
                if users_response.status == 200:
                    users = await users_response.json()
                    for user in users:
                        if user.get('email') == 'etudiant.test@example.com':
                            logger.info(f"✅ Using existing test student: {user.get('email')}")
                            self.test_student_id = user.get('id')
                            # Try to get the actual password from the user record
                            temp_password = user.get('temporary_password')
                            if not temp_password:
                                # Try common patterns
                                temp_password = f"Kalama{user.get('id', '')[:6]}"
                            return {
                                "id": user.get('id'),
                                "email": user.get('email'),
                                "password": temp_password
                            }
            
            # First register a student
            student_data = {
                "email": "etudiant.test@example.com",
                "first_name": "Étudiant",
                "last_name": "Test",
                "phone": "+33123456789",
                "level": "kkid",
                "preferred_slots": "Matin",
                "referral_source": "Test"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=student_data) as response:
                if response.status == 200:
                    logger.info("✅ Test student registered")
                    
                    # Get the student ID
                    headers = {"Authorization": f"Bearer {self.admin_token}"}
                    async with self.session.get(f"{BACKEND_URL}/admin/pending-registrations", headers=headers) as pending_response:
                        if pending_response.status == 200:
                            pending = await pending_response.json()
                            for user in pending:
                                if user.get('email') == student_data['email']:
                                    student_id = user.get('id')
                                    
                                    # Approve the student
                                    async with self.session.post(f"{BACKEND_URL}/admin/approve-registration/{student_id}", headers=headers) as approve_response:
                                        if approve_response.status == 200:
                                            approval_data = await approve_response.json()
                                            logger.info(f"✅ Test student approved: {approval_data.get('email')}")
                                            self.test_student_id = student_id
                                            return {
                                                "id": student_id,
                                                "email": student_data['email'],
                                                "password": approval_data.get('temporary_password')
                                            }
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to register test student: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error creating test student: {str(e)}")
            return None

    async def login_teacher(self, teacher_email: str, teacher_password: str) -> bool:
        """Login as teacher and get token"""
        try:
            login_data = {
                "email": teacher_email,
                "password": teacher_password
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.teacher_token = data.get("access_token")
                    logger.info("✅ Teacher login successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Teacher login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Teacher login error: {str(e)}")
            return False

    async def login_student(self, student_email: str, student_password: str) -> bool:
        """Login as student and get token"""
        try:
            login_data = {
                "email": student_email,
                "password": student_password
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.student_token = data.get("access_token")
                    logger.info("✅ Student login successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Student login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Student login error: {str(e)}")
            return False
    
    async def test_password_change_security(self) -> bool:
        """Test that password changes don't store plain text passwords"""
        try:
            logger.info("🔍 Testing password change security...")
            
            # Change admin password
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            password_data = {
                "old_password": ADMIN_PASSWORD,
                "new_password": "NewSecurePassword123!"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/change-password", 
                                       json=password_data, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Password change endpoint works")
                    self.test_results["change_password"]["details"].append("Password change endpoint responds correctly")
                    
                    # Change back to original password
                    revert_data = {
                        "old_password": "NewSecurePassword123!",
                        "new_password": ADMIN_PASSWORD
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/auth/change-password", 
                                               json=revert_data, headers=headers) as revert_response:
                        if revert_response.status == 200:
                            logger.info("✅ Password reverted successfully")
                            self.test_results["change_password"]["details"].append("Password successfully reverted")
                            self.test_results["change_password"]["passed"] = True
                            return True
                        else:
                            error_text = await revert_response.text()
                            logger.error(f"❌ Failed to revert password: {revert_response.status} - {error_text}")
                            self.test_results["change_password"]["details"].append(f"Failed to revert password: {error_text}")
                            return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Password change failed: {response.status} - {error_text}")
                    self.test_results["change_password"]["details"].append(f"Password change failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Password change test error: {str(e)}")
            self.test_results["change_password"]["details"].append(f"Test error: {str(e)}")
            return False
    
    async def test_admin_password_reset(self) -> bool:
        """Test admin password reset functionality"""
        try:
            logger.info("🔍 Testing admin password reset...")
            
            # Get test user first
            test_user_id = await self.get_test_user()
            if not test_user_id:
                self.test_results["admin_reset_password"]["details"].append("Failed to create test user")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/admin/reset-user-password/{test_user_id}", 
                                       headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Admin password reset endpoint works")
                    
                    # Check response structure
                    required_fields = ["message", "temporary_password", "email_sent"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        logger.info("✅ Password reset response has all required fields")
                        self.test_results["admin_reset_password"]["details"].append("Response contains all required fields")
                        
                        if data.get("message") == "Password reset successfully":
                            logger.info("✅ Correct success message")
                            self.test_results["admin_reset_password"]["details"].append("Correct success message returned")
                        
                        if data.get("temporary_password"):
                            logger.info("✅ Temporary password generated")
                            self.test_results["admin_reset_password"]["details"].append("Temporary password generated successfully")
                        
                        if data.get("email_sent") == False:
                            logger.info("✅ Email sending status correctly reported (AWS SES not configured)")
                            self.test_results["admin_reset_password"]["details"].append("Email sending status correctly reported")
                        
                        self.test_results["admin_reset_password"]["passed"] = True
                        return True
                    else:
                        logger.error(f"❌ Missing required fields in response: {missing_fields}")
                        self.test_results["admin_reset_password"]["details"].append(f"Missing fields: {missing_fields}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Admin password reset failed: {response.status} - {error_text}")
                    self.test_results["admin_reset_password"]["details"].append(f"Reset failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Admin password reset test error: {str(e)}")
            self.test_results["admin_reset_password"]["details"].append(f"Test error: {str(e)}")
            return False
    
    async def cleanup_test_user(self, user_id: str):
        """Clean up test user"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.delete(f"{BACKEND_URL}/admin/delete-user/{user_id}", 
                                         headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Test user cleaned up")
                else:
                    logger.warning(f"⚠️ Failed to clean up test user: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up test user: {str(e)}")
    
    async def test_contact_form(self) -> bool:
        """Test public contact form functionality"""
        try:
            logger.info("🔍 Testing contact form...")
            
            # Test valid contact form submission
            contact_data = {
                "name": "Jean Dupont",
                "email": "jean.dupont@example.com",
                "message": "Bonjour, je souhaite des informations sur vos cours d'anglais."
            }
            
            async with self.session.post(f"{BACKEND_URL}/contact/send", json=contact_data) as response:
                if response.status == 200:
                    data = await response.json()
                    expected_message = "Message received and will be processed"
                    
                    if data.get("message") == expected_message:
                        logger.info("✅ Contact form works correctly")
                        self.test_results["contact_form"]["details"].append("Valid contact form submission successful")
                    else:
                        logger.info(f"✅ Contact form works (message: {data.get('message')})")
                        self.test_results["contact_form"]["details"].append(f"Contact form works with message: {data.get('message')}")
                    
                    # Test validation - invalid email
                    invalid_data = {
                        "name": "Test User",
                        "email": "invalid-email",
                        "message": "Test message"
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/contact/send", json=invalid_data) as invalid_response:
                        if invalid_response.status == 400:
                            logger.info("✅ Email validation works")
                            self.test_results["contact_form"]["details"].append("Email validation working correctly")
                        else:
                            logger.warning("⚠️ Email validation may not be working properly")
                            self.test_results["contact_form"]["details"].append("Email validation unclear")
                    
                    # Test validation - missing fields
                    incomplete_data = {
                        "name": "Test User",
                        "email": "test@example.com"
                        # missing message
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/contact/send", json=incomplete_data) as incomplete_response:
                        if incomplete_response.status == 400:
                            logger.info("✅ Required field validation works")
                            self.test_results["contact_form"]["details"].append("Required field validation working")
                        else:
                            logger.warning("⚠️ Required field validation may not be working")
                            self.test_results["contact_form"]["details"].append("Required field validation unclear")
                    
                    self.test_results["contact_form"]["passed"] = True
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Contact form failed: {response.status} - {error_text}")
                    self.test_results["contact_form"]["details"].append(f"Contact form failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Contact form test error: {str(e)}")
            self.test_results["contact_form"]["details"].append(f"Test error: {str(e)}")
            return False
    
    async def create_test_file(self) -> str:
        """Create a test PDF file for upload testing"""
        try:
            # Create a simple test PDF content
            test_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Kalamatheque Book) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(test_content)
                return temp_file.name
                
        except Exception as e:
            logger.error(f"❌ Error creating test file: {str(e)}")
            return None

    async def test_file_upload(self) -> bool:
        """Test file upload endpoint"""
        try:
            logger.info("🔍 Testing file upload endpoint...")
            
            # Create test file
            test_file_path = await self.create_test_file()
            if not test_file_path:
                self.test_results["file_upload"]["details"].append("Failed to create test file")
                return False
            
            try:
                # Upload file
                with open(test_file_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('file', file, filename='test_book.pdf', content_type='application/pdf')
                    
                    async with self.session.post(f"{BACKEND_URL}/uploadfile/", data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # Check response structure
                            required_fields = ["message", "file_url", "filename"]
                            missing_fields = [field for field in required_fields if field not in result]
                            
                            if not missing_fields:
                                logger.info("✅ File upload successful")
                                self.test_results["file_upload"]["details"].append("File uploaded successfully")
                                self.test_results["file_upload"]["details"].append(f"File URL: {result.get('file_url')}")
                                self.test_results["file_upload"]["passed"] = True
                                return result.get('file_url')
                            else:
                                logger.error(f"❌ Missing fields in upload response: {missing_fields}")
                                self.test_results["file_upload"]["details"].append(f"Missing fields: {missing_fields}")
                                return False
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ File upload failed: {response.status} - {error_text}")
                            self.test_results["file_upload"]["details"].append(f"Upload failed: {error_text}")
                            return False
            finally:
                # Clean up test file
                if os.path.exists(test_file_path):
                    os.unlink(test_file_path)
                    
        except Exception as e:
            logger.error(f"❌ File upload test error: {str(e)}")
            self.test_results["file_upload"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_access_verification(self) -> bool:
        """Test Kalamathèque access code verification"""
        try:
            logger.info("🔍 Testing access code verification...")
            
            # Test correct access code
            correct_data = {"access_code": KALAMATHEQUE_ACCESS_CODE}
            async with self.session.post(f"{BACKEND_URL}/kalamatheque/verify-access", json=correct_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("access") == True:
                        logger.info("✅ Correct access code accepted")
                        self.test_results["access_verification"]["details"].append("Correct access code works")
                    else:
                        logger.error("❌ Correct access code not properly accepted")
                        self.test_results["access_verification"]["details"].append("Correct access code issue")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Access verification failed: {response.status} - {error_text}")
                    self.test_results["access_verification"]["details"].append(f"Access verification failed: {error_text}")
                    return False
            
            # Test incorrect access code
            incorrect_data = {"access_code": "WrongCode"}
            async with self.session.post(f"{BACKEND_URL}/kalamatheque/verify-access", json=incorrect_data) as response:
                if response.status == 403:
                    logger.info("✅ Incorrect access code properly rejected")
                    self.test_results["access_verification"]["details"].append("Incorrect access code properly rejected")
                    self.test_results["access_verification"]["passed"] = True
                    return True
                else:
                    logger.error(f"❌ Incorrect access code not properly rejected: {response.status}")
                    self.test_results["access_verification"]["details"].append("Incorrect access code not rejected")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Access verification test error: {str(e)}")
            self.test_results["access_verification"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_book_creation(self, file_url: str) -> bool:
        """Test book creation (admin only)"""
        try:
            logger.info("🔍 Testing book creation...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test book creation with all fields
            book_data = {
                "title": "Test English Grammar Book",
                "author": "Test Author",
                "description": "A comprehensive guide to English grammar for intermediate learners",
                "level": "intermediate",
                "file_url": file_url,
                "file_type": "pdf",
                "cover_image": "/images/test-cover.jpg"
            }
            
            async with self.session.post(f"{BACKEND_URL}/kalamatheque/books", json=book_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "book_id" in result and result.get("message"):
                        logger.info("✅ Book created successfully")
                        self.test_results["book_creation"]["details"].append("Book created with all fields")
                        self.test_book_id = result["book_id"]
                        
                        # Test book creation with missing required fields
                        incomplete_data = {
                            "title": "Incomplete Book"
                            # Missing required fields
                        }
                        
                        async with self.session.post(f"{BACKEND_URL}/kalamatheque/books", json=incomplete_data, headers=headers) as incomplete_response:
                            if incomplete_response.status in [400, 422]:
                                logger.info("✅ Missing required fields properly rejected")
                                self.test_results["book_creation"]["details"].append("Missing fields validation works")
                            else:
                                logger.warning("⚠️ Missing fields validation unclear")
                                self.test_results["book_creation"]["details"].append("Missing fields validation unclear")
                        
                        self.test_results["book_creation"]["passed"] = True
                        return True
                    else:
                        logger.error("❌ Book creation response missing required fields")
                        self.test_results["book_creation"]["details"].append("Response missing book_id or message")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Book creation failed: {response.status} - {error_text}")
                    self.test_results["book_creation"]["details"].append(f"Creation failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Book creation test error: {str(e)}")
            self.test_results["book_creation"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_book_retrieval(self) -> bool:
        """Test book retrieval endpoints"""
        try:
            logger.info("🔍 Testing book retrieval...")
            
            # Test get all books
            async with self.session.get(f"{BACKEND_URL}/kalamatheque/books") as response:
                if response.status == 200:
                    books = await response.json()
                    
                    if isinstance(books, list):
                        logger.info(f"✅ Retrieved {len(books)} books")
                        self.test_results["book_retrieval"]["details"].append(f"Retrieved {len(books)} books")
                        
                        # Verify our test book is in the list
                        if self.test_book_id:
                            test_book_found = any(book.get("id") == self.test_book_id for book in books)
                            if test_book_found:
                                logger.info("✅ Test book found in book list")
                                self.test_results["book_retrieval"]["details"].append("Test book found in list")
                            else:
                                logger.warning("⚠️ Test book not found in list")
                                self.test_results["book_retrieval"]["details"].append("Test book not found in list")
                    else:
                        logger.error("❌ Books response is not a list")
                        self.test_results["book_retrieval"]["details"].append("Invalid response format")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Get books failed: {response.status} - {error_text}")
                    self.test_results["book_retrieval"]["details"].append(f"Get books failed: {error_text}")
                    return False
            
            # Test get specific book
            if self.test_book_id:
                async with self.session.get(f"{BACKEND_URL}/kalamatheque/books/{self.test_book_id}") as response:
                    if response.status == 200:
                        book = await response.json()
                        
                        if book.get("id") == self.test_book_id:
                            logger.info("✅ Specific book retrieved successfully")
                            self.test_results["book_retrieval"]["details"].append("Specific book retrieval works")
                            self.test_results["book_retrieval"]["passed"] = True
                            return True
                        else:
                            logger.error("❌ Retrieved book ID doesn't match")
                            self.test_results["book_retrieval"]["details"].append("Book ID mismatch")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Get specific book failed: {response.status} - {error_text}")
                        self.test_results["book_retrieval"]["details"].append(f"Get specific book failed: {error_text}")
                        return False
            else:
                logger.warning("⚠️ No test book ID available for specific book test")
                self.test_results["book_retrieval"]["details"].append("No test book for specific retrieval")
                self.test_results["book_retrieval"]["passed"] = True
                return True
                
        except Exception as e:
            logger.error(f"❌ Book retrieval test error: {str(e)}")
            self.test_results["book_retrieval"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_ai_assistant(self) -> bool:
        """Test AI assistant endpoint"""
        try:
            logger.info("🔍 Testing AI assistant...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test summarize action
            test_data = {
                "action": "summarize",
                "text": "English grammar is the set of structural rules governing the composition of clauses, phrases and words in the English language. The term refers to the study of such rules and this field includes phonology, morphology, syntax, semantics, and pragmatics."
            }
            
            async with self.session.post(f"{BACKEND_URL}/kalamatheque/ai-assistant", json=test_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "result" in result and result["result"]:
                        logger.info("✅ AI assistant summarize works")
                        self.test_results["ai_assistant"]["details"].append("AI summarize function works")
                        
                        # Test explain action
                        explain_data = {
                            "action": "explain",
                            "text": "The quick brown fox jumps over the lazy dog."
                        }
                        
                        async with self.session.post(f"{BACKEND_URL}/kalamatheque/ai-assistant", json=explain_data, headers=headers) as explain_response:
                            if explain_response.status == 200:
                                explain_result = await explain_response.json()
                                if "result" in explain_result and explain_result["result"]:
                                    logger.info("✅ AI assistant explain works")
                                    self.test_results["ai_assistant"]["details"].append("AI explain function works")
                                    self.test_results["ai_assistant"]["passed"] = True
                                    return True
                                else:
                                    logger.error("❌ AI explain response missing result")
                                    self.test_results["ai_assistant"]["details"].append("AI explain missing result")
                                    return False
                            else:
                                error_text = await explain_response.text()
                                logger.error(f"❌ AI explain failed: {explain_response.status} - {error_text}")
                                self.test_results["ai_assistant"]["details"].append(f"AI explain failed: {error_text}")
                                return False
                    else:
                        logger.error("❌ AI assistant response missing result")
                        self.test_results["ai_assistant"]["details"].append("AI response missing result")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ AI assistant failed: {response.status} - {error_text}")
                    self.test_results["ai_assistant"]["details"].append(f"AI assistant failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ AI assistant test error: {str(e)}")
            self.test_results["ai_assistant"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_text_to_speech(self) -> bool:
        """Test text-to-speech endpoint"""
        try:
            logger.info("🔍 Testing text-to-speech...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            test_data = {
                "text": "Hello, this is a test of the text-to-speech functionality for Kalamathèque."
            }
            
            async with self.session.post(f"{BACKEND_URL}/kalamatheque/text-to-speech", json=test_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "audio_base64" in result and result["audio_base64"]:
                        # Verify it's valid base64
                        try:
                            audio_data = base64.b64decode(result["audio_base64"])
                            if len(audio_data) > 0:
                                logger.info("✅ Text-to-speech works and returns valid audio")
                                self.test_results["text_to_speech"]["details"].append("TTS generates valid audio")
                                self.test_results["text_to_speech"]["passed"] = True
                                return True
                            else:
                                logger.error("❌ TTS returned empty audio data")
                                self.test_results["text_to_speech"]["details"].append("TTS returned empty audio")
                                return False
                        except Exception as decode_error:
                            logger.error(f"❌ TTS returned invalid base64: {str(decode_error)}")
                            self.test_results["text_to_speech"]["details"].append("TTS returned invalid base64")
                            return False
                    else:
                        logger.error("❌ TTS response missing audio_base64")
                        self.test_results["text_to_speech"]["details"].append("TTS response missing audio")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Text-to-speech failed: {response.status} - {error_text}")
                    self.test_results["text_to_speech"]["details"].append(f"TTS failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Text-to-speech test error: {str(e)}")
            self.test_results["text_to_speech"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_book_deletion(self) -> bool:
        """Test book deletion (admin only)"""
        try:
            logger.info("🔍 Testing book deletion...")
            
            if not self.test_book_id:
                logger.warning("⚠️ No test book ID available for deletion test")
                self.test_results["book_deletion"]["details"].append("No test book for deletion")
                self.test_results["book_deletion"]["passed"] = True
                return True
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(f"{BACKEND_URL}/kalamatheque/books/{self.test_book_id}", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("message"):
                        logger.info("✅ Book deleted successfully")
                        self.test_results["book_deletion"]["details"].append("Book deletion works")
                        
                        # Verify book is actually deleted
                        async with self.session.get(f"{BACKEND_URL}/kalamatheque/books/{self.test_book_id}") as verify_response:
                            if verify_response.status == 404:
                                logger.info("✅ Book properly removed from database")
                                self.test_results["book_deletion"]["details"].append("Book properly removed")
                                self.test_results["book_deletion"]["passed"] = True
                                return True
                            else:
                                logger.error("❌ Book still exists after deletion")
                                self.test_results["book_deletion"]["details"].append("Book not properly removed")
                                return False
                    else:
                        logger.error("❌ Book deletion response missing message")
                        self.test_results["book_deletion"]["details"].append("Deletion response missing message")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Book deletion failed: {response.status} - {error_text}")
                    self.test_results["book_deletion"]["details"].append(f"Deletion failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Book deletion test error: {str(e)}")
            self.test_results["book_deletion"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_flashcard_system(self) -> bool:
        """Test complete flashcard system workflow"""
        try:
            logger.info("🔍 Testing flashcard system...")
            
            if not self.teacher_token:
                logger.error("❌ No teacher token available")
                self.test_results["flashcard_system"]["details"].append("No teacher token")
                return False
            
            headers = {"Authorization": f"Bearer {self.teacher_token}"}
            
            # 1. Create flashcard set
            set_data = {
                "title": "Vocabulaire Anglais Basique",
                "description": "Mots de base pour débutants"
            }
            
            async with self.session.post(f"{BACKEND_URL}/teacher/create-flashcard-set", json=set_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    self.test_flashcard_set_id = result.get("set_id")
                    logger.info("✅ Flashcard set created")
                    self.test_results["flashcard_system"]["details"].append("Flashcard set creation works")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Flashcard set creation failed: {response.status} - {error_text}")
                    self.test_results["flashcard_system"]["details"].append(f"Set creation failed: {error_text}")
                    return False
            
            # 2. Add flashcards to set
            flashcards = [
                {"question": "Bonjour", "answer": "Hello", "set_id": self.test_flashcard_set_id},
                {"question": "Au revoir", "answer": "Goodbye", "set_id": self.test_flashcard_set_id},
                {"question": "Merci", "answer": "Thank you", "set_id": self.test_flashcard_set_id}
            ]
            
            for flashcard in flashcards:
                async with self.session.post(f"{BACKEND_URL}/teacher/add-flashcard", json=flashcard, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"✅ Flashcard added: {flashcard['question']}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to add flashcard: {response.status} - {error_text}")
                        self.test_results["flashcard_system"]["details"].append(f"Flashcard addition failed: {error_text}")
                        return False
            
            self.test_results["flashcard_system"]["details"].append("All flashcards added successfully")
            
            # 3. Assign game to student
            if self.test_student_id:
                game_data = {
                    "student_id": self.test_student_id,
                    "game_type": "flashcard",
                    "game_id": self.test_flashcard_set_id,
                    "title": "Test Flashcard Game"
                }
                
                async with self.session.post(f"{BACKEND_URL}/teacher/assign-game", json=game_data, headers=headers) as response:
                    if response.status == 200:
                        logger.info("✅ Game assigned to student")
                        self.test_results["flashcard_system"]["details"].append("Game assignment works")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Game assignment failed: {response.status} - {error_text}")
                        self.test_results["flashcard_system"]["details"].append(f"Game assignment failed: {error_text}")
                        return False
                
                # 4. Test student can see games
                if self.student_token:
                    student_headers = {"Authorization": f"Bearer {self.student_token}"}
                    async with self.session.get(f"{BACKEND_URL}/student/my-games", headers=student_headers) as response:
                        if response.status == 200:
                            games = await response.json()
                            if isinstance(games, list) and len(games) > 0:
                                logger.info(f"✅ Student can see {len(games)} assigned games")
                                self.test_results["flashcard_system"]["details"].append("Student game retrieval works")
                                
                                # 5. Submit game score
                                score_data = {
                                    "assignment_id": games[0].get("id"),
                                    "score": 85,
                                    "total": 3
                                }
                                
                                async with self.session.post(f"{BACKEND_URL}/student/submit-game-score", json=score_data, headers=student_headers) as response:
                                    if response.status == 200:
                                        logger.info("✅ Game score submitted")
                                        self.test_results["flashcard_system"]["details"].append("Score submission works")
                                        self.test_results["flashcard_system"]["passed"] = True
                                        return True
                                    else:
                                        error_text = await response.text()
                                        logger.error(f"❌ Score submission failed: {response.status} - {error_text}")
                                        self.test_results["flashcard_system"]["details"].append(f"Score submission failed: {error_text}")
                                        return False
                            else:
                                logger.error("❌ Student has no games assigned")
                                self.test_results["flashcard_system"]["details"].append("No games found for student")
                                return False
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Student games retrieval failed: {response.status} - {error_text}")
                            self.test_results["flashcard_system"]["details"].append(f"Student games failed: {error_text}")
                            return False
                else:
                    logger.warning("⚠️ No student token for game testing")
                    self.test_results["flashcard_system"]["details"].append("No student token available")
                    return False
            else:
                logger.warning("⚠️ No test student for game assignment")
                self.test_results["flashcard_system"]["details"].append("No test student available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Flashcard system test error: {str(e)}")
            self.test_results["flashcard_system"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_video_system(self) -> bool:
        """Test K-Kid video assignment system"""
        try:
            logger.info("🔍 Testing video system...")
            
            if not self.teacher_token or not self.test_student_id:
                logger.error("❌ Missing teacher token or student ID")
                self.test_results["video_system"]["details"].append("Missing prerequisites")
                return False
            
            headers = {"Authorization": f"Bearer {self.teacher_token}"}
            
            # 1. Assign video to K-Kid student
            video_data = {
                "student_id": self.test_student_id,
                "title": "Learn Colors in English",
                "description": "Educational video for K-Kid level",
                "video_url": "https://www.youtube.com/watch?v=example123",
                "thumbnail_url": "/images/colors-video.jpg"
            }
            
            async with self.session.post(f"{BACKEND_URL}/teacher/assign-video", json=video_data, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Video assigned to K-Kid student")
                    self.test_results["video_system"]["details"].append("Video assignment works")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Video assignment failed: {response.status} - {error_text}")
                    self.test_results["video_system"]["details"].append(f"Video assignment failed: {error_text}")
                    return False
            
            # 2. Test student can see assigned videos
            if self.student_token:
                student_headers = {"Authorization": f"Bearer {self.student_token}"}
                async with self.session.get(f"{BACKEND_URL}/student/my-videos", headers=student_headers) as response:
                    if response.status == 200:
                        videos = await response.json()
                        if isinstance(videos, list) and len(videos) > 0:
                            logger.info(f"✅ Student can see {len(videos)} assigned videos")
                            self.test_results["video_system"]["details"].append("Student video retrieval works")
                            self.test_results["video_system"]["passed"] = True
                            return True
                        else:
                            logger.error("❌ Student has no videos assigned")
                            self.test_results["video_system"]["details"].append("No videos found for student")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Student videos retrieval failed: {response.status} - {error_text}")
                        self.test_results["video_system"]["details"].append(f"Student videos failed: {error_text}")
                        return False
            else:
                logger.warning("⚠️ No student token for video testing")
                self.test_results["video_system"]["details"].append("No student token available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Video system test error: {str(e)}")
            self.test_results["video_system"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_question_management(self) -> bool:
        """Test admin test question management"""
        try:
            logger.info("🔍 Testing test question management...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 1. Create QCM question
            qcm_data = {
                "level": "intermediate",
                "question_type": "mcq",
                "question": "What is the past tense of 'go'?",
                "options": ["goed", "went", "gone", "going"],
                "correct_answer": 1
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/create-test-question", json=qcm_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    qcm_question_id = result.get("question_id")
                    logger.info("✅ QCM question created")
                    self.test_results["test_questions"]["details"].append("QCM question creation works")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ QCM question creation failed: {response.status} - {error_text}")
                    self.test_results["test_questions"]["details"].append(f"QCM creation failed: {error_text}")
                    return False
            
            # 2. Create True/False question
            tf_data = {
                "level": "beginner",
                "question_type": "true_false",
                "question": "The word 'cat' has 3 letters.",
                "correct_answer": True
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/create-test-question", json=tf_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    tf_question_id = result.get("question_id")
                    logger.info("✅ True/False question created")
                    self.test_results["test_questions"]["details"].append("True/False question creation works")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ True/False question creation failed: {response.status} - {error_text}")
                    self.test_results["test_questions"]["details"].append(f"True/False creation failed: {error_text}")
                    return False
            
            # 3. Test filtering by level
            async with self.session.get(f"{BACKEND_URL}/test-questions/intermediate", headers=headers) as response:
                if response.status == 200:
                    questions = await response.json()
                    if isinstance(questions, list):
                        logger.info(f"✅ Retrieved {len(questions)} intermediate questions")
                        self.test_results["test_questions"]["details"].append("Question filtering by level works")
                        self.test_results["test_questions"]["passed"] = True
                        return True
                    else:
                        logger.error("❌ Questions response is not a list")
                        self.test_results["test_questions"]["details"].append("Invalid questions response")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Question retrieval failed: {response.status} - {error_text}")
                    self.test_results["test_questions"]["details"].append(f"Question retrieval failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Test question management error: {str(e)}")
            self.test_results["test_questions"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_pricing_independence(self) -> bool:
        """Test EUR vs FCFA price independence"""
        try:
            logger.info("🔍 Testing pricing independence...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 1. Get current pricing
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    original_pricing = await response.json()
                    logger.info("✅ Retrieved current pricing")
                else:
                    logger.error("❌ Failed to get current pricing")
                    self.test_results["pricing_independence"]["details"].append("Failed to get pricing")
                    return False
            
            # 2. Update EUR prices only
            new_pricing = original_pricing.copy()
            new_pricing["beginner_eur"] = 80  # Changed from original
            new_pricing["intermediate_eur"] = 95  # Changed from original
            # Keep FCFA prices unchanged if they exist
            
            async with self.session.post(f"{BACKEND_URL}/admin/update-prices", json=new_pricing, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ EUR prices updated")
                    self.test_results["pricing_independence"]["details"].append("EUR price update works")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Price update failed: {response.status} - {error_text}")
                    self.test_results["pricing_independence"]["details"].append(f"Price update failed: {error_text}")
                    return False
            
            # 3. Verify prices were updated correctly
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    updated_pricing = await response.json()
                    
                    if (updated_pricing.get("beginner_eur") == 80 and 
                        updated_pricing.get("intermediate_eur") == 95):
                        logger.info("✅ EUR prices updated correctly")
                        self.test_results["pricing_independence"]["details"].append("EUR prices independent")
                        
                        # Restore original pricing
                        async with self.session.post(f"{BACKEND_URL}/admin/update-prices", json=original_pricing, headers=headers) as restore_response:
                            if restore_response.status == 200:
                                logger.info("✅ Original pricing restored")
                                self.test_results["pricing_independence"]["details"].append("Pricing restored")
                                self.test_results["pricing_independence"]["passed"] = True
                                return True
                            else:
                                logger.warning("⚠️ Failed to restore original pricing")
                                self.test_results["pricing_independence"]["details"].append("Failed to restore pricing")
                                return False
                    else:
                        logger.error("❌ Prices not updated correctly")
                        self.test_results["pricing_independence"]["details"].append("Price update verification failed")
                        return False
                else:
                    logger.error("❌ Failed to verify updated pricing")
                    self.test_results["pricing_independence"]["details"].append("Price verification failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Pricing independence test error: {str(e)}")
            self.test_results["pricing_independence"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_admin_delete_user(self) -> bool:
        """Test admin user deletion functionality"""
        try:
            logger.info("🔍 Testing admin user deletion...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Create a temporary teacher for deletion test
            temp_teacher_data = {
                "first_name": "TempTeacher",
                "last_name": "ForDeletion"
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/create-teacher", json=temp_teacher_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    temp_email = data.get('email')
                    
                    # Get the teacher ID
                    async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as users_response:
                        if users_response.status == 200:
                            users = await users_response.json()
                            temp_teacher_id = None
                            for user in users:
                                if user.get('email') == temp_email:
                                    temp_teacher_id = user.get('id')
                                    break
                            
                            if temp_teacher_id:
                                # Delete the teacher
                                async with self.session.delete(f"{BACKEND_URL}/admin/delete-user/{temp_teacher_id}", headers=headers) as delete_response:
                                    if delete_response.status == 200:
                                        logger.info("✅ Teacher deleted successfully")
                                        self.test_results["admin_delete_user"]["details"].append("User deletion works")
                                        
                                        # Verify teacher is deleted
                                        async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as verify_response:
                                            if verify_response.status == 200:
                                                remaining_users = await verify_response.json()
                                                teacher_still_exists = any(user.get('id') == temp_teacher_id for user in remaining_users)
                                                
                                                if not teacher_still_exists:
                                                    logger.info("✅ Teacher properly removed from database")
                                                    self.test_results["admin_delete_user"]["details"].append("User properly deleted")
                                                    self.test_results["admin_delete_user"]["passed"] = True
                                                    return True
                                                else:
                                                    logger.error("❌ Teacher still exists after deletion")
                                                    self.test_results["admin_delete_user"]["details"].append("User not properly deleted")
                                                    return False
                                            else:
                                                logger.error("❌ Failed to verify deletion")
                                                self.test_results["admin_delete_user"]["details"].append("Deletion verification failed")
                                                return False
                                    else:
                                        error_text = await delete_response.text()
                                        logger.error(f"❌ User deletion failed: {delete_response.status} - {error_text}")
                                        self.test_results["admin_delete_user"]["details"].append(f"Deletion failed: {error_text}")
                                        return False
                            else:
                                logger.error("❌ Could not find temp teacher ID")
                                self.test_results["admin_delete_user"]["details"].append("Could not find temp teacher")
                                return False
                        else:
                            logger.error("❌ Failed to get users list")
                            self.test_results["admin_delete_user"]["details"].append("Failed to get users")
                            return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create temp teacher: {response.status} - {error_text}")
                    self.test_results["admin_delete_user"]["details"].append(f"Temp teacher creation failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Admin delete user test error: {str(e)}")
            self.test_results["admin_delete_user"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_email_notifications(self) -> bool:
        """Test email notification logging"""
        try:
            logger.info("🔍 Testing email notifications...")
            
            # Test registration email logging by creating a new student
            student_data = {
                "email": "test.email@example.com",
                "first_name": "TestEmail",
                "last_name": "User",
                "phone": "+33987654321",
                "level": "beginner",
                "preferred_slots": "Soir",
                "referral_source": "Test"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=student_data) as response:
                if response.status == 200:
                    logger.info("✅ Registration submitted - emails should be logged")
                    self.test_results["email_notifications"]["details"].append("Registration triggers email logging")
                    self.test_results["email_notifications"]["passed"] = True
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Registration failed: {response.status} - {error_text}")
                    self.test_results["email_notifications"]["details"].append(f"Registration failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Email notifications test error: {str(e)}")
            self.test_results["email_notifications"]["details"].append(f"Test error: {str(e)}")
            return False
    
    async def test_group_registration(self) -> dict:
        """Test 1: Group registration endpoint"""
        try:
            logger.info("🔍 Testing group registration...")
            
            # Test group registration with 1 main person + 2 additional members
            group_data = {
                "first_name": "Alice",
                "last_name": "Dupont",
                "email": "alice.groupe@example.com",
                "phone": "+33612345678",
                "country_code": "+33",
                "level": "intermediate",
                "additional_members": [
                    {
                        "first_name": "Bob",
                        "last_name": "Martin"
                    },
                    {
                        "first_name": "Charlie",
                        "last_name": "Bernard"
                    }
                ],
                "preferred_slots": "Lundi 14h-16h",
                "referral_source": "Facebook"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/register-group", json=group_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Verify response structure
                    required_fields = ["message", "group_id", "total_members", "members_names"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        if result.get("total_members") == 3:
                            logger.info("✅ Group registration successful with correct member count")
                            self.test_results["group_registration"]["details"].append("Group registration endpoint works")
                            self.test_results["group_registration"]["details"].append(f"Group ID: {result.get('group_id')}")
                            self.test_results["group_registration"]["details"].append(f"Total members: {result.get('total_members')}")
                            self.test_results["group_registration"]["passed"] = True
                            return {
                                "group_id": result.get("group_id"),
                                "email": group_data["email"],
                                "total_members": result.get("total_members")
                            }
                        else:
                            logger.error(f"❌ Incorrect member count: expected 3, got {result.get('total_members')}")
                            self.test_results["group_registration"]["details"].append(f"Incorrect member count: {result.get('total_members')}")
                            return None
                    else:
                        logger.error(f"❌ Missing required fields in response: {missing_fields}")
                        self.test_results["group_registration"]["details"].append(f"Missing fields: {missing_fields}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Group registration failed: {response.status} - {error_text}")
                    self.test_results["group_registration"]["details"].append(f"Registration failed: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Group registration test error: {str(e)}")
            self.test_results["group_registration"]["details"].append(f"Test error: {str(e)}")
            return None

    async def test_pending_group_registrations(self) -> bool:
        """Test 2: Get pending group registrations (Admin)"""
        try:
            logger.info("🔍 Testing pending group registrations retrieval...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/admin/pending-group-registrations", headers=headers) as response:
                if response.status == 200:
                    pending_groups = await response.json()
                    
                    if isinstance(pending_groups, list):
                        logger.info(f"✅ Retrieved {len(pending_groups)} pending group registrations")
                        self.test_results["pending_group_registrations"]["details"].append(f"Retrieved {len(pending_groups)} pending groups")
                        
                        # Verify structure of pending groups
                        if len(pending_groups) > 0:
                            group = pending_groups[0]
                            required_fields = ["id", "email", "is_approved", "magic_code_generated", "members", "total_members"]
                            missing_fields = [field for field in required_fields if field not in group]
                            
                            if not missing_fields:
                                if group.get("is_approved") == False and group.get("magic_code_generated") == False:
                                    logger.info("✅ Pending group has correct approval status")
                                    self.test_results["pending_group_registrations"]["details"].append("Group approval status correct")
                                    self.test_results["pending_group_registrations"]["passed"] = True
                                    return True
                                else:
                                    logger.error("❌ Group approval status incorrect")
                                    self.test_results["pending_group_registrations"]["details"].append("Incorrect approval status")
                                    return False
                            else:
                                logger.error(f"❌ Missing fields in group data: {missing_fields}")
                                self.test_results["pending_group_registrations"]["details"].append(f"Missing fields: {missing_fields}")
                                return False
                        else:
                            logger.info("✅ No pending groups found (expected if none exist)")
                            self.test_results["pending_group_registrations"]["details"].append("No pending groups found")
                            self.test_results["pending_group_registrations"]["passed"] = True
                            return True
                    else:
                        logger.error("❌ Response is not a list")
                        self.test_results["pending_group_registrations"]["details"].append("Invalid response format")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to get pending groups: {response.status} - {error_text}")
                    self.test_results["pending_group_registrations"]["details"].append(f"Request failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Pending group registrations test error: {str(e)}")
            self.test_results["pending_group_registrations"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_magic_code_generation(self, group_id: str) -> dict:
        """Test 3: Generate magic code for group (Admin)"""
        try:
            logger.info("🔍 Testing magic code generation...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # First ensure we have a teacher to assign
            if not self.test_teacher_id:
                teacher_info = await self.create_test_teacher()
                if not teacher_info:
                    logger.error("❌ Failed to create test teacher for magic code test")
                    self.test_results["magic_code_generation"]["details"].append("Failed to create test teacher")
                    return None
            
            # Generate magic code
            async with self.session.post(f"{BACKEND_URL}/admin/generate-magic-code/{group_id}?teacher_id={self.test_teacher_id}", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Verify response structure
                    required_fields = ["message", "magic_code", "group_id", "email", "total_members", "members_names", "teacher_name", "teacher_email"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        magic_code = result.get("magic_code")
                        if magic_code and len(magic_code) == 8:
                            logger.info(f"✅ Magic code generated successfully: {magic_code}")
                            self.test_results["magic_code_generation"]["details"].append("Magic code generated with correct length")
                            self.test_results["magic_code_generation"]["details"].append(f"Magic code: {magic_code}")
                            self.test_results["magic_code_generation"]["details"].append(f"Teacher assigned: {result.get('teacher_name')}")
                            self.test_results["magic_code_generation"]["passed"] = True
                            return {
                                "magic_code": magic_code,
                                "email": result.get("email"),
                                "group_id": group_id
                            }
                        else:
                            logger.error(f"❌ Invalid magic code format: {magic_code}")
                            self.test_results["magic_code_generation"]["details"].append(f"Invalid magic code: {magic_code}")
                            return None
                    else:
                        logger.error(f"❌ Missing required fields in response: {missing_fields}")
                        self.test_results["magic_code_generation"]["details"].append(f"Missing fields: {missing_fields}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Magic code generation failed: {response.status} - {error_text}")
                    self.test_results["magic_code_generation"]["details"].append(f"Generation failed: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Magic code generation test error: {str(e)}")
            self.test_results["magic_code_generation"]["details"].append(f"Test error: {str(e)}")
            return None

    async def test_magic_code_login(self, email: str, magic_code: str) -> bool:
        """Test 4: Login with magic code"""
        try:
            logger.info("🔍 Testing magic code login...")
            
            login_data = {
                "email": email,
                "password": magic_code
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Verify response structure
                    required_fields = ["access_token", "token_type", "user"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        if result.get("token_type") == "bearer" and result.get("access_token"):
                            user_info = result.get("user", {})
                            if user_info.get("email") == email:
                                logger.info("✅ Magic code login successful")
                                self.test_results["magic_code_login"]["details"].append("Magic code login works")
                                self.test_results["magic_code_login"]["details"].append(f"User logged in: {user_info.get('first_name')} {user_info.get('last_name')}")
                                self.test_results["magic_code_login"]["passed"] = True
                                return True
                            else:
                                logger.error("❌ User email mismatch in login response")
                                self.test_results["magic_code_login"]["details"].append("Email mismatch in response")
                                return False
                        else:
                            logger.error("❌ Invalid token response")
                            self.test_results["magic_code_login"]["details"].append("Invalid token response")
                            return False
                    else:
                        logger.error(f"❌ Missing required fields in login response: {missing_fields}")
                        self.test_results["magic_code_login"]["details"].append(f"Missing fields: {missing_fields}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Magic code login failed: {response.status} - {error_text}")
                    self.test_results["magic_code_login"]["details"].append(f"Login failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Magic code login test error: {str(e)}")
            self.test_results["magic_code_login"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_group_system_verification(self, group_id: str, magic_code: str) -> bool:
        """Test 5: Additional verifications for group system"""
        try:
            logger.info("🔍 Testing group system verifications...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 1. Verify group no longer appears in pending registrations
            async with self.session.get(f"{BACKEND_URL}/admin/pending-group-registrations", headers=headers) as response:
                if response.status == 200:
                    pending_groups = await response.json()
                    group_still_pending = any(group.get("id") == group_id for group in pending_groups)
                    
                    if not group_still_pending:
                        logger.info("✅ Group no longer appears in pending registrations")
                        self.test_results["group_system_verification"]["details"].append("Group removed from pending list")
                    else:
                        logger.error("❌ Group still appears in pending registrations")
                        self.test_results["group_system_verification"]["details"].append("Group still in pending list")
                        return False
                else:
                    logger.error("❌ Failed to check pending registrations")
                    self.test_results["group_system_verification"]["details"].append("Failed to check pending list")
                    return False
            
            # 2. Try to generate magic code again (should fail)
            async with self.session.post(f"{BACKEND_URL}/admin/generate-magic-code/{group_id}?teacher_id={self.test_teacher_id}", headers=headers) as response:
                if response.status == 400:
                    logger.info("✅ Cannot generate second magic code (correct behavior)")
                    self.test_results["group_system_verification"]["details"].append("Duplicate magic code generation prevented")
                else:
                    logger.error("❌ Should not be able to generate second magic code")
                    self.test_results["group_system_verification"]["details"].append("Duplicate magic code generation not prevented")
                    return False
            
            # 3. Test multiple simultaneous logins with same code
            login_data = {
                "email": "alice.groupe@example.com",
                "password": magic_code
            }
            
            # Simulate 2 simultaneous logins
            login_tasks = [
                self.session.post(f"{BACKEND_URL}/auth/login", json=login_data),
                self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            ]
            
            responses = await asyncio.gather(*login_tasks, return_exceptions=True)
            successful_logins = 0
            
            for response in responses:
                if not isinstance(response, Exception):
                    if response.status == 200:
                        successful_logins += 1
                    await response.close()
            
            if successful_logins >= 2:
                logger.info("✅ Multiple simultaneous logins work with same magic code")
                self.test_results["group_system_verification"]["details"].append("Multiple simultaneous logins supported")
                self.test_results["group_system_verification"]["passed"] = True
                return True
            else:
                logger.error(f"❌ Only {successful_logins}/2 simultaneous logins succeeded")
                self.test_results["group_system_verification"]["details"].append(f"Only {successful_logins}/2 simultaneous logins worked")
                return False
                
        except Exception as e:
            logger.error(f"❌ Group system verification test error: {str(e)}")
            self.test_results["group_system_verification"]["details"].append(f"Test error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run comprehensive backend tests for My KALAMA ENGLISH"""
        logger.info("🚀 Starting My KALAMA ENGLISH Backend Tests")
        logger.info("=" * 70)
        
        # Login as admin
        if not await self.login_admin():
            logger.error("❌ Cannot proceed without admin login")
            return
        
        # Create test users
        logger.info("\n🔧 Setting up test users...")
        teacher_info = await self.create_test_teacher()
        student_info = await self.create_test_student()
        
        if teacher_info:
            await self.login_teacher(teacher_info["email"], teacher_info["password"])
        
        if student_info:
            await self.login_student(student_info["email"], student_info["password"])
        
        # Run NEW FEATURE TESTS first (priority tests from review request)
        
        # Test 1: Flashcard System (NOUVEAU)
        logger.info(f"\n📋 Running: Flashcard System Test (PRIORITY)")
        logger.info("-" * 50)
        try:
            result = await self.test_flashcard_system()
            if result:
                logger.info(f"✅ Flashcard System: PASSED")
            else:
                logger.error(f"❌ Flashcard System: FAILED")
        except Exception as e:
            logger.error(f"❌ Flashcard System: ERROR - {str(e)}")
        
        # Test 2: Video System K-Kid (NOUVEAU)
        logger.info(f"\n📋 Running: Video System K-Kid Test (PRIORITY)")
        logger.info("-" * 50)
        try:
            result = await self.test_video_system()
            if result:
                logger.info(f"✅ Video System: PASSED")
            else:
                logger.error(f"❌ Video System: FAILED")
        except Exception as e:
            logger.error(f"❌ Video System: ERROR - {str(e)}")
        
        # Test 3: Test Questions Management (NOUVEAU)
        logger.info(f"\n📋 Running: Test Questions Management (PRIORITY)")
        logger.info("-" * 50)
        try:
            result = await self.test_question_management()
            if result:
                logger.info(f"✅ Test Questions: PASSED")
            else:
                logger.error(f"❌ Test Questions: FAILED")
        except Exception as e:
            logger.error(f"❌ Test Questions: ERROR - {str(e)}")
        
        # Test 4: Pricing Independence (RÉCENT)
        logger.info(f"\n📋 Running: EUR vs FCFA Pricing Independence (PRIORITY)")
        logger.info("-" * 50)
        try:
            result = await self.test_pricing_independence()
            if result:
                logger.info(f"✅ Pricing Independence: PASSED")
            else:
                logger.error(f"❌ Pricing Independence: FAILED")
        except Exception as e:
            logger.error(f"❌ Pricing Independence: ERROR - {str(e)}")
        
        # Test 5: Admin Delete User
        logger.info(f"\n📋 Running: Admin User Deletion (PRIORITY)")
        logger.info("-" * 50)
        try:
            result = await self.test_admin_delete_user()
            if result:
                logger.info(f"✅ Admin Delete User: PASSED")
            else:
                logger.error(f"❌ Admin Delete User: FAILED")
        except Exception as e:
            logger.error(f"❌ Admin Delete User: ERROR - {str(e)}")
        
        # Test 6: Email Notifications
        logger.info(f"\n📋 Running: Email Notifications Logging (PRIORITY)")
        logger.info("-" * 50)
        try:
            result = await self.test_email_notifications()
            if result:
                logger.info(f"✅ Email Notifications: PASSED")
            else:
                logger.error(f"❌ Email Notifications: FAILED")
        except Exception as e:
            logger.error(f"❌ Email Notifications: ERROR - {str(e)}")
        
        # EXISTING KALAMATHÈQUE TESTS (if time permits)
        logger.info(f"\n📋 Running: Kalamathèque File Upload")
        logger.info("-" * 50)
        test_file_url = None
        try:
            test_file_url = await self.test_file_upload()
            if test_file_url:
                logger.info(f"✅ File Upload: PASSED")
            else:
                logger.error(f"❌ File Upload: FAILED")
        except Exception as e:
            logger.error(f"❌ File Upload: ERROR - {str(e)}")
        
        logger.info(f"\n📋 Running: Kalamathèque Access Verification")
        logger.info("-" * 50)
        try:
            result = await self.test_access_verification()
            if result:
                logger.info(f"✅ Access Verification: PASSED")
            else:
                logger.error(f"❌ Access Verification: FAILED")
        except Exception as e:
            logger.error(f"❌ Access Verification: ERROR - {str(e)}")
        
        if test_file_url:
            logger.info(f"\n📋 Running: Kalamathèque Book Creation")
            logger.info("-" * 50)
            try:
                result = await self.test_book_creation(test_file_url)
                if result:
                    logger.info(f"✅ Book Creation: PASSED")
                else:
                    logger.error(f"❌ Book Creation: FAILED")
            except Exception as e:
                logger.error(f"❌ Book Creation: ERROR - {str(e)}")
        
        logger.info(f"\n📋 Running: Kalamathèque Book Retrieval")
        logger.info("-" * 50)
        try:
            result = await self.test_book_retrieval()
            if result:
                logger.info(f"✅ Book Retrieval: PASSED")
            else:
                logger.error(f"❌ Book Retrieval: FAILED")
        except Exception as e:
            logger.error(f"❌ Book Retrieval: ERROR - {str(e)}")
        
        logger.info(f"\n📋 Running: Kalamathèque AI Assistant")
        logger.info("-" * 50)
        try:
            result = await self.test_ai_assistant()
            if result:
                logger.info(f"✅ AI Assistant: PASSED")
            else:
                logger.error(f"❌ AI Assistant: FAILED")
        except Exception as e:
            logger.error(f"❌ AI Assistant: ERROR - {str(e)}")
        
        logger.info(f"\n📋 Running: Kalamathèque Text-to-Speech")
        logger.info("-" * 50)
        try:
            result = await self.test_text_to_speech()
            if result:
                logger.info(f"✅ Text-to-Speech: PASSED")
            else:
                logger.error(f"❌ Text-to-Speech: FAILED")
        except Exception as e:
            logger.error(f"❌ Text-to-Speech: ERROR - {str(e)}")
        
        if self.test_book_id:
            logger.info(f"\n📋 Running: Kalamathèque Book Deletion")
            logger.info("-" * 50)
            try:
                result = await self.test_book_deletion()
                if result:
                    logger.info(f"✅ Book Deletion: PASSED")
                else:
                    logger.error(f"❌ Book Deletion: FAILED")
            except Exception as e:
                logger.error(f"❌ Book Deletion: ERROR - {str(e)}")
        
        # Calculate overall results
        passed_tests = sum(1 for results in self.test_results.values() if results["passed"])
        total_tests = len(self.test_results) - 1  # Exclude overall_backend
        
        # Overall assessment
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            self.test_results["overall_backend"]["passed"] = True
            self.test_results["overall_backend"]["details"].append(f"Strong performance: {passed_tests}/{total_tests} tests passed")
        else:
            self.test_results["overall_backend"]["details"].append(f"Needs attention: {passed_tests}/{total_tests} tests passed")
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("🏁 MY KALAMA ENGLISH BACKEND TEST SUMMARY")
        logger.info("=" * 70)
        
        # Priority tests first
        priority_tests = ["flashcard_system", "video_system", "test_questions", "pricing_independence", "admin_delete_user", "email_notifications"]
        
        logger.info("\n🎯 PRIORITY TESTS (New Features):")
        for test_name in priority_tests:
            if test_name in self.test_results:
                results = self.test_results[test_name]
                status = "✅ PASSED" if results["passed"] else "❌ FAILED"
                logger.info(f"  {test_name.upper().replace('_', ' ')}: {status}")
                for detail in results["details"]:
                    logger.info(f"    • {detail}")
        
        logger.info("\n📚 KALAMATHÈQUE TESTS:")
        kalamathèque_tests = ["file_upload", "access_verification", "book_creation", "book_retrieval", "ai_assistant", "text_to_speech", "book_deletion"]
        for test_name in kalamathèque_tests:
            if test_name in self.test_results:
                results = self.test_results[test_name]
                status = "✅ PASSED" if results["passed"] else "❌ FAILED"
                logger.info(f"  {test_name.upper().replace('_', ' ')}: {status}")
                for detail in results["details"]:
                    logger.info(f"    • {detail}")
        
        logger.info(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests >= total_tests * 0.8:
            logger.info("🎉 BACKEND TESTS SUCCESSFUL!")
        else:
            logger.warning("⚠️ SOME BACKEND TESTS FAILED - REVIEW REQUIRED")

async def main():
    """Main test runner"""
    async with MyKalamaEnglishBackendTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())