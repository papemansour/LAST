"""
Backend tests for the Prestataire (Contractor) system.
Covers: register, login, facture submission, secretary search/pay, HR sub-tab data.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to frontend .env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass

API = f"{BASE_URL}/api"

SECRETARY_EMAIL = "secretaire@mykalamaenglish.com"
SECRETARY_PASSWORD = "kalamasecret"


# ---- Fixtures ----
@pytest.fixture(scope="module")
def secretary_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": SECRETARY_EMAIL, "password": SECRETARY_PASSWORD
    }, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Secretary login failed: {r.status_code} {r.text}")
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def sec_headers(secretary_token):
    return {"Authorization": f"Bearer {secretary_token}"}


@pytest.fixture(scope="module")
def new_prestataire():
    ts = int(time.time())
    payload = {
        "first_name": "TEST",
        "last_name": "Prestataire",
        "email": f"TEST_prest_{ts}@example.com",
        "phone": "+33600000000",
        "company_name": f"TEST_Company_{ts}",
        "services": "Design graphique, dev web"
    }
    r = requests.post(f"{API}/prestataire/register", json=payload, timeout=20)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    data = r.json()
    assert "prestataire_code" in data
    return {"payload": payload, "prestataire_code": data["prestataire_code"]}


# ---- Registration ----
class TestPrestataireRegistration:
    def test_register_missing_fields(self):
        r = requests.post(f"{API}/prestataire/register", json={"first_name": "x"}, timeout=15)
        assert r.status_code == 400

    def test_register_duplicate_email(self, new_prestataire):
        r = requests.post(f"{API}/prestataire/register",
                          json=new_prestataire["payload"], timeout=15)
        assert r.status_code == 400
        assert "existe" in r.text.lower() or "exist" in r.text.lower()


# ---- Login flow (need access_code, which is only sent by email) ----
class TestPrestataireLogin:
    def test_login_invalid_code(self):
        r = requests.post(f"{API}/prestataire/login",
                          json={"access_code": "INVALID9"}, timeout=15)
        assert r.status_code == 401

    def test_login_missing_code(self):
        r = requests.post(f"{API}/prestataire/login", json={}, timeout=15)
        assert r.status_code == 400


# ---- Facture submission using prestataire_code (public) ----
class TestFactureSubmission:
    def test_submit_facture(self, new_prestataire):
        r = requests.post(f"{API}/prestataire/facture", json={
            "prestataire_code": new_prestataire["prestataire_code"],
            "amount": 250.50,
            "conception_time": "20 heures",
            "services": "Design",
            "description": "Test facture"
        }, timeout=15)
        assert r.status_code == 200, r.text
        assert "facture_id" in r.json()

    def test_submit_facture_invalid_code(self):
        r = requests.post(f"{API}/prestataire/facture", json={
            "prestataire_code": "NOTREAL",
            "amount": 10.0,
            "conception_time": "1h"
        }, timeout=15)
        assert r.status_code == 404

    def test_submit_facture_missing_fields(self, new_prestataire):
        r = requests.post(f"{API}/prestataire/facture", json={
            "prestataire_code": new_prestataire["prestataire_code"]
        }, timeout=15)
        assert r.status_code == 400

    def test_my_factures(self, new_prestataire):
        r = requests.get(
            f"{API}/prestataire/my-factures/{new_prestataire['prestataire_code']}",
            timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["prestataire_code"] == new_prestataire["prestataire_code"]


# ---- Secretary endpoints ----
class TestSecretaryPrestataireRoutes:
    def test_all_prestataires(self, sec_headers, new_prestataire):
        r = requests.get(f"{API}/secretary/all-prestataires",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200, r.text
        codes = [p["prestataire_code"] for p in r.json()]
        assert new_prestataire["prestataire_code"] in codes

    def test_get_by_code(self, sec_headers, new_prestataire):
        code = new_prestataire["prestataire_code"]
        r = requests.get(f"{API}/secretary/prestataire/{code}",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "prestataire" in data and "pending_factures" in data
        assert data["prestataire"]["prestataire_code"] == code
        # access_code should NOT leak
        assert "access_code" not in data["prestataire"]
        assert len(data["pending_factures"]) >= 1

    def test_get_by_invalid_code(self, sec_headers):
        r = requests.get(f"{API}/secretary/prestataire/BOGUS9",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 404

    def test_get_by_code_requires_auth(self):
        r = requests.get(f"{API}/secretary/prestataire/ABC123", timeout=15)
        assert r.status_code in (401, 403)

    def test_all_factures(self, sec_headers):
        r = requests.get(f"{API}/secretary/prestataire-factures",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_pay_facture(self, sec_headers, new_prestataire):
        code = new_prestataire["prestataire_code"]
        # find a pending facture id
        r = requests.get(f"{API}/secretary/prestataire/{code}",
                         headers=sec_headers, timeout=15)
        pendings = r.json()["pending_factures"]
        assert len(pendings) > 0
        fid = pendings[0]["id"]

        r2 = requests.post(f"{API}/secretary/pay-facture/{fid}",
                           headers=sec_headers, timeout=15)
        assert r2.status_code == 200, r2.text

        # second time should 400 (already paid)
        r3 = requests.post(f"{API}/secretary/pay-facture/{fid}",
                           headers=sec_headers, timeout=15)
        assert r3.status_code == 400

    def test_pay_facture_not_found(self, sec_headers):
        r = requests.post(f"{API}/secretary/pay-facture/nonexistent-id",
                          headers=sec_headers, timeout=15)
        assert r.status_code == 404


# ---- Secretary HR endpoints ----
class TestSecretaryHR:
    def test_leave_balances(self, sec_headers):
        r = requests.get(f"{API}/admin/leave-balances",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_availability_calendar(self, sec_headers):
        r = requests.get(f"{API}/admin/availability-calendar",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200

    def test_all_teachers_detailed(self, sec_headers):
        r = requests.get(f"{API}/admin/all-teachers-detailed",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200
        teachers = r.json()
        assert isinstance(teachers, list)
        if teachers:
            t = teachers[0]
            for k in ("first_name", "last_name", "email", "months_worked"):
                assert k in t, f"missing key {k} in teacher fiche: {t.keys()}"

    def test_all_students(self, sec_headers):
        r = requests.get(f"{API}/admin/all-students",
                         headers=sec_headers, timeout=15)
        assert r.status_code == 200
        students = r.json()
        assert isinstance(students, list)
        if students:
            s = students[0]
            for k in ("first_name", "last_name", "email"):
                assert k in s
            assert "level" in s or "pack" in s, f"no level/pack field: {s.keys()}"
