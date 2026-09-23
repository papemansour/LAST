"""
Backend tests for:
- Communication staff endpoints (payments, notes, leaves, availability, stats)
- Secretary/Admin update-user and delete-user endpoints (Teacher edit/delete)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://attendance-tracker-698.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@mykalamaenglish.com", "password": "adminco"}
SECRETARY = {"email": "secretaire@mykalamaenglish.com", "password": "kalamasecret"}
COMMUNICATION = {"email": "com@mykalamaenglish.com", "password": "COMKALAMA"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"No token returned: {data}"
    return tok, data


@pytest.fixture(scope="module")
def admin_token():
    tok, _ = _login(ADMIN)
    return tok


@pytest.fixture(scope="module")
def secretary_token():
    tok, _ = _login(SECRETARY)
    return tok


@pytest.fixture(scope="module")
def com_token():
    tok, _ = _login(COMMUNICATION)
    return tok


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


# ==================== AUTH ====================
class TestAuth:
    def test_admin_login(self):
        tok, data = _login(ADMIN)
        assert tok
        # user role should be admin
        user = data.get("user", {})
        assert user.get("role") == "admin"

    def test_secretary_login(self):
        tok, data = _login(SECRETARY)
        assert tok
        assert data.get("user", {}).get("role") == "secretary"

    def test_communication_login(self):
        tok, data = _login(COMMUNICATION)
        assert tok
        assert data.get("user", {}).get("role") == "communication"


# ==================== COMMUNICATION ====================
class TestCommunicationDashboard:
    def test_stats(self, com_token):
        r = requests.get(f"{API}/communication/stats", headers=H(com_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "totalStudents" in d and "totalTeachers" in d and "totalNews" in d

    def test_invalid_com_code_rejected(self, com_token):
        r = requests.get(f"{API}/communication/balance/XXX", headers=H(com_token), timeout=20)
        assert r.status_code == 400

    def test_balance_mbm_empty_or_valid(self, com_token):
        r = requests.get(f"{API}/communication/balance/MBM", headers=H(com_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["pendingAmount", "paidAmount", "totalHours", "payments"]:
            assert k in d
        assert isinstance(d["payments"], list)

    def test_set_and_get_availability_mbm(self, com_token):
        av = {"lundi": ["09:00", "10:00"], "mardi": ["14:00"]}
        r = requests.post(
            f"{API}/communication/set-availability",
            headers=H(com_token),
            json={"com_code": "MBM", "availability": av},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        # GET
        r = requests.get(f"{API}/communication/my-availability/MBM", headers=H(com_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("com_code") == "MBM"
        assert d.get("availability", {}).get("lundi") == ["09:00", "10:00"]

    def test_notes_crud(self, com_token):
        # Create
        r = requests.post(
            f"{API}/communication/notes",
            headers=H(com_token),
            json={"com_code": "MBM", "title": "TEST_Note", "content": "Contenu test"},
            timeout=20,
        )
        assert r.status_code == 200
        note_id = r.json().get("id")
        assert note_id
        # List
        r = requests.get(f"{API}/communication/notes/MBM", headers=H(com_token), timeout=20)
        assert r.status_code == 200
        notes = r.json()
        assert any(n.get("id") == note_id for n in notes)
        found = next(n for n in notes if n.get("id") == note_id)
        assert found["title"] == "TEST_Note"
        # Delete
        r = requests.delete(f"{API}/communication/notes/{note_id}", headers=H(com_token), timeout=20)
        assert r.status_code == 200

    def test_leaves_create_and_list(self, com_token):
        r = requests.post(
            f"{API}/communication/leaves",
            headers=H(com_token),
            json={
                "com_code": "MBM",
                "start_date": "2026-02-01",
                "end_date": "2026-02-03",
                "reason": "TEST_conge",
            },
            timeout=20,
        )
        assert r.status_code == 200
        leave_id = r.json().get("id")
        assert leave_id
        r = requests.get(f"{API}/communication/leaves/MBM", headers=H(com_token), timeout=20)
        assert r.status_code == 200
        leaves = r.json()
        found = next((l for l in leaves if l.get("id") == leave_id), None)
        assert found is not None
        assert found["status"] == "pending"

    def test_admin_creates_payment_for_com(self, admin_token, com_token):
        payload = {
            "com_code": "MBM",
            "month": "Janvier",
            "year": 2026,
            "amount": 250.5,
            "hours": 20,
            "status": "pending",
            "notes": "TEST_payment",
        }
        r = requests.post(f"{API}/communication/payments", headers=H(admin_token), json=payload, timeout=20)
        assert r.status_code == 200, r.text
        pay_id = r.json().get("id")
        assert pay_id
        # Verify via balance GET
        r = requests.get(f"{API}/communication/balance/MBM", headers=H(com_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert any(p.get("id") == pay_id and p.get("amount") == 250.5 for p in d["payments"])
        # Mark as paid
        r = requests.put(
            f"{API}/communication/payments/{pay_id}/status",
            headers=H(admin_token),
            json={"status": "paid"},
            timeout=20,
        )
        assert r.status_code == 200

    def test_com_cannot_create_payment(self, com_token):
        r = requests.post(
            f"{API}/communication/payments",
            headers=H(com_token),
            json={"com_code": "MBM", "amount": 100},
            timeout=20,
        )
        assert r.status_code == 403


# ==================== SECRETARY: TEACHER EDIT/DELETE ====================
class TestSecretaryTeacherManagement:
    def test_secretary_can_list_teachers(self, secretary_token):
        r = requests.get(f"{API}/admin/all-teachers-detailed", headers=H(secretary_token), timeout=20)
        assert r.status_code == 200
        teachers = r.json()
        assert isinstance(teachers, list)

    def test_secretary_updates_teacher(self, admin_token, secretary_token):
        # Create a teacher via admin
        first = f"TESTteach{int(time.time())}"
        r = requests.post(
            f"{API}/admin/create-teacher",
            headers=H(admin_token),
            json={"first_name": first, "last_name": "AutoTest"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        email = r.json()["email"]
        # Get teacher id
        r = requests.get(f"{API}/admin/all-teachers-detailed", headers=H(secretary_token), timeout=20)
        teachers = r.json()
        t = next((x for x in teachers if x["email"] == email), None)
        assert t, f"teacher {email} not found"
        tid = t["user_id"]

        # Update as secretary
        new_phone = "+33111222333"
        new_last = "UpdatedName"
        r = requests.put(
            f"{API}/admin/update-user/{tid}",
            headers=H(secretary_token),
            json={"first_name": first, "last_name": new_last, "email": email, "phone": new_phone},
            timeout=20,
        )
        assert r.status_code == 200, r.text

        # Verify persistence
        r = requests.get(f"{API}/admin/all-teachers-detailed", headers=H(secretary_token), timeout=20)
        teachers = r.json()
        t2 = next((x for x in teachers if x["user_id"] == tid), None)
        assert t2 is not None
        assert t2["last_name"] == new_last
        assert t2["phone"] == new_phone

        # Cleanup: secretary deletes teacher
        r = requests.delete(f"{API}/admin/delete-user/{tid}", headers=H(secretary_token), timeout=20)
        assert r.status_code == 200

        # Verify teacher gone
        r = requests.get(f"{API}/admin/all-teachers-detailed", headers=H(secretary_token), timeout=20)
        teachers = r.json()
        assert not any(x["user_id"] == tid for x in teachers)

    def test_secretary_cannot_modify_admin(self, admin_token, secretary_token):
        # Get admin user id
        r = requests.get(f"{API}/admin/all-users", headers=H(admin_token), timeout=20)
        assert r.status_code == 200
        users = r.json()
        admin_user = next((u for u in users if u.get("role") == "admin"), None)
        assert admin_user is not None
        r = requests.put(
            f"{API}/admin/update-user/{admin_user['id']}",
            headers=H(secretary_token),
            json={"first_name": "Hacker"},
            timeout=20,
        )
        assert r.status_code == 403
