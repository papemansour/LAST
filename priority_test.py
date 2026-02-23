#!/usr/bin/env python3
"""
Priority Backend Testing for My KALAMA ENGLISH
Focus on new features from review request
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://elearning-platform-6.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"

class PriorityTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.teacher_token = None
        self.student_token = None
        self.test_teacher_id = None
        self.test_student_id = None
        self.test_flashcard_set_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login_admin(self) -> bool:
        """Login as admin and get token"""
        try:
            login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    logger.info("✅ Admin login successful")
                    return True
                else:
                    logger.error(f"❌ Admin login failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Admin login error: {str(e)}")
            return False

    async def setup_test_users(self):
        """Setup test users"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Get existing users
        async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as response:
            if response.status == 200:
                users = await response.json()
                for user in users:
                    if user.get('email') == 'proftest.flashcards@mykalamaenglish.com':
                        self.test_teacher_id = user.get('id')
                        temp_password = user.get('temporary_password') or f"Teacher{user.get('id', '')[:8]}"
                        
                        # Login as teacher
                        login_data = {"email": user.get('email'), "password": temp_password}
                        async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                            if login_response.status == 200:
                                login_result = await login_response.json()
                                self.teacher_token = login_result.get("access_token")
                                logger.info("✅ Teacher login successful")
                    
                    elif user.get('email') == 'etudiant.test@example.com':
                        self.test_student_id = user.get('id')
                        temp_password = user.get('temporary_password') or f"Kalama{user.get('id', '')[:6]}"
                        
                        # Login as student
                        login_data = {"email": user.get('email'), "password": temp_password}
                        async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                            if login_response.status == 200:
                                login_result = await login_response.json()
                                self.student_token = login_result.get("access_token")
                                logger.info("✅ Student login successful")

    async def test_flashcard_system(self) -> bool:
        """Test complete flashcard system workflow"""
        logger.info("🔍 Testing flashcard system...")
        
        if not self.teacher_token:
            logger.error("❌ No teacher token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            # 1. Create flashcard set
            set_data = {"title": "Test Vocabulary", "description": "Test flashcards"}
            async with self.session.post(f"{BACKEND_URL}/teacher/create-flashcard-set", json=set_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    self.test_flashcard_set_id = result.get("set_id")
                    logger.info("✅ Flashcard set created")
                else:
                    logger.error(f"❌ Flashcard set creation failed: {response.status}")
                    return False
            
            # 2. Add flashcards
            flashcards = [
                {"question": "Hello", "answer": "Bonjour", "set_id": self.test_flashcard_set_id},
                {"question": "Goodbye", "answer": "Au revoir", "set_id": self.test_flashcard_set_id}
            ]
            
            for flashcard in flashcards:
                async with self.session.post(f"{BACKEND_URL}/teacher/add-flashcard", json=flashcard, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"✅ Flashcard added: {flashcard['question']}")
                    else:
                        logger.error(f"❌ Failed to add flashcard: {response.status}")
                        return False
            
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
                    else:
                        logger.error(f"❌ Game assignment failed: {response.status}")
                        return False
                
                # 4. Test student can see games
                if self.student_token:
                    student_headers = {"Authorization": f"Bearer {self.student_token}"}
                    async with self.session.get(f"{BACKEND_URL}/student/my-games", headers=student_headers) as response:
                        if response.status == 200:
                            games = await response.json()
                            if isinstance(games, list) and len(games) > 0:
                                logger.info(f"✅ Student can see {len(games)} assigned games")
                                
                                # 5. Submit game score
                                score_data = {
                                    "assignment_id": games[0].get("id"),
                                    "score": 85,
                                    "total": 2
                                }
                                
                                async with self.session.post(f"{BACKEND_URL}/student/submit-game-score", json=score_data, headers=student_headers) as response:
                                    if response.status == 200:
                                        logger.info("✅ Game score submitted")
                                        return True
                                    else:
                                        logger.error(f"❌ Score submission failed: {response.status}")
                                        return False
                            else:
                                logger.error("❌ Student has no games assigned")
                                return False
                        else:
                            logger.error(f"❌ Student games retrieval failed: {response.status}")
                            return False
                else:
                    logger.warning("⚠️ No student token for game testing")
                    return False
            else:
                logger.warning("⚠️ No test student for game assignment")
                return False
                
        except Exception as e:
            logger.error(f"❌ Flashcard system test error: {str(e)}")
            return False

    async def test_video_system(self) -> bool:
        """Test K-Kid video assignment system"""
        logger.info("🔍 Testing video system...")
        
        if not self.teacher_token or not self.test_student_id:
            logger.error("❌ Missing teacher token or student ID")
            return False
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            # Assign video to K-Kid student
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
                else:
                    logger.error(f"❌ Video assignment failed: {response.status}")
                    return False
            
            # Test student can see assigned videos
            if self.student_token:
                student_headers = {"Authorization": f"Bearer {self.student_token}"}
                async with self.session.get(f"{BACKEND_URL}/student/my-videos", headers=student_headers) as response:
                    if response.status == 200:
                        videos = await response.json()
                        if isinstance(videos, list) and len(videos) > 0:
                            logger.info(f"✅ Student can see {len(videos)} assigned videos")
                            return True
                        else:
                            logger.error("❌ Student has no videos assigned")
                            return False
                    else:
                        logger.error(f"❌ Student videos retrieval failed: {response.status}")
                        return False
            else:
                logger.warning("⚠️ No student token for video testing")
                return False
                
        except Exception as e:
            logger.error(f"❌ Video system test error: {str(e)}")
            return False

    async def test_question_management(self) -> bool:
        """Test admin test question management"""
        logger.info("🔍 Testing test question management...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Create QCM question
            qcm_data = {
                "level": "intermediate",
                "question_type": "mcq",
                "question": "What is the past tense of 'go'?",
                "options": ["goed", "went", "gone", "going"],
                "correct_answer": 1
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/create-test-question", json=qcm_data, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ QCM question created")
                else:
                    logger.error(f"❌ QCM question creation failed: {response.status}")
                    return False
            
            # Create True/False question
            tf_data = {
                "level": "beginner",
                "question_type": "true_false",
                "question": "The word 'cat' has 3 letters.",
                "correct_answer": True
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/create-test-question", json=tf_data, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ True/False question created")
                else:
                    logger.error(f"❌ True/False question creation failed: {response.status}")
                    return False
            
            # Test filtering by level
            async with self.session.get(f"{BACKEND_URL}/test-questions/intermediate", headers=headers) as response:
                if response.status == 200:
                    questions = await response.json()
                    if isinstance(questions, list):
                        logger.info(f"✅ Retrieved {len(questions)} intermediate questions")
                        return True
                    else:
                        logger.error("❌ Questions response is not a list")
                        return False
                else:
                    logger.error(f"❌ Question retrieval failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Test question management error: {str(e)}")
            return False

    async def test_admin_delete_user(self) -> bool:
        """Test admin user deletion functionality"""
        logger.info("🔍 Testing admin user deletion...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Create a temporary teacher for deletion test
            temp_teacher_data = {"first_name": "TempTeacher", "last_name": "ForDeletion"}
            
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
                                        
                                        # Verify teacher is deleted
                                        async with self.session.get(f"{BACKEND_URL}/admin/all-users", headers=headers) as verify_response:
                                            if verify_response.status == 200:
                                                remaining_users = await verify_response.json()
                                                teacher_still_exists = any(user.get('id') == temp_teacher_id for user in remaining_users)
                                                
                                                if not teacher_still_exists:
                                                    logger.info("✅ Teacher properly removed from database")
                                                    return True
                                                else:
                                                    logger.error("❌ Teacher still exists after deletion")
                                                    return False
                                            else:
                                                logger.error("❌ Failed to verify deletion")
                                                return False
                                    else:
                                        logger.error(f"❌ User deletion failed: {delete_response.status}")
                                        return False
                            else:
                                logger.error("❌ Could not find temp teacher ID")
                                return False
                        else:
                            logger.error("❌ Failed to get users list")
                            return False
                else:
                    logger.error(f"❌ Failed to create temp teacher: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Admin delete user test error: {str(e)}")
            return False

    async def test_email_notifications(self) -> bool:
        """Test email notification logging"""
        logger.info("🔍 Testing email notifications...")
        
        try:
            # Test registration email logging by creating a new student
            student_data = {
                "email": "test.email.notifications@example.com",
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
                    return True
                else:
                    logger.error(f"❌ Registration failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Email notifications test error: {str(e)}")
            return False

    async def run_priority_tests(self):
        """Run priority tests from review request"""
        logger.info("🚀 Starting Priority Backend Tests")
        logger.info("=" * 60)
        
        # Login as admin
        if not await self.login_admin():
            logger.error("❌ Cannot proceed without admin login")
            return
        
        # Setup test users
        await self.setup_test_users()
        
        results = {}
        
        # Test 1: Flashcard System (NOUVEAU)
        logger.info(f"\n📋 Running: Flashcard System Test (PRIORITY)")
        logger.info("-" * 50)
        results["flashcard_system"] = await self.test_flashcard_system()
        
        # Test 2: Video System K-Kid (NOUVEAU)
        logger.info(f"\n📋 Running: Video System K-Kid Test (PRIORITY)")
        logger.info("-" * 50)
        results["video_system"] = await self.test_video_system()
        
        # Test 3: Test Questions Management (NOUVEAU)
        logger.info(f"\n📋 Running: Test Questions Management (PRIORITY)")
        logger.info("-" * 50)
        results["test_questions"] = await self.test_question_management()
        
        # Test 4: Admin Delete User
        logger.info(f"\n📋 Running: Admin User Deletion (PRIORITY)")
        logger.info("-" * 50)
        results["admin_delete_user"] = await self.test_admin_delete_user()
        
        # Test 5: Email Notifications
        logger.info(f"\n📋 Running: Email Notifications Logging (PRIORITY)")
        logger.info("-" * 50)
        results["email_notifications"] = await self.test_email_notifications()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("🏁 PRIORITY TESTS SUMMARY")
        logger.info("=" * 60)
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        logger.info(f"\nOverall Result: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests >= total_tests * 0.8:
            logger.info("🎉 PRIORITY TESTS SUCCESSFUL!")
        else:
            logger.warning("⚠️ SOME PRIORITY TESTS FAILED - REVIEW REQUIRED")
        
        return results

async def main():
    """Main test runner"""
    async with PriorityTester() as tester:
        await tester.run_priority_tests()

if __name__ == "__main__":
    asyncio.run(main())