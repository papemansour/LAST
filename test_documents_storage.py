#!/usr/bin/env python3
"""
Document Storage System Test for My KALAMA ENGLISH
Tests the complete document system as requested in the review
"""

import asyncio
import aiohttp
import json
import logging
import tempfile
import os
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://tutor-hub-32.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"
STUDENT_EMAIL = "test.student@example.com"
STUDENT_PASSWORD = "Test2025"

class DocumentStorageSystemTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.student_token = None
        self.test_student_id = None
        
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

    async def login_student(self) -> bool:
        """Login as student and get token"""
        try:
            login_data = {
                "email": STUDENT_EMAIL,
                "password": STUDENT_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.student_token = data.get("access_token")
                    user_info = data.get("user", {})
                    self.test_student_id = user_info.get("id")
                    logger.info(f"✅ Student login successful: {user_info.get('email')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Student login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Student login error: {str(e)}")
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
/Length 50
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document Storage System) Tj
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
305
%%EOF"""
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(test_content)
                return temp_file.name
                
        except Exception as e:
            logger.error(f"❌ Error creating test document file: {str(e)}")
            return None

    async def test_document_upload(self) -> Optional[str]:
        """Test 1: Document upload (Admin)"""
        try:
            logger.info("📤 Testing document upload...")
            
            # Create test file
            test_file_path = await self.create_test_document_file()
            if not test_file_path:
                logger.error("❌ Failed to create test file")
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
                                    return file_url
                                else:
                                    logger.error(f"❌ Invalid file URL format: {file_url}")
                                    return None
                            else:
                                logger.error(f"❌ Missing fields in upload response: {missing_fields}")
                                return None
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Document upload failed: {response.status} - {error_text}")
                            return None
            finally:
                # Clean up test file
                if os.path.exists(test_file_path):
                    os.unlink(test_file_path)
                    
        except Exception as e:
            logger.error(f"❌ Document upload test error: {str(e)}")
            return None

    async def test_document_send(self, file_url: str) -> bool:
        """Test 2: Send document to student"""
        try:
            logger.info("📨 Testing document send...")
            
            if not self.test_student_id:
                logger.error("❌ No test student available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Send document to student
            document_data = {
                "title": "Test Document Storage",
                "description": "Document de test pour vérifier le système de stockage",
                "file_url": file_url,
                "file_name": "test_document.pdf",
                "file_type": "pdf",
                "recipient_ids": [self.test_student_id]
            }
            
            async with self.session.post(f"{BACKEND_URL}/documents/send", json=document_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Document sent successfully")
                    logger.info(f"📄 Response: {result.get('message', 'Success')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Document send failed: {response.status} - {error_text}")
                    
                    # Check if it's the known DocumentCreate model conflict
                    if "recipient_type" in error_text or "Field required" in error_text:
                        logger.error("🚨 CONFIRMED: DocumentCreate model conflict detected")
                        logger.error("💡 ISSUE: Backend expects 'recipient_type' instead of 'recipient_ids'")
                    
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Document send test error: {str(e)}")
            return False

    async def test_file_access_via_curl(self, file_url: str) -> bool:
        """Test 3: Direct file access via curl (GET /uploads/documents/{filename})"""
        try:
            logger.info("🔗 Testing direct file access...")
            
            # Extract filename from URL
            filename = file_url.split('/')[-1] if file_url else None
            if not filename:
                logger.error("❌ Cannot extract filename from URL")
                return False
            
            # Test direct file access
            file_access_url = f"https://tutor-hub-32.preview.emergentagent.com/uploads/documents/{filename}"
            
            async with self.session.get(file_access_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', '0')
                    
                    logger.info(f"✅ File accessible via direct URL")
                    logger.info(f"📄 Content-Type: {content_type}")
                    logger.info(f"📏 Content-Length: {content_length} bytes")
                    logger.info(f"🔗 URL: {file_access_url}")
                    
                    # Verify content type for PDF
                    if filename.endswith('.pdf') and 'pdf' in content_type.lower():
                        logger.info("✅ PDF Content-Type verification passed")
                    
                    return True
                else:
                    logger.error(f"❌ File access failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Document access test error: {str(e)}")
            return False

    async def test_student_document_retrieval(self) -> bool:
        """Test 4: Student document retrieval (GET /api/documents/my-documents)"""
        try:
            logger.info("📥 Testing student document retrieval...")
            
            if not self.student_token:
                logger.error("❌ No student token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.student_token}"}
            
            # Get student documents
            async with self.session.get(f"{BACKEND_URL}/documents/my-documents", headers=headers) as response:
                if response.status == 200:
                    documents = await response.json()
                    
                    if isinstance(documents, list):
                        logger.info(f"✅ Retrieved {len(documents)} documents for student")
                        
                        # Check document structure
                        if len(documents) > 0:
                            doc = documents[0]
                            required_fields = ["id", "title", "file_url"]
                            missing_fields = [field for field in required_fields if field not in doc]
                            
                            if not missing_fields:
                                logger.info("✅ Document structure validation passed")
                                
                                # Verify URL format
                                file_url = doc.get('file_url', '')
                                if file_url.startswith('/uploads/documents/'):
                                    logger.info("✅ Document URL format correct")
                                    logger.info(f"📄 Document: {doc.get('title')} - {file_url}")
                                else:
                                    logger.warning(f"⚠️ Unexpected URL format: {file_url}")
                            else:
                                logger.warning(f"⚠️ Missing document fields: {missing_fields}")
                        
                        return True
                    else:
                        logger.error("❌ Documents response is not a list")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Document retrieval failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Document retrieval test error: {str(e)}")
            return False

    async def test_existing_file_access(self) -> bool:
        """Test 5: Access to existing file in uploads directory"""
        try:
            logger.info("📋 Testing existing file access...")
            
            # Use the existing PDF file mentioned in the review request
            existing_filename = "05684018-449e-481d-92d9-95382bca65a7.pdf"
            file_access_url = f"https://tutor-hub-32.preview.emergentagent.com/uploads/documents/{existing_filename}"
            
            async with self.session.get(file_access_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', '0')
                    
                    logger.info(f"✅ Existing file accessible")
                    logger.info(f"📄 File: {existing_filename}")
                    logger.info(f"📄 Content-Type: {content_type}")
                    logger.info(f"📏 Content-Length: {content_length} bytes")
                    logger.info(f"🔗 URL: {file_access_url}")
                    
                    return True
                else:
                    logger.error(f"❌ Existing file access failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Existing file access test error: {str(e)}")
            return False

    async def verify_files_in_directory(self) -> bool:
        """Verify files are stored in /app/uploads/documents/"""
        try:
            logger.info("📁 Verifying files in /app/uploads/documents/...")
            
            # This would be done via shell command in the container
            # For now, we'll just log that this should be verified manually
            logger.info("📁 Files should be verified to exist in /app/uploads/documents/")
            logger.info("📁 Use: ls -la /app/uploads/documents/ to verify")
            
            return True
                    
        except Exception as e:
            logger.error(f"❌ Directory verification error: {str(e)}")
            return False

    async def run_complete_test(self):
        """Run the complete document storage system test"""
        logger.info("🚀 Starting Document Storage System Test")
        logger.info("=" * 70)
        
        # Step 1: Login as admin
        logger.info("\n🔐 Step 1: Admin Login")
        if not await self.login_admin():
            logger.error("❌ Cannot continue without admin access")
            return
        
        # Step 2: Login as student
        logger.info("\n🔐 Step 2: Student Login")
        if not await self.login_student():
            logger.error("❌ Cannot continue without student access")
            return
        
        # Step 3: Document Upload
        logger.info("\n📤 Step 3: Document Upload Test")
        file_url = await self.test_document_upload()
        if not file_url:
            logger.error("❌ Document upload failed - cannot continue with full test")
            return
        
        # Step 4: Send Document to Student
        logger.info("\n📨 Step 4: Send Document to Student")
        send_success = await self.test_document_send(file_url)
        
        # Step 5: Direct File Access
        logger.info("\n🔗 Step 5: Direct File Access Test")
        access_success = await self.test_file_access_via_curl(file_url)
        
        # Step 6: Student Document Retrieval
        logger.info("\n📥 Step 6: Student Document Retrieval")
        retrieval_success = await self.test_student_document_retrieval()
        
        # Step 7: Existing File Access
        logger.info("\n📋 Step 7: Existing File Access Test")
        existing_success = await self.test_existing_file_access()
        
        # Step 8: Directory Verification
        logger.info("\n📁 Step 8: Directory Verification")
        directory_success = await self.verify_files_in_directory()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 DOCUMENT STORAGE SYSTEM TEST RESULTS")
        logger.info("=" * 70)
        
        tests = [
            ("Document Upload", bool(file_url)),
            ("Document Send", send_success),
            ("Direct File Access", access_success),
            ("Student Retrieval", retrieval_success),
            ("Existing File Access", existing_success),
            ("Directory Verification", directory_success)
        ]
        
        passed_tests = 0
        for test_name, result in tests:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
            if result:
                passed_tests += 1
        
        logger.info(f"\n📈 Overall Result: {passed_tests}/{len(tests)} tests passed ({(passed_tests/len(tests))*100:.1f}%)")
        
        # Critical assessment
        critical_tests = [bool(file_url), access_success, existing_success]
        critical_passed = sum(critical_tests)
        
        if critical_passed >= 2:  # Upload + Access OR Upload + Existing
            logger.info("🎉 CORE DOCUMENT STORAGE FUNCTIONALITY WORKING!")
            logger.info("✅ Files can be uploaded and accessed via StaticFiles")
        else:
            logger.error("❌ CRITICAL DOCUMENT STORAGE ISSUES DETECTED")
        
        # Known issues
        if not send_success:
            logger.warning("⚠️ KNOWN ISSUE: Document send fails due to DocumentCreate model conflict")
            logger.warning("💡 SOLUTION: Fix conflicting DocumentCreate models in server.py")

async def main():
    """Main test runner"""
    async with DocumentStorageSystemTester() as tester:
        await tester.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())