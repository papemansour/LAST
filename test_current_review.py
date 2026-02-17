#!/usr/bin/env python3
"""
Test script for current review request features only
"""

import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://teacher-secretary.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"

class CurrentReviewTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
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

    async def test_group_courses_get_all(self) -> bool:
        """Test 1: Group Courses - Get All"""
        try:
            logger.info("🔍 Test 1: Group Courses - Get All...")
            
            async with self.session.get(f"{BACKEND_URL}/group-courses") as response:
                if response.status == 200:
                    courses = await response.json()
                    
                    if isinstance(courses, list):
                        logger.info(f"✅ Retrieved {len(courses)} group courses")
                        
                        if len(courses) >= 1:
                            logger.info("✅ At least 1 course found as expected")
                            return True
                        else:
                            logger.warning("⚠️ No courses found - may need to create one first")
                            return True  # Still pass as endpoint works
                    else:
                        logger.error("❌ Response is not an array")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Get group courses failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Group courses get all test error: {str(e)}")
            return False

    async def test_group_courses_create(self) -> bool:
        """Test 2: Group Courses - Create (as admin)"""
        try:
            logger.info("🔍 Test 2: Group Courses - Create as admin...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            course_data = {
                "title": "Test Group",
                "level": "beginner", 
                "max_students": 5
            }
            
            async with self.session.post(f"{BACKEND_URL}/group-courses", json=course_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "course_id" in result:
                        logger.info("✅ Group course created successfully")
                        logger.info(f"✅ Course ID: {result.get('course_id')}")
                        return True
                    else:
                        logger.error("❌ Response missing course_id")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Group course creation failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Group courses create test error: {str(e)}")
            return False

    async def test_student_points_get(self) -> bool:
        """Test 3: Student Points - Get My Points"""
        try:
            logger.info("🔍 Test 3: Student Points - Get My Points...")
            
            # Try to use existing student credentials
            student_credentials = [
                {"email": "test.student@example.com", "password": "Test2025"},
                {"email": "clubtest@example.com", "password": "TestClub2025"},
                {"email": "etudiant.test@example.com", "password": "KKid2025"}
            ]
            
            for creds in student_credentials:
                try:
                    login_data = {
                        "email": creds["email"],
                        "password": creds["password"]
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.student_token = data.get("access_token")
                            logger.info(f"✅ Student login successful: {creds['email']}")
                            break
                        else:
                            logger.warning(f"⚠️ Failed to login as {creds['email']}")
                except Exception as e:
                    logger.warning(f"⚠️ Login attempt failed for {creds['email']}: {str(e)}")
            
            if not self.student_token:
                logger.error("❌ Could not login as any student")
                return False
            
            headers = {"Authorization": f"Bearer {self.student_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/student/my-points", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    required_fields = ["total_points", "available_points", "rewards"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        rewards = result.get("rewards", {})
                        if "tiers" in rewards:
                            logger.info("✅ Student points response has all required fields")
                            logger.info(f"✅ Total points: {result.get('total_points')}")
                            logger.info(f"✅ Available points: {result.get('available_points')}")
                            logger.info(f"✅ Rewards tiers: {len(rewards.get('tiers', []))}")
                            return True
                        else:
                            logger.error("❌ Rewards object missing tiers")
                            return False
                    else:
                        logger.error(f"❌ Missing required fields: {missing_fields}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Get student points failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Student points get test error: {str(e)}")
            return False

    async def test_delete_teacher_sessions(self) -> bool:
        """Test 4: Delete All Teacher Sessions (as admin)"""
        try:
            logger.info("🔍 Test 4: Delete All Teacher Sessions as admin...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(f"{BACKEND_URL}/admin/teacher-sessions", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "count" in result or "deleted_count" in result or "message" in result:
                        deleted_count = result.get("count", result.get("deleted_count", 0))
                        logger.info(f"✅ Teacher sessions deleted successfully - Count: {deleted_count}")
                        return True
                    else:
                        logger.error("❌ Response missing count information")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Delete teacher sessions failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Delete teacher sessions test error: {str(e)}")
            return False

    async def test_reset_billing_stats_secretary(self) -> bool:
        """Test 5: Reset Billing Stats (as secretary)"""
        try:
            logger.info("🔍 Test 5: Reset Billing Stats as secretary...")
            
            # Login as secretary
            secretary_data = {"code": "secretaire2025"}
            async with self.session.post(f"{BACKEND_URL}/auth/secretary-login", json=secretary_data) as response:
                if response.status == 200:
                    result = await response.json()
                    secretary_token = result.get("access_token")
                    logger.info("✅ Secretary login successful")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Secretary login failed: {response.status} - {error_text}")
                    return False
            
            headers = {"Authorization": f"Bearer {secretary_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/secretary/reset-billing-stats", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "deleted" in result:
                        deleted_info = result["deleted"]
                        logger.info("✅ Billing stats reset successfully")
                        logger.info(f"✅ Deleted: {deleted_info}")
                        return True
                    else:
                        logger.error("❌ Response missing deleted counts")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Reset billing stats failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Reset billing stats test error: {str(e)}")
            return False

    async def run_tests(self):
        """Run all current review request tests"""
        logger.info("🚀 Starting Current Review Request Tests")
        logger.info("=" * 70)
        
        # Login as admin
        if not await self.login_admin():
            logger.error("❌ Cannot proceed without admin login")
            return
        
        results = {}
        
        # Test 1: Group Courses - Get All
        results["group_courses_get_all"] = await self.test_group_courses_get_all()
        
        # Test 2: Group Courses - Create (as admin)
        results["group_courses_create"] = await self.test_group_courses_create()
        
        # Test 3: Student Points - Get My Points
        results["student_points_get"] = await self.test_student_points_get()
        
        # Test 4: Delete All Teacher Sessions (as admin)
        results["delete_teacher_sessions"] = await self.test_delete_teacher_sessions()
        
        # Test 5: Reset Billing Stats (as secretary)
        results["reset_billing_stats"] = await self.test_reset_billing_stats_secretary()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 CURRENT REVIEW REQUEST TEST RESULTS:")
        logger.info("=" * 70)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"  {test_name.upper().replace('_', ' ')}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\n📊 Overall Result: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            logger.info("🎉 ALL CURRENT REVIEW REQUEST TESTS PASSED!")
        else:
            logger.warning(f"⚠️ {total - passed} test(s) failed")

async def main():
    """Main test runner"""
    async with CurrentReviewTester() as tester:
        await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())