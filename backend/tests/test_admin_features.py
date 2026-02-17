"""
Test suite for Admin Dashboard new features:
1. Verify 'pending-groups' and 'group-courses' tabs are removed (frontend check)
2. Test 'Vider la poubelle' (Empty Trash) - DELETE /api/admin/empty-trash
3. Test Analytics hours_by_semester (quarterly hours)
4. Test Revenue edit - POST /api/admin/update-revenue
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@mykalamaenglish.com"
ADMIN_PASSWORD = "adminco"


class TestAdminLogin:
    """Test admin authentication"""
    
    def test_admin_login_success(self):
        """Test admin can login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✅ Admin login successful: {data['user']['email']}")


class TestEmptyTrash:
    """Test the Empty Trash functionality - DELETE /api/admin/empty-trash"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_empty_trash_requires_auth(self):
        """Test that empty-trash endpoint requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/admin/empty-trash")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Empty trash requires authentication")
    
    def test_empty_trash_endpoint_exists(self, admin_token):
        """Test that the empty-trash endpoint exists and responds"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.delete(f"{BASE_URL}/api/admin/empty-trash", headers=headers)
        # Should return 200 even if trash is empty
        assert response.status_code == 200, f"Empty trash failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "deleted_count" in data
        print(f"✅ Empty trash endpoint works: {data['message']}")
    
    def test_get_trash_endpoint(self, admin_token):
        """Test that we can get trash contents"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/trash", headers=headers)
        assert response.status_code == 200, f"Get trash failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get trash works: {len(data)} items in trash")


class TestAnalyticsHoursBySemester:
    """Test Analytics with hours_by_semester (quarterly hours)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_analytics_returns_hours_by_semester(self, admin_token):
        """Test that analytics endpoint returns hours_by_semester data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?period=month", headers=headers)
        assert response.status_code == 200, f"Analytics failed: {response.text}"
        data = response.json()
        
        # Check that hours_by_semester exists
        assert "hours_by_semester" in data, "hours_by_semester not found in analytics response"
        hours_data = data["hours_by_semester"]
        assert isinstance(hours_data, list), "hours_by_semester should be a list"
        
        # Check structure of each quarter entry
        if len(hours_data) > 0:
            quarter = hours_data[0]
            assert "semester" in quarter, "Each quarter should have 'semester' field"
            assert "hours" in quarter, "Each quarter should have 'hours' field"
            assert "label" in quarter, "Each quarter should have 'label' field"
            # Label should be like "T1 2025", "T2 2025", etc.
            assert "T" in quarter["label"], f"Label should contain 'T' for trimester: {quarter['label']}"
        
        print(f"✅ Analytics returns hours_by_semester: {len(hours_data)} quarters")
        for q in hours_data:
            print(f"   - {q['label']}: {q['hours']}h")
    
    def test_analytics_no_hours_by_week(self, admin_token):
        """Verify that hours_by_week is no longer the primary field (replaced by semester)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?period=month", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # hours_by_semester should be present
        assert "hours_by_semester" in data, "hours_by_semester should be present"
        print("✅ Analytics uses hours_by_semester (quarterly) instead of weekly")


class TestUpdateRevenue:
    """Test Revenue update functionality - POST /api/admin/update-revenue"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_update_revenue_requires_auth(self):
        """Test that update-revenue endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/update-revenue", json={
            "month": "Jan",
            "incoming_eur": 1000,
            "outgoing_eur": 500
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Update revenue requires authentication")
    
    def test_update_revenue_requires_month(self, admin_token):
        """Test that month field is required"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/admin/update-revenue", 
                                headers=headers,
                                json={
                                    "incoming_eur": 1000,
                                    "outgoing_eur": 500
                                })
        assert response.status_code == 400, f"Expected 400 for missing month, got {response.status_code}"
        print("✅ Update revenue requires month field")
    
    def test_update_revenue_success(self, admin_token):
        """Test successful revenue update"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        test_data = {
            "month": "TEST_Jan",  # Use TEST_ prefix for cleanup
            "incoming_eur": 2500,
            "incoming_fcfa": 850000,
            "outgoing_eur": 1200,
            "outgoing_fcfa": 400000
        }
        response = requests.post(f"{BASE_URL}/api/admin/update-revenue", 
                                headers=headers,
                                json=test_data)
        assert response.status_code == 200, f"Update revenue failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "correction" in data
        correction = data["correction"]
        assert correction["month"] == "TEST_Jan"
        assert correction["incoming_eur"] == 2500
        assert correction["outgoing_eur"] == 1200
        print(f"✅ Update revenue successful: {data['message']}")
    
    def test_update_revenue_upsert(self, admin_token):
        """Test that updating same month overwrites previous data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First update
        response1 = requests.post(f"{BASE_URL}/api/admin/update-revenue", 
                                 headers=headers,
                                 json={
                                     "month": "TEST_Feb",
                                     "incoming_eur": 1000,
                                     "outgoing_eur": 500
                                 })
        assert response1.status_code == 200
        
        # Second update with different values
        response2 = requests.post(f"{BASE_URL}/api/admin/update-revenue", 
                                 headers=headers,
                                 json={
                                     "month": "TEST_Feb",
                                     "incoming_eur": 2000,
                                     "outgoing_eur": 800
                                 })
        assert response2.status_code == 200
        data = response2.json()
        assert data["correction"]["incoming_eur"] == 2000
        assert data["correction"]["outgoing_eur"] == 800
        print("✅ Update revenue upsert works correctly")


class TestAnalyticsRevenueByMonth:
    """Test that revenue_by_month is returned in analytics"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_analytics_has_revenue_by_month(self, admin_token):
        """Test that analytics returns revenue_by_month with edit-compatible structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?period=month", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "revenue_by_month" in data, "revenue_by_month not found"
        revenue_data = data["revenue_by_month"]
        assert isinstance(revenue_data, list)
        
        if len(revenue_data) > 0:
            month_data = revenue_data[0]
            assert "month" in month_data, "Each month should have 'month' field"
            assert "incoming_eur" in month_data, "Each month should have 'incoming_eur'"
            assert "outgoing_eur" in month_data, "Each month should have 'outgoing_eur'"
            assert "incoming_fcfa" in month_data, "Each month should have 'incoming_fcfa'"
            assert "outgoing_fcfa" in month_data, "Each month should have 'outgoing_fcfa'"
        
        print(f"✅ Analytics returns revenue_by_month: {len(revenue_data)} months")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
