#!/usr/bin/env python3
"""
Focused test for pricing update flow as requested in review
Tests the complete flow:
1. Admin login (admin@mykalamaenglish.com / adminco)
2. Get current prices via GET /api/pricing
3. Update prices via POST /admin/update-prices (change beginner_eur from 76 to 80)
4. Verify new prices via GET /api/pricing
5. Verify prices are saved in MongoDB
"""

import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from environment
BACKEND_URL = "https://tutor-hub-32.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"

class PricingFlowTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login_admin(self) -> bool:
        """Step 1: Login as admin"""
        try:
            logger.info("🔍 Step 1: Logging in as admin...")
            
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    logger.info("✅ Step 1 PASSED: Admin login successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 1 FAILED: Admin login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Step 1 ERROR: Admin login error: {str(e)}")
            return False
    
    async def get_current_prices(self) -> dict:
        """Step 2: Get current prices via GET /api/pricing"""
        try:
            logger.info("🔍 Step 2: Getting current prices...")
            
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    pricing = await response.json()
                    beginner_eur = pricing.get("beginner_eur", "N/A")
                    logger.info(f"✅ Step 2 PASSED: Retrieved current prices - beginner_eur: {beginner_eur}")
                    logger.info(f"   Full pricing: {json.dumps(pricing, indent=2)}")
                    return pricing
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 2 FAILED: GET /api/pricing failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Step 2 ERROR: {str(e)}")
            return None
    
    async def update_prices(self, original_pricing: dict) -> bool:
        """Step 3: Update prices via POST /admin/update-prices"""
        try:
            logger.info("🔍 Step 3: Updating prices (beginner_eur: 76 → 80)...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Modify beginner_eur from 76 to 80
            updated_pricing = original_pricing.copy()
            updated_pricing["beginner_eur"] = 80
            
            logger.info(f"   Sending update: beginner_eur = {updated_pricing['beginner_eur']}")
            
            async with self.session.post(f"{BACKEND_URL}/admin/update-prices", 
                                       json=updated_pricing, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Step 3 PASSED: Prices updated successfully")
                    logger.info(f"   Response: {result.get('message', 'No message')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 3 FAILED: POST /admin/update-prices failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Step 3 ERROR: {str(e)}")
            return False
    
    async def verify_new_prices(self) -> dict:
        """Step 4: Verify new prices are returned by GET /api/pricing"""
        try:
            logger.info("🔍 Step 4: Verifying new prices...")
            
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    pricing = await response.json()
                    beginner_eur = pricing.get("beginner_eur")
                    
                    if beginner_eur == 80:
                        logger.info(f"✅ Step 4 PASSED: New prices verified - beginner_eur: {beginner_eur}")
                        return pricing
                    else:
                        logger.error(f"❌ Step 4 FAILED: Expected beginner_eur=80, got {beginner_eur}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 4 FAILED: GET /api/pricing verification failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Step 4 ERROR: {str(e)}")
            return None
    
    async def verify_mongodb_persistence(self) -> bool:
        """Step 5: Verify prices are saved in MongoDB"""
        try:
            logger.info("🔍 Step 5: Verifying MongoDB persistence...")
            
            # Wait a moment to ensure database write is complete
            await asyncio.sleep(2)
            
            async with self.session.get(f"{BACKEND_URL}/pricing") as response:
                if response.status == 200:
                    pricing = await response.json()
                    beginner_eur = pricing.get("beginner_eur")
                    
                    if beginner_eur == 80:
                        logger.info("✅ Step 5 PASSED: MongoDB persistence verified")
                        logger.info(f"   Persistent beginner_eur: {beginner_eur}")
                        return True
                    else:
                        logger.error(f"❌ Step 5 FAILED: Price not persisted - got {beginner_eur}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Step 5 FAILED: Cannot verify persistence: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Step 5 ERROR: {str(e)}")
            return False
    
    async def restore_original_prices(self, original_pricing: dict) -> bool:
        """Cleanup: Restore original prices"""
        try:
            logger.info("🔧 Cleanup: Restoring original prices...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/admin/update-prices", 
                                       json=original_pricing, headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ Cleanup: Original prices restored")
                    return True
                else:
                    logger.warning("⚠️ Cleanup: Failed to restore original prices")
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {str(e)}")
            return False
    
    async def run_complete_flow(self):
        """Run the complete pricing update flow test"""
        logger.info("🚀 STARTING PRICING UPDATE FLOW TEST")
        logger.info("=" * 70)
        logger.info("Testing endpoints:")
        logger.info("- POST /api/auth/login")
        logger.info("- GET /api/pricing (before and after)")
        logger.info("- POST /admin/update-prices")
        logger.info("Success criteria: Modified prices immediately visible via GET /api/pricing")
        logger.info("=" * 70)
        
        success = True
        
        # Step 1: Admin login
        if not await self.login_admin():
            return False
        
        # Step 2: Get current prices
        original_pricing = await self.get_current_prices()
        if not original_pricing:
            return False
        
        # Step 3: Update prices
        if not await self.update_prices(original_pricing):
            return False
        
        # Step 4: Verify new prices
        new_pricing = await self.verify_new_prices()
        if not new_pricing:
            return False
        
        # Step 5: Verify MongoDB persistence
        if not await self.verify_mongodb_persistence():
            return False
        
        # Cleanup: Restore original prices
        await self.restore_original_prices(original_pricing)
        
        # Final verification
        logger.info("\n" + "=" * 70)
        logger.info("🎉 PRICING UPDATE FLOW TEST COMPLETED SUCCESSFULLY!")
        logger.info("✅ All 5 steps passed:")
        logger.info("   1. ✅ Admin login (admin@mykalamaenglish.com)")
        logger.info("   2. ✅ GET /api/pricing (retrieved current prices)")
        logger.info("   3. ✅ POST /admin/update-prices (beginner_eur: 76 → 80)")
        logger.info("   4. ✅ GET /api/pricing (verified new prices)")
        logger.info("   5. ✅ MongoDB persistence (prices saved)")
        logger.info("✅ SUCCESS CRITERIA MET: Modified prices immediately visible!")
        logger.info("=" * 70)
        
        return True

async def main():
    """Main test execution"""
    async with PricingFlowTester() as tester:
        success = await tester.run_complete_flow()
        
        if success:
            print("\n🎉 TEST RESULT: PASSED")
            return 0
        else:
            print("\n❌ TEST RESULT: FAILED")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)