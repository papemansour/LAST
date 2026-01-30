#!/usr/bin/env python3
"""
Focused test for Teacher Session/Pointage System and Meet Links System
"""

import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://elearn-platform-13.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"

class FocusedTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.teacher_token = None
        self.student_token = None
        
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

    async def test_teacher_session_system(self) -> bool:
        """Test Teacher Session/Pointage System"""
        try:
            logger.info("🔍 Testing Teacher Session/Pointage System...")
            
            # Login as teacher first
            teacher_login_success = await self.login_teacher("prof.test@example.com", "TestProf2025")
            if not teacher_login_success:
                logger.error("❌ Failed to login as teacher")
                return False
            
            headers = {"Authorization": f"Bearer {self.teacher_token}"}
            
            # 1. Start a new session
            logger.info("📝 Test 1: Start Session")
            async with self.session.post(f"{BACKEND_URL}/teacher/session/start", headers=headers) as response:
                if response.status == 200:
                    start_result = await response.json()
                    session_id = start_result.get("session_id")
                    logger.info(f"✅ Test 1 PASSED: Session started successfully, session_id: {session_id}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 1 FAILED: Session start failed: {response.status} - {error_text}")
                    return False
            
            # 2. Pause the session
            logger.info("📝 Test 2: Pause Session")
            async with self.session.post(f"{BACKEND_URL}/teacher/session/pause", headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Test 2 PASSED: Session paused successfully")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 2 FAILED: Session pause failed: {response.status} - {error_text}")
                    return False
            
            # 3. Resume the session
            logger.info("📝 Test 3: Resume Session")
            async with self.session.post(f"{BACKEND_URL}/teacher/session/resume", headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Test 3 PASSED: Session resumed successfully")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 3 FAILED: Session resume failed: {response.status} - {error_text}")
                    return False
            
            # 4. End the session with timing data
            logger.info("📝 Test 4: End Session")
            end_data = {
                "total_time": 300,  # 5 minutes
                "paused_duration": 30  # 30 seconds
            }
            
            async with self.session.post(f"{BACKEND_URL}/teacher/session/end", json=end_data, headers=headers) as response:
                if response.status == 200:
                    end_result = await response.json()
                    logger.info(f"✅ Test 4 PASSED: Session ended successfully")
                    logger.info(f"📊 Response: {end_result}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 4 FAILED: Session end failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Teacher session system test error: {str(e)}")
            return False

    async def test_meet_links_system(self) -> bool:
        """Test Course Links (Meet Links) System"""
        try:
            logger.info("🔍 Testing Course Links (Meet Links) System...")
            
            # Login as teacher first
            teacher_login_success = await self.login_teacher("prof.test@example.com", "TestProf2025")
            if not teacher_login_success:
                logger.error("❌ Failed to login as teacher")
                return False
            
            headers = {"Authorization": f"Bearer {self.teacher_token}"}
            
            # 1. Get teacher's profile
            logger.info("📝 Test 1: Get Teacher Profile")
            async with self.session.get(f"{BACKEND_URL}/auth/me", headers=headers) as response:
                if response.status == 200:
                    teacher_data = await response.json()
                    logger.info(f"✅ Test 1 PASSED: Retrieved teacher profile")
                    logger.info(f"📊 Teacher: {teacher_data.get('first_name')} {teacher_data.get('last_name')}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 1 FAILED: Failed to get teacher profile: {response.status} - {error_text}")
                    return False
            
            # Get a real student ID from the database
            logger.info("📝 Test 2: Get Student List")
            student_id = None
            student_email = None
            async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers={"Authorization": f"Bearer {self.admin_token}"}) as response:
                if response.status == 200:
                    users = await response.json()
                    for user in users:
                        if user.get('role') == 'student' and user.get('is_active'):
                            student_id = user.get('id')
                            student_email = user.get('email')
                            logger.info(f"✅ Test 2 PASSED: Found active student: {student_email}")
                            break
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 2 FAILED: Failed to get users: {response.status} - {error_text}")
                    return False
            
            if not student_id:
                logger.error("❌ No active student found for testing")
                return False
            
            # 3. Send meet link to student
            logger.info("📝 Test 3: Send Meet Link")
            meet_link_data = {
                "student_id": student_id,
                "meet_link": "https://meet.google.com/test-link-123",
                "title": "Test Course Link",
                "scheduled_date": "2025-01-05T14:00:00Z"
            }
            
            async with self.session.post(f"{BACKEND_URL}/teacher/send-meet-link", json=meet_link_data, headers=headers) as response:
                if response.status == 200:
                    link_result = await response.json()
                    meet_id = link_result.get("meet_link_id")
                    logger.info(f"✅ Test 3 PASSED: Meet link sent successfully, meet_id: {meet_id}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Test 3 FAILED: Meet link sending failed: {response.status} - {error_text}")
                    return False
            
            # 4. Login as student to test receiving the link
            logger.info("📝 Test 4: Student Login")
            # Get student password
            student_password = None
            for user in users:
                if user.get('id') == student_id:
                    student_password = user.get('temporary_password') or "Test2025"
                    break
            
            if student_password:
                student_login_success = await self.login_student(student_email, student_password)
                if student_login_success:
                    logger.info("✅ Test 4 PASSED: Student login successful")
                    student_headers = {"Authorization": f"Bearer {self.student_token}"}
                    
                    # 5. Get student's meet links
                    logger.info("📝 Test 5: Get Student Meet Links")
                    async with self.session.get(f"{BACKEND_URL}/student/my-meet-links", headers=student_headers) as response:
                        if response.status == 200:
                            meet_links = await response.json()
                            if isinstance(meet_links, list) and len(meet_links) > 0:
                                logger.info(f"✅ Test 5 PASSED: Student received {len(meet_links)} meet links")
                                
                                # Verify teacher_name field is present
                                first_link = meet_links[0]
                                if "teacher_name" in first_link:
                                    logger.info("✅ Meet link contains teacher_name field")
                                else:
                                    logger.warning("⚠️ Meet link missing teacher_name field")
                                
                                logger.info(f"📊 First meet link: {first_link}")
                                
                                # 6. Mark meet as attended
                                if meet_id:
                                    logger.info("📝 Test 6: Mark Meet Attended")
                                    async with self.session.put(f"{BACKEND_URL}/student/mark-meet-attended/{meet_id}", headers=student_headers) as response:
                                        if response.status == 200:
                                            logger.info("✅ Test 6 PASSED: Meet marked as attended successfully")
                                            return True
                                        else:
                                            error_text = await response.text()
                                            logger.error(f"❌ Test 6 FAILED: Meet attendance marking failed: {response.status} - {error_text}")
                                            return False
                                else:
                                    logger.warning("⚠️ No meet_id available for attendance test")
                                    return True
                            else:
                                logger.error("❌ Test 5 FAILED: Student has no meet links")
                                return False
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Test 5 FAILED: Student meet links retrieval failed: {response.status} - {error_text}")
                            return False
                else:
                    logger.error("❌ Test 4 FAILED: Student login failed")
                    return False
            else:
                logger.error("❌ No student password available")
                return False
                    
        except Exception as e:
            logger.error(f"❌ Meet links system test error: {str(e)}")
            return False

    async def run_tests(self):
        """Run focused tests"""
        logger.info("🚀 Starting Focused Tests for Teacher Session & Meet Links")
        logger.info("=" * 70)
        
        # Login as admin first
        if not await self.login_admin():
            logger.error("❌ Cannot proceed without admin login")
            return
        
        # Test 1: Teacher Session/Pointage System
        logger.info("\n🎯 Test 1: Teacher Session/Pointage System")
        logger.info("-" * 50)
        session_result = await self.test_teacher_session_system()
        if session_result:
            logger.info("✅ TEACHER SESSION SYSTEM: PASSED")
        else:
            logger.error("❌ TEACHER SESSION SYSTEM: FAILED")
        
        # Test 2: Course Links (Meet Links) System
        logger.info("\n🎯 Test 2: Course Links (Meet Links) System")
        logger.info("-" * 50)
        meet_result = await self.test_meet_links_system()
        if meet_result:
            logger.info("✅ MEET LINKS SYSTEM: PASSED")
        else:
            logger.error("❌ MEET LINKS SYSTEM: FAILED")
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 FOCUSED TEST RESULTS SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Teacher Session System: {'✅ PASSED' if session_result else '❌ FAILED'}")
        logger.info(f"Meet Links System: {'✅ PASSED' if meet_result else '❌ FAILED'}")
        logger.info(f"Overall: {'✅ ALL TESTS PASSED' if session_result and meet_result else '❌ SOME TESTS FAILED'}")

async def main():
    async with FocusedTester() as tester:
        await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())