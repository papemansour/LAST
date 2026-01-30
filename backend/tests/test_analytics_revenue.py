"""
Test suite for Admin Analytics Revenue Separation Feature
Tests the new incoming/outgoing revenue separation in /admin/analytics endpoint
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminAnalyticsRevenue:
    """Test Admin Analytics endpoint with revenue separation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.teacher_token = None
    
    def test_admin_login_success(self):
        """Test admin login to get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@mykalamaenglish.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        self.admin_token = data["access_token"]
        return self.admin_token
    
    def test_teacher_login_success(self):
        """Test teacher login to get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "proftest.flashcards@mykalamaenglish.com",
            "password": "teacher123"
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        self.teacher_token = data["access_token"]
        return self.teacher_token
    
    def test_admin_analytics_returns_revenue_separation(self):
        """Test that /admin/analytics returns incoming_eur, outgoing_eur, net_eur in summary"""
        # Login as admin
        admin_token = self.test_admin_login_success()
        
        # Get analytics
        response = self.session.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Analytics request failed: {response.text}"
        data = response.json()
        
        # Verify summary contains new revenue fields
        assert "summary" in data, "Response should contain 'summary'"
        summary = data["summary"]
        
        # Check for new revenue separation fields
        assert "incoming_eur" in summary, "Summary should contain 'incoming_eur'"
        assert "outgoing_eur" in summary, "Summary should contain 'outgoing_eur'"
        assert "net_eur" in summary, "Summary should contain 'net_eur'"
        assert "incoming_fcfa" in summary, "Summary should contain 'incoming_fcfa'"
        assert "outgoing_fcfa" in summary, "Summary should contain 'outgoing_fcfa'"
        assert "net_fcfa" in summary, "Summary should contain 'net_fcfa'"
        
        # Verify net calculation is correct
        expected_net_eur = summary["incoming_eur"] - summary["outgoing_eur"]
        assert summary["net_eur"] == expected_net_eur, f"Net EUR calculation incorrect: {summary['net_eur']} != {expected_net_eur}"
        
        expected_net_fcfa = summary["incoming_fcfa"] - summary["outgoing_fcfa"]
        assert summary["net_fcfa"] == expected_net_fcfa, f"Net FCFA calculation incorrect: {summary['net_fcfa']} != {expected_net_fcfa}"
        
        print(f"✓ Summary revenue fields verified:")
        print(f"  - incoming_eur: {summary['incoming_eur']}")
        print(f"  - outgoing_eur: {summary['outgoing_eur']}")
        print(f"  - net_eur: {summary['net_eur']}")
    
    def test_admin_analytics_revenue_by_month_structure(self):
        """Test that revenue_by_month contains incoming/outgoing for each month"""
        # Login as admin
        admin_token = self.test_admin_login_success()
        
        # Get analytics
        response = self.session.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify revenue_by_month structure
        assert "revenue_by_month" in data, "Response should contain 'revenue_by_month'"
        revenue_by_month = data["revenue_by_month"]
        
        assert len(revenue_by_month) > 0, "revenue_by_month should not be empty"
        
        # Check each month entry has the correct structure
        for month_data in revenue_by_month:
            assert "month" in month_data, "Each month should have 'month' field"
            assert "incoming_eur" in month_data, "Each month should have 'incoming_eur'"
            assert "incoming_fcfa" in month_data, "Each month should have 'incoming_fcfa'"
            assert "outgoing_eur" in month_data, "Each month should have 'outgoing_eur'"
            assert "outgoing_fcfa" in month_data, "Each month should have 'outgoing_fcfa'"
            
            # Verify values are numbers
            assert isinstance(month_data["incoming_eur"], (int, float)), "incoming_eur should be numeric"
            assert isinstance(month_data["outgoing_eur"], (int, float)), "outgoing_eur should be numeric"
        
        print(f"✓ revenue_by_month structure verified with {len(revenue_by_month)} months")
        for m in revenue_by_month:
            print(f"  - {m['month']}: +{m['incoming_eur']}€ / -{m['outgoing_eur']}€")
    
    def test_admin_analytics_requires_admin_role(self):
        """Test that non-admin users cannot access analytics"""
        # Login as teacher
        teacher_token = self.test_teacher_login_success()
        
        # Try to access analytics
        response = self.session.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 403, f"Teacher should not access admin analytics: {response.status_code}"
        print("✓ Non-admin access correctly denied")
    
    def test_admin_analytics_requires_auth(self):
        """Test that unauthenticated requests are rejected"""
        response = self.session.get(f"{BASE_URL}/api/admin/analytics?period=month")
        
        assert response.status_code in [401, 403], f"Unauthenticated request should be rejected: {response.status_code}"
        print("✓ Unauthenticated access correctly denied")
    
    def test_admin_analytics_different_periods(self):
        """Test analytics with different period parameters"""
        admin_token = self.test_admin_login_success()
        
        for period in ["week", "month", "year"]:
            response = self.session.get(
                f"{BASE_URL}/api/admin/analytics?period={period}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200, f"Analytics for period '{period}' failed: {response.text}"
            data = response.json()
            
            # Verify structure is consistent across periods
            assert "summary" in data
            assert "revenue_by_month" in data
            assert "incoming_eur" in data["summary"]
            assert "outgoing_eur" in data["summary"]
            assert "net_eur" in data["summary"]
            
            print(f"✓ Period '{period}' returns valid data")
    
    def test_admin_analytics_no_old_revenue_field(self):
        """Test that old 'revenue_eur' field is not present (replaced by incoming/outgoing)"""
        admin_token = self.test_admin_login_success()
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/analytics?period=month",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Old field should not exist
        assert "revenue_eur" not in data["summary"], "Old 'revenue_eur' field should be removed"
        
        # New fields should exist
        assert "incoming_eur" in data["summary"], "New 'incoming_eur' field should exist"
        assert "outgoing_eur" in data["summary"], "New 'outgoing_eur' field should exist"
        
        print("✓ Old revenue_eur field correctly replaced with incoming/outgoing")


class TestTeacherDashboardNoCoursesTab:
    """Test that 'Cours' tab is removed from teacher dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_teacher_login_success(self):
        """Test teacher login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "proftest.flashcards@mykalamaenglish.com",
            "password": "teacher123"
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_teacher_my_courses_endpoint_still_works(self):
        """Test that /teacher/my-courses endpoint still works (even if tab removed)"""
        teacher_token = self.test_teacher_login_success()
        
        response = self.session.get(
            f"{BASE_URL}/api/teacher/my-courses",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # Endpoint should still work
        assert response.status_code == 200, f"Teacher courses endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ /teacher/my-courses endpoint works, returns {len(data)} courses")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
