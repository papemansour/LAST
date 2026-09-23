"""Tests for new Secretary STAFF endpoints (all-staff, staff-payments, staff-leaves)."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-tracker-698.preview.emergentagent.com').rstrip('/')

SECRETARY_EMAIL = "secretaire@mykalamaenglish.com"
SECRETARY_PASSWORD = "kalamasecret"


@pytest.fixture(scope="module")
def secretary_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": SECRETARY_EMAIL, "password": SECRETARY_PASSWORD},
                      timeout=15)
    assert r.status_code == 200, f"Secretary login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def sec_client(secretary_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {secretary_token}"})
    return s


class TestAllStaff:
    def test_get_all_staff(self, sec_client):
        r = sec_client.get(f"{BASE_URL}/api/secretary/all-staff", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Expected at least one staff member"
        member = data[0]
        for k in ("id", "name", "role", "leaves_used", "leaves_total"):
            assert k in member, f"Missing key {k} in staff: {member}"
        assert member["leaves_total"] == 30

    def test_all_staff_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/secretary/all-staff", timeout=15)
        assert r.status_code in (401, 403)


class TestStaffPayments:
    created_id = None

    def test_get_staff_payments(self, sec_client):
        r = sec_client.get(f"{BASE_URL}/api/secretary/staff-payments", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_staff_payment_and_persist(self, sec_client):
        payload = {
            "staffId": "MBM",
            "staffName": "TEST_MBM Staff",
            "staffRole": "communication",
            "month": "2026-01",
            "amount": 400,
            "bonus": 50,
            "deductions": 2,
            "currency": "EUR",
            "description": "TEST_ staff payment"
        }
        r = sec_client.post(f"{BASE_URL}/api/secretary/staff-payments",
                            json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["montant_net"] == 400 + 50 - (2 * 5)  # 440
        assert body.get("invoice_ref", "").startswith("STAFF-")
        TestStaffPayments.created_id = body["id"]

        # Verify persistence via GET
        r2 = sec_client.get(f"{BASE_URL}/api/secretary/staff-payments", timeout=15)
        assert r2.status_code == 200
        ids = [p["id"] for p in r2.json()]
        assert body["id"] in ids

    def test_delete_staff_payment(self, sec_client):
        pid = TestStaffPayments.created_id
        assert pid, "No payment id captured"
        r = sec_client.delete(f"{BASE_URL}/api/secretary/staff-payments/{pid}", timeout=15)
        assert r.status_code == 200
        # verify gone
        r2 = sec_client.get(f"{BASE_URL}/api/secretary/staff-payments", timeout=15)
        assert pid not in [p["id"] for p in r2.json()]


class TestStaffLeaves:
    created_id = None

    def test_get_staff_leaves(self, sec_client):
        r = sec_client.get(f"{BASE_URL}/api/secretary/staff-leaves", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_staff_leave_and_persist(self, sec_client):
        payload = {
            "staffId": "MBM",
            "staffName": "TEST_MBM Staff",
            "startDate": "2026-02-01",
            "endDate": "2026-02-05",
            "daysUsed": 5,
            "reason": "TEST_ conge"
        }
        r = sec_client.post(f"{BASE_URL}/api/secretary/staff-leaves",
                            json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["days_used"] == 5
        assert "id" in body
        TestStaffLeaves.created_id = body["id"]

        r2 = sec_client.get(f"{BASE_URL}/api/secretary/staff-leaves", timeout=15)
        assert r2.status_code == 200
        found = [x for x in r2.json() if x["id"] == body["id"]]
        assert found, "Created leave not returned by GET"
        assert found[0]["days_used"] == 5
        assert found[0]["status"] == "approved"

    def test_delete_staff_leave(self, sec_client):
        lid = TestStaffLeaves.created_id
        assert lid
        r = sec_client.delete(f"{BASE_URL}/api/secretary/staff-leaves/{lid}", timeout=15)
        assert r.status_code == 200
        r2 = sec_client.get(f"{BASE_URL}/api/secretary/staff-leaves", timeout=15)
        assert lid not in [x["id"] for x in r2.json()]
