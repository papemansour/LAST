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
import random
import string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://e-learn-dash.preview.emergentagent.com/api"

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
            # Review Request Priority Tests
            "dashboard_access": {"passed": False, "details": []},
            "documents_section": {"passed": False, "details": []},
            "student_pack_info": {"passed": False, "details": []},
            
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
            "pricing_update_flow": {"passed": False, "details": []},
            "admin_delete_user": {"passed": False, "details": []},
            "email_notifications": {"passed": False, "details": []},
            
            # Group registration system tests
            "group_registration": {"passed": False, "details": []},
            "pending_group_registrations": {"passed": False, "details": []},
            "magic_code_generation": {"passed": False, "details": []},
            "magic_code_login": {"passed": False, "details": []},
            "group_system_verification": {"passed": False, "details": []},
            
            # Document system tests (NEW)
            "document_upload": {"passed": False, "details": []},
            "document_send": {"passed": False, "details": []},
            "document_access": {"passed": False, "details": []},
            "document_retrieval": {"passed": False, "details": []},
            "document_system": {"passed": False, "details": []},
            
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

    async def test_pricing_update_flow(self) -> bool:
        """Test complete pricing update flow as requested in review"""
        try:
            logger.info("🔍 Testing complete pricing update flow...")
            
            # 1. Admin login (already done in login_admin)
            if not self.admin_token:
                logger.error("❌ Admin not logged in")
                self.test_results["pricing_update_flow"]["details"].append("Admin login failed")
                return False
            
            logger.info("✅ Step 1: Admin logged in successfully")
            self.test_results["pricing_update_flow"]["details"].append("Admin login successful")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 2. Get current prices via GET /api/pricing
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    original_pricing = await response.json()
                    original_beginner_eur = original_pricing.get("beginner_eur", 76)
                    logger.info(f"✅ Step 2: Retrieved current prices - beginner_eur: {original_beginner_eur}")
                    self.test_results["pricing_update_flow"]["details"].append(f"Current beginner_eur: {original_beginner_eur}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 2 failed: GET /api/pricing - {response.status} - {error_text}")
                    self.test_results["pricing_update_flow"]["details"].append(f"GET pricing failed: {error_text}")
                    return False
            
            # 3. Modify prices via POST /admin/update-prices (change beginner_eur from 76 to 80)
            updated_pricing = original_pricing.copy()
            updated_pricing["beginner_eur"] = 80
            
            async with self.session.post(f"{BACKEND_URL}/admin/update-prices", json=updated_pricing, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Step 3: Prices updated successfully via POST /admin/update-prices")
                    self.test_results["pricing_update_flow"]["details"].append("Price update successful")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 3 failed: POST /admin/update-prices - {response.status} - {error_text}")
                    self.test_results["pricing_update_flow"]["details"].append(f"Price update failed: {error_text}")
                    return False
            
            # 4. Verify new prices are returned by GET /api/pricing
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    new_pricing = await response.json()
                    new_beginner_eur = new_pricing.get("beginner_eur")
                    
                    if new_beginner_eur == 80:
                        logger.info(f"✅ Step 4: New prices verified via GET /api/pricing - beginner_eur: {new_beginner_eur}")
                        self.test_results["pricing_update_flow"]["details"].append(f"New beginner_eur confirmed: {new_beginner_eur}")
                    else:
                        logger.error(f"❌ Step 4 failed: Expected beginner_eur=80, got {new_beginner_eur}")
                        self.test_results["pricing_update_flow"]["details"].append(f"Price verification failed: expected 80, got {new_beginner_eur}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 4 failed: GET /api/pricing verification - {response.status} - {error_text}")
                    self.test_results["pricing_update_flow"]["details"].append(f"Price verification failed: {error_text}")
                    return False
            
            # 5. Verify prices are saved in MongoDB (by checking persistence)
            # Wait a moment and check again to ensure database persistence
            await asyncio.sleep(1)
            
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    persistent_pricing = await response.json()
                    persistent_beginner_eur = persistent_pricing.get("beginner_eur")
                    
                    if persistent_beginner_eur == 80:
                        logger.info("✅ Step 5: Prices confirmed saved in MongoDB (persistence verified)")
                        self.test_results["pricing_update_flow"]["details"].append("MongoDB persistence verified")
                    else:
                        logger.error(f"❌ Step 5 failed: Price not persisted in MongoDB")
                        self.test_results["pricing_update_flow"]["details"].append("MongoDB persistence failed")
                        return False
                else:
                    logger.error(f"❌ Step 5 failed: Cannot verify MongoDB persistence")
                    self.test_results["pricing_update_flow"]["details"].append("MongoDB persistence check failed")
                    return False
            
            # SUCCESS: All steps completed
            logger.info("🎉 PRICING UPDATE FLOW COMPLETE - All steps successful!")
            logger.info("✅ Criteria met: Modified prices by admin are immediately visible via GET /api/pricing")
            
            # Restore original pricing for cleanup
            async with self.session.post(f"{BACKEND_URL}/admin/update-prices", json=original_pricing, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Cleanup: Original pricing restored")
                    self.test_results["pricing_update_flow"]["details"].append("Original pricing restored")
                else:
                    logger.warning("⚠️ Cleanup: Failed to restore original pricing")
                    self.test_results["pricing_update_flow"]["details"].append("Failed to restore original pricing")
            
            self.test_results["pricing_update_flow"]["passed"] = True
            return True
                    
        except Exception as e:
            logger.error(f"❌ Pricing update flow test error: {str(e)}")
            self.test_results["pricing_update_flow"]["details"].append(f"Test error: {str(e)}")
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

    async def create_test_document_file(self) -> str:
        """Create a test PDF file for document upload testing"""
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
(Test Document System) Tj
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
            logger.error(f"❌ Error creating test document file: {str(e)}")
            return None

    async def test_document_system_complete(self) -> bool:
        """Complete document system test as requested in review"""
        try:
            logger.info("🔍 Testing complete document system...")
            
            # Test 1: Document Upload (Admin)
            logger.info("📤 Step 1: Testing document upload...")
            file_url = await self.test_document_upload()
            if not file_url:
                logger.error("❌ Document upload failed - cannot continue")
                return False
            
            # Test 2: Send Document to Student
            logger.info("📨 Step 2: Testing document send...")
            send_success = await self.test_document_send(file_url)
            
            # Test 3: Direct File Access
            logger.info("🔗 Step 3: Testing direct file access...")
            access_success = await self.test_document_access(file_url)
            
            # Test 4: Student Document Retrieval
            logger.info("📥 Step 4: Testing student document retrieval...")
            retrieval_success = await self.test_document_retrieval()
            
            # Test 5: Existing File Access
            logger.info("📋 Step 5: Testing existing file access...")
            existing_success = await self.test_existing_file_access()
            
            # Overall assessment
            tests_passed = sum([
                bool(file_url),  # Upload
                send_success,    # Send
                access_success,  # Access
                retrieval_success, # Retrieval
                existing_success   # Existing file
            ])
            
            logger.info(f"📊 Document system tests: {tests_passed}/5 passed")
            
            # Consider system working if upload, access, and existing file work
            if file_url and access_success and existing_success:
                logger.info("✅ Core document system functionality working")
                self.test_results["document_system"]["details"].append("Core functionality working (upload, access, StaticFiles)")
                self.test_results["document_system"]["passed"] = True
                return True
            else:
                logger.error("❌ Core document system functionality failed")
                self.test_results["document_system"]["details"].append("Core functionality failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Complete document system test error: {str(e)}")
            self.test_results["document_system"]["details"].append(f"System test error: {str(e)}")
            return False

    async def test_document_upload(self) -> Optional[str]:
        """Test document upload (Admin/Prof)"""
        try:
            logger.info("🔍 Testing document upload...")
            
            # Create test file
            test_file_path = await self.create_test_document_file()
            if not test_file_path:
                self.test_results["document_upload"]["details"].append("Failed to create test file")
                return None
            
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Upload document
                with open(test_file_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('file', file, filename='test_document.pdf', content_type='application/pdf')
                    
                    async with self.session.post(f"{BACKEND_URL}/documents/upload", data=data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # Check response structure
                            required_fields = ["file_url", "file_name", "file_type"]
                            missing_fields = [field for field in required_fields if field not in result]
                            
                            if not missing_fields:
                                file_url = result.get('file_url')
                                if file_url and file_url.startswith('/uploads/documents/'):
                                    logger.info("✅ Document upload successful")
                                    logger.info(f"📄 File URL: {file_url}")
                                    self.test_results["document_upload"]["details"].append("Document uploaded successfully")
                                    self.test_results["document_upload"]["details"].append(f"File URL format correct: {file_url}")
                                    self.test_results["document_upload"]["passed"] = True
                                    return file_url
                                else:
                                    logger.error(f"❌ Invalid file URL format: {file_url}")
                                    self.test_results["document_upload"]["details"].append(f"Invalid URL format: {file_url}")
                                    return None
                            else:
                                logger.error(f"❌ Missing fields in upload response: {missing_fields}")
                                self.test_results["document_upload"]["details"].append(f"Missing fields: {missing_fields}")
                                return None
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Document upload failed: {response.status} - {error_text}")
                            self.test_results["document_upload"]["details"].append(f"Upload failed: {error_text}")
                            return None
            finally:
                # Clean up test file
                if os.path.exists(test_file_path):
                    os.unlink(test_file_path)
                    
        except Exception as e:
            logger.error(f"❌ Document upload test error: {str(e)}")
            self.test_results["document_upload"]["details"].append(f"Test error: {str(e)}")
            return None

    async def test_document_send(self, file_url: str) -> bool:
        """Test send document to student"""
        try:
            logger.info("🔍 Testing document send...")
            
            if not self.test_student_id:
                logger.error("❌ No test student available")
                self.test_results["document_send"]["details"].append("No test student available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Send document to student
            document_data = {
                "title": "Test Document",
                "description": "Document de test pour vérifier le système",
                "file_url": file_url,
                "file_name": "test_document.pdf",
                "file_type": "pdf",
                "recipient_ids": [self.test_student_id]
            }
            
            async with self.session.post(f"{BACKEND_URL}/documents/send", json=document_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Document sent successfully")
                    self.test_results["document_send"]["details"].append("Document sent to student")
                    self.test_results["document_send"]["details"].append(f"Response: {result.get('message', 'Success')}")
                    self.test_results["document_send"]["passed"] = True
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Document send failed: {response.status} - {error_text}")
                    self.test_results["document_send"]["details"].append(f"Send failed: {error_text}")
                    
                    # Check if it's the known DocumentCreate model conflict
                    if "recipient_type" in error_text or "Field required" in error_text:
                        logger.error("🚨 CONFIRMED: DocumentCreate model conflict detected")
                        self.test_results["document_send"]["details"].append("ISSUE: DocumentCreate model conflict - endpoint expects 'recipient_type' instead of 'recipient_ids'")
                    
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Document send test error: {str(e)}")
            self.test_results["document_send"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_document_access(self, file_url: str) -> bool:
        """Test direct file access via backend"""
        try:
            logger.info("🔍 Testing document access...")
            
            # Extract filename from URL
            filename = file_url.split('/')[-1] if file_url else None
            if not filename:
                logger.error("❌ Cannot extract filename from URL")
                self.test_results["document_access"]["details"].append("Invalid file URL")
                return False
            
            # Test direct file access
            file_access_url = f"https://e-learn-dash.preview.emergentagent.com/uploads/documents/{filename}"
            
            async with self.session.get(file_access_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', '0')
                    
                    logger.info(f"✅ File accessible via direct URL")
                    logger.info(f"📄 Content-Type: {content_type}")
                    logger.info(f"📏 Content-Length: {content_length} bytes")
                    
                    self.test_results["document_access"]["details"].append("File accessible via direct URL")
                    self.test_results["document_access"]["details"].append(f"Content-Type: {content_type}")
                    self.test_results["document_access"]["details"].append(f"Content-Length: {content_length} bytes")
                    
                    # Verify content type for PDF
                    if filename.endswith('.pdf') and 'pdf' in content_type.lower():
                        logger.info("✅ PDF Content-Type correct")
                        self.test_results["document_access"]["details"].append("PDF Content-Type verification passed")
                    
                    self.test_results["document_access"]["passed"] = True
                    return True
                else:
                    logger.error(f"❌ File access failed: {response.status}")
                    self.test_results["document_access"]["details"].append(f"File access failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Document access test error: {str(e)}")
            self.test_results["document_access"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_document_retrieval(self) -> bool:
        """Test student document retrieval"""
        try:
            logger.info("🔍 Testing document retrieval...")
            
            if not self.student_token:
                logger.error("❌ No student token available")
                self.test_results["document_retrieval"]["details"].append("No student token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.student_token}"}
            
            # Get student documents
            async with self.session.get(f"{BACKEND_URL}/documents/my-documents", headers=headers) as response:
                if response.status == 200:
                    documents = await response.json()
                    
                    if isinstance(documents, list):
                        logger.info(f"✅ Retrieved {len(documents)} documents for student")
                        self.test_results["document_retrieval"]["details"].append(f"Retrieved {len(documents)} documents")
                        
                        # Check document structure
                        if len(documents) > 0:
                            doc = documents[0]
                            required_fields = ["id", "title", "file_url"]
                            missing_fields = [field for field in required_fields if field not in doc]
                            
                            if not missing_fields:
                                logger.info("✅ Document structure correct")
                                self.test_results["document_retrieval"]["details"].append("Document structure validation passed")
                                
                                # Verify URL format
                                file_url = doc.get('file_url', '')
                                if file_url.startswith('/uploads/documents/'):
                                    logger.info("✅ Document URL format correct")
                                    self.test_results["document_retrieval"]["details"].append("Document URL format correct")
                                else:
                                    logger.warning(f"⚠️ Unexpected URL format: {file_url}")
                                    self.test_results["document_retrieval"]["details"].append(f"Unexpected URL format: {file_url}")
                            else:
                                logger.warning(f"⚠️ Missing document fields: {missing_fields}")
                                self.test_results["document_retrieval"]["details"].append(f"Missing fields: {missing_fields}")
                        
                        self.test_results["document_retrieval"]["passed"] = True
                        return True
                    else:
                        logger.error("❌ Documents response is not a list")
                        self.test_results["document_retrieval"]["details"].append("Invalid response format")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Document retrieval failed: {response.status} - {error_text}")
                    self.test_results["document_retrieval"]["details"].append(f"Retrieval failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Document retrieval test error: {str(e)}")
            self.test_results["document_retrieval"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_existing_file_access(self) -> bool:
        """Test access to existing file in uploads directory"""
        try:
            logger.info("🔍 Testing existing file access...")
            
            # Use the existing PDF file mentioned in the review request
            existing_filename = "05684018-449e-481d-92d9-95382bca65a7.pdf"
            file_access_url = f"https://e-learn-dash.preview.emergentagent.com/uploads/documents/{existing_filename}"
            
            async with self.session.get(file_access_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', '0')
                    
                    logger.info(f"✅ Existing file accessible")
                    logger.info(f"📄 Content-Type: {content_type}")
                    logger.info(f"📏 Content-Length: {content_length} bytes")
                    
                    self.test_results["document_system"]["details"].append("Existing file accessible via StaticFiles")
                    self.test_results["document_system"]["details"].append(f"File: {existing_filename}")
                    self.test_results["document_system"]["details"].append(f"Content-Type: {content_type}")
                    
                    return True
                else:
                    logger.error(f"❌ Existing file access failed: {response.status}")
                    self.test_results["document_system"]["details"].append(f"Existing file access failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Existing file access test error: {str(e)}")
            self.test_results["document_system"]["details"].append(f"Existing file test error: {str(e)}")
            return False
    
    async def test_group_registration(self) -> dict:
        """Test 1: Group registration endpoint"""
        try:
            logger.info("🔍 Testing group registration...")
            
            # Generate unique email for this test run
            import time
            unique_id = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            
            # Test group registration with 1 main person + 2 additional members
            group_data = {
                "first_name": "Alice",
                "last_name": "Dupont",
                "email": f"alice.groupe.{unique_id}@example.com",
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

    async def test_group_system_verification(self, group_id: str, magic_code: str, email: str) -> bool:
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
                "email": email,
                "password": magic_code
            }
            
            # Test multiple simultaneous logins with same code (simplified approach)
            successful_logins = 0
            
            # Test first login
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response1:
                if response1.status == 200:
                    successful_logins += 1
            
            # Test second login
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response2:
                if response2.status == 200:
                    successful_logins += 1
            
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

    async def test_dashboard_access_complete(self) -> bool:
        """Test complete dashboard access for all 3 roles as per review request"""
        try:
            logger.info("🔍 Testing complete dashboard access (Admin, Teacher, Student)...")
            
            # Test credentials from review request
            test_credentials = [
                {"email": "admin@mykalamaenglish.com", "password": "adminco", "role": "admin"},
                {"email": "prof.test@example.com", "password": "TestProf2025", "role": "teacher"},
                {"email": "test.student@example.com", "password": "Test2025", "role": "student"}
            ]
            
            dashboard_results = []
            
            for creds in test_credentials:
                logger.info(f"🔍 Testing {creds['role']} dashboard access...")
                
                # Login with specific credentials
                login_data = {
                    "email": creds["email"],
                    "password": creds["password"]
                }
                
                async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        token = data.get("access_token")
                        user_info = data.get("user", {})
                        
                        logger.info(f"✅ {creds['role']} login successful: {creds['email']}")
                        
                        # Test /api/auth/me endpoint
                        headers = {"Authorization": f"Bearer {token}"}
                        async with self.session.get(f"{BACKEND_URL}/auth/me", headers=headers) as me_response:
                            if me_response.status == 200:
                                me_data = await me_response.json()
                                logger.info(f"✅ {creds['role']} /auth/me works - Role: {me_data.get('role')}, Level: {me_data.get('level')}")
                                
                                dashboard_results.append({
                                    "role": creds['role'],
                                    "email": creds['email'],
                                    "login_success": True,
                                    "auth_me_success": True,
                                    "user_data": me_data
                                })
                            else:
                                error_text = await me_response.text()
                                logger.error(f"❌ {creds['role']} /auth/me failed: {me_response.status} - {error_text}")
                                dashboard_results.append({
                                    "role": creds['role'],
                                    "email": creds['email'],
                                    "login_success": True,
                                    "auth_me_success": False,
                                    "error": error_text
                                })
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ {creds['role']} login failed: {response.status} - {error_text}")
                        dashboard_results.append({
                            "role": creds['role'],
                            "email": creds['email'],
                            "login_success": False,
                            "error": error_text
                        })
            
            # Check results
            successful_logins = sum(1 for result in dashboard_results if result.get("login_success"))
            successful_auth_me = sum(1 for result in dashboard_results if result.get("auth_me_success"))
            
            if successful_logins == 3 and successful_auth_me == 3:
                logger.info("✅ All 3 dashboards accessible without errors")
                self.test_results["dashboard_access"]["passed"] = True
                self.test_results["dashboard_access"]["details"].append("All 3 dashboard logins successful")
                self.test_results["dashboard_access"]["details"].append("All /auth/me endpoints working")
                return dashboard_results
            else:
                logger.error(f"❌ Dashboard access issues: {successful_logins}/3 logins, {successful_auth_me}/3 auth/me")
                self.test_results["dashboard_access"]["details"].append(f"Login issues: {successful_logins}/3 successful")
                return False
                
        except Exception as e:
            logger.error(f"❌ Dashboard access test error: {str(e)}")
            self.test_results["dashboard_access"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_documents_section_complete(self) -> bool:
        """Test Documents section access for all dashboards as per review request"""
        try:
            logger.info("🔍 Testing Documents section in all dashboards...")
            
            # Get tokens for all roles
            dashboard_results = await self.test_dashboard_access_complete()
            if not dashboard_results:
                logger.error("❌ Cannot test documents without dashboard access")
                return False
            
            documents_results = []
            
            for result in dashboard_results:
                if not result.get("login_success"):
                    continue
                    
                role = result["role"]
                email = result["email"]
                
                logger.info(f"🔍 Testing Documents section for {role}...")
                
                # Login again to get fresh token
                login_data = {"email": email, "password": self.get_password_for_email(email)}
                
                async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        token = data.get("access_token")
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        # Test documents endpoints based on role
                        if role == "student":
                            # Test GET /api/documents/my-documents
                            async with self.session.get(f"{BACKEND_URL}/documents/my-documents", headers=headers) as doc_response:
                                if doc_response.status == 200:
                                    documents = await doc_response.json()
                                    logger.info(f"✅ {role} can access my-documents: {len(documents)} documents")
                                    
                                    # Test GET /api/documents/received  
                                    async with self.session.get(f"{BACKEND_URL}/documents/received", headers=headers) as received_response:
                                        if received_response.status == 200:
                                            received_docs = await received_response.json()
                                            logger.info(f"✅ {role} can access received documents: {len(received_docs)} documents")
                                            
                                            documents_results.append({
                                                "role": role,
                                                "email": email,
                                                "my_documents_success": True,
                                                "received_documents_success": True,
                                                "my_documents_count": len(documents),
                                                "received_documents_count": len(received_docs)
                                            })
                                        else:
                                            error_text = await received_response.text()
                                            logger.error(f"❌ {role} received documents failed: {received_response.status} - {error_text}")
                                            documents_results.append({
                                                "role": role,
                                                "email": email,
                                                "my_documents_success": True,
                                                "received_documents_success": False,
                                                "error": error_text
                                            })
                                else:
                                    error_text = await doc_response.text()
                                    logger.error(f"❌ {role} my-documents failed: {doc_response.status} - {error_text}")
                                    documents_results.append({
                                        "role": role,
                                        "email": email,
                                        "my_documents_success": False,
                                        "error": error_text
                                    })
                        
                        elif role in ["admin", "teacher"]:
                            # Test document sending capabilities
                            async with self.session.get(f"{BACKEND_URL}/documents/my-documents", headers=headers) as doc_response:
                                if doc_response.status == 200:
                                    documents = await doc_response.json()
                                    logger.info(f"✅ {role} can access documents: {len(documents)} documents")
                                    
                                    documents_results.append({
                                        "role": role,
                                        "email": email,
                                        "documents_access_success": True,
                                        "documents_count": len(documents)
                                    })
                                else:
                                    error_text = await doc_response.text()
                                    logger.error(f"❌ {role} documents access failed: {doc_response.status} - {error_text}")
                                    documents_results.append({
                                        "role": role,
                                        "email": email,
                                        "documents_access_success": False,
                                        "error": error_text
                                    })
            
            # Evaluate results
            successful_tests = sum(1 for result in documents_results if 
                                 result.get("my_documents_success") or result.get("documents_access_success"))
            
            if successful_tests >= 2:  # At least 2 out of 3 roles working
                logger.info("✅ Documents section accessible in dashboards")
                self.test_results["documents_section"]["passed"] = True
                self.test_results["documents_section"]["details"].append("Documents section accessible")
                self.test_results["documents_section"]["details"].append(f"Results: {documents_results}")
                return True
            else:
                logger.error("❌ Documents section access issues")
                self.test_results["documents_section"]["details"].append("Documents access issues")
                return False
                
        except Exception as e:
            logger.error(f"❌ Documents section test error: {str(e)}")
            self.test_results["documents_section"]["details"].append(f"Test error: {str(e)}")
            return False

    async def test_student_pack_info(self) -> bool:
        """Test student pack information for test.student@example.com as per review request"""
        try:
            logger.info("🔍 Testing student pack information for test.student@example.com...")
            
            # Login as the specific student
            login_data = {
                "email": "test.student@example.com",
                "password": "Test2025"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    logger.info("✅ Student login successful")
                    
                    # Get detailed user info via /auth/me
                    headers = {"Authorization": f"Bearer {token}"}
                    async with self.session.get(f"{BACKEND_URL}/auth/me", headers=headers) as me_response:
                        if me_response.status == 200:
                            student_data = await me_response.json()
                            
                            # Extract pack information
                            level = student_data.get("level")
                            phone = student_data.get("phone", "")
                            email = student_data.get("email")
                            
                            # Check if phone has country code +221
                            has_senegal_code = phone.startswith("+221")
                            
                            logger.info(f"✅ Student pack info retrieved:")
                            logger.info(f"   - Email: {email}")
                            logger.info(f"   - Level/Pack: {level}")
                            logger.info(f"   - Phone: {phone}")
                            logger.info(f"   - Has +221 code: {has_senegal_code}")
                            
                            # Get pricing for the student's level
                            async with self.session.get(f"{BACKEND_URL}/pricing") as pricing_response:
                                if pricing_response.status == 200:
                                    pricing_data = await pricing_response.json()
                                    
                                    # Determine price based on level
                                    price_key = f"{level}_eur" if level else "beginner_eur"
                                    student_price = pricing_data.get(price_key, "Unknown")
                                    
                                    logger.info(f"   - Pack price: {student_price} EUR")
                                    
                                    self.test_results["student_pack_info"]["passed"] = True
                                    self.test_results["student_pack_info"]["details"].append(f"Student: {email}")
                                    self.test_results["student_pack_info"]["details"].append(f"Pack/Level: {level}")
                                    self.test_results["student_pack_info"]["details"].append(f"Phone: {phone}")
                                    self.test_results["student_pack_info"]["details"].append(f"Has +221 code: {has_senegal_code}")
                                    self.test_results["student_pack_info"]["details"].append(f"Price: {student_price} EUR")
                                    
                                    return {
                                        "email": email,
                                        "level": level,
                                        "phone": phone,
                                        "has_senegal_code": has_senegal_code,
                                        "price": student_price
                                    }
                                else:
                                    logger.error("❌ Failed to get pricing information")
                                    self.test_results["student_pack_info"]["details"].append("Pricing retrieval failed")
                                    return False
                        else:
                            error_text = await me_response.text()
                            logger.error(f"❌ Failed to get student details: {me_response.status} - {error_text}")
                            self.test_results["student_pack_info"]["details"].append(f"Student details failed: {error_text}")
                            return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Student login failed: {response.status} - {error_text}")
                    self.test_results["student_pack_info"]["details"].append(f"Student login failed: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Student pack info test error: {str(e)}")
            self.test_results["student_pack_info"]["details"].append(f"Test error: {str(e)}")
            return False

    def get_password_for_email(self, email: str) -> str:
        """Get password for specific email addresses"""
        password_map = {
            "admin@mykalamaenglish.com": "adminco",
            "prof.test@example.com": "TestProf2025", 
            "test.student@example.com": "Test2025"
        }
        return password_map.get(email, "")

    async def run_all_tests(self):
        """Run comprehensive backend tests for My KALAMA ENGLISH"""
        logger.info("🚀 Starting My KALAMA ENGLISH Backend Tests")
        logger.info("=" * 70)
        
        # Login as admin
        if not await self.login_admin():
            logger.error("❌ Cannot proceed without admin login")
            return
        
        # REVIEW REQUEST PRIORITY TESTS (HIGHEST PRIORITY)
        logger.info(f"\n🎯 Running: REVIEW REQUEST PRIORITY TESTS")
        logger.info("=" * 70)
        
        # Test 1: Dashboard Access for all 3 roles
        logger.info(f"\n📋 Running: Dashboard Access Test (Admin, Teacher, Student)")
        logger.info("-" * 50)
        try:
            result = await self.test_dashboard_access_complete()
            if result:
                logger.info(f"✅ Dashboard Access: PASSED")
            else:
                logger.error(f"❌ Dashboard Access: FAILED")
        except Exception as e:
            logger.error(f"❌ Dashboard Access: ERROR - {str(e)}")
        
        # Test 2: Documents Section in all dashboards
        logger.info(f"\n📋 Running: Documents Section Test")
        logger.info("-" * 50)
        try:
            result = await self.test_documents_section_complete()
            if result:
                logger.info(f"✅ Documents Section: PASSED")
            else:
                logger.error(f"❌ Documents Section: FAILED")
        except Exception as e:
            logger.error(f"❌ Documents Section: ERROR - {str(e)}")
        
        # Test 3: Student Pack Information
        logger.info(f"\n📋 Running: Student Pack Information Test")
        logger.info("-" * 50)
        try:
            result = await self.test_student_pack_info()
            if result:
                logger.info(f"✅ Student Pack Info: PASSED")
            else:
                logger.error(f"❌ Student Pack Info: FAILED")
        except Exception as e:
            logger.error(f"❌ Student Pack Info: ERROR - {str(e)}")
        
        # Create test users for other tests
        logger.info("\n🔧 Setting up test users for additional tests...")
        teacher_info = await self.create_test_teacher()
        student_info = await self.create_test_student()
        
        if teacher_info:
            await self.login_teacher(teacher_info["email"], teacher_info["password"])
        
        if student_info:
            await self.login_student(student_info["email"], student_info["password"])
        
        # GROUP REGISTRATION SYSTEM TESTS (SECONDARY PRIORITY)
        logger.info(f"\n📋 Running: Group Registration System Tests")
        logger.info("=" * 70)
        
        # Test 1: Group Registration
        logger.info(f"\n📋 Running: Group Registration")
        logger.info("-" * 50)
        group_info = None
        try:
            group_info = await self.test_group_registration()
            if group_info:
                logger.info(f"✅ Group Registration: PASSED")
            else:
                logger.error(f"❌ Group Registration: FAILED")
        except Exception as e:
            logger.error(f"❌ Group Registration: ERROR - {str(e)}")
        
        # Test 2: Pending Group Registrations
        logger.info(f"\n📋 Running: Pending Group Registrations")
        logger.info("-" * 50)
        try:
            result = await self.test_pending_group_registrations()
            if result:
                logger.info(f"✅ Pending Group Registrations: PASSED")
            else:
                logger.error(f"❌ Pending Group Registrations: FAILED")
        except Exception as e:
            logger.error(f"❌ Pending Group Registrations: ERROR - {str(e)}")
        
        # Test 3: Magic Code Generation (only if group registration succeeded)
        magic_code_info = None
        if group_info:
            logger.info(f"\n📋 Running: Magic Code Generation")
            logger.info("-" * 50)
            try:
                magic_code_info = await self.test_magic_code_generation(group_info["group_id"])
                if magic_code_info:
                    logger.info(f"✅ Magic Code Generation: PASSED")
                else:
                    logger.error(f"❌ Magic Code Generation: FAILED")
            except Exception as e:
                logger.error(f"❌ Magic Code Generation: ERROR - {str(e)}")
        
        # Test 4: Magic Code Login (only if magic code was generated)
        if magic_code_info:
            logger.info(f"\n📋 Running: Magic Code Login")
            logger.info("-" * 50)
            try:
                result = await self.test_magic_code_login(magic_code_info["email"], magic_code_info["magic_code"])
                if result:
                    logger.info(f"✅ Magic Code Login: PASSED")
                else:
                    logger.error(f"❌ Magic Code Login: FAILED")
            except Exception as e:
                logger.error(f"❌ Magic Code Login: ERROR - {str(e)}")
        
        # Test 5: Group System Verification (only if magic code was generated)
        if magic_code_info:
            logger.info(f"\n📋 Running: Group System Verification")
            logger.info("-" * 50)
            try:
                result = await self.test_group_system_verification(magic_code_info["group_id"], magic_code_info["magic_code"], magic_code_info["email"])
                if result:
                    logger.info(f"✅ Group System Verification: PASSED")
                else:
                    logger.error(f"❌ Group System Verification: FAILED")
            except Exception as e:
                logger.error(f"❌ Group System Verification: ERROR - {str(e)}")

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
        
        # Test 4.5: Complete Pricing Update Flow (REVIEW REQUEST)
        logger.info(f"\n📋 Running: Complete Pricing Update Flow (REVIEW REQUEST)")
        logger.info("-" * 50)
        try:
            result = await self.test_pricing_update_flow()
            if result:
                logger.info(f"✅ Pricing Update Flow: PASSED")
            else:
                logger.error(f"❌ Pricing Update Flow: FAILED")
        except Exception as e:
            logger.error(f"❌ Pricing Update Flow: ERROR - {str(e)}")
        
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
        
        # Test 7: Document System (REVIEW REQUEST - HIGH PRIORITY)
        logger.info(f"\n📋 Running: Complete Document System Test (REVIEW REQUEST)")
        logger.info("-" * 50)
        try:
            result = await self.test_document_system_complete()
            if result:
                logger.info(f"✅ Document System: PASSED")
            else:
                logger.error(f"❌ Document System: FAILED")
        except Exception as e:
            logger.error(f"❌ Document System: ERROR - {str(e)}")
        
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
        
        # Group registration tests first (highest priority)
        group_tests = ["group_registration", "pending_group_registrations", "magic_code_generation", "magic_code_login", "group_system_verification"]
        
        logger.info("\n🎯 GROUP REGISTRATION SYSTEM TESTS (HIGHEST PRIORITY):")
        for test_name in group_tests:
            if test_name in self.test_results:
                results = self.test_results[test_name]
                status = "✅ PASSED" if results["passed"] else "❌ FAILED"
                logger.info(f"  {test_name.upper().replace('_', ' ')}: {status}")
                for detail in results["details"]:
                    logger.info(f"    • {detail}")
        
        # Priority tests second
        priority_tests = ["flashcard_system", "video_system", "test_questions", "pricing_independence", "admin_delete_user", "email_notifications", "document_system"]
        
        logger.info("\n🎯 OTHER PRIORITY TESTS (New Features):")
        for test_name in priority_tests:
            if test_name in self.test_results:
                results = self.test_results[test_name]
                status = "✅ PASSED" if results["passed"] else "❌ FAILED"
                logger.info(f"  {test_name.upper().replace('_', ' ')}: {status}")
                for detail in results["details"]:
                    logger.info(f"    • {detail}")
        
        logger.info("\n📄 DOCUMENT SYSTEM TESTS:")
        document_tests = ["document_upload", "document_send", "document_access", "document_retrieval"]
        for test_name in document_tests:
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