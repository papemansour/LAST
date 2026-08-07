"""Regression tests for leave balances, employee access, and intermediate MCQs."""
from datetime import datetime, timezone
import os
from uuid import uuid4

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL is missing")
BASE_URL = base_url.rstrip("/")

ADMIN_CREDENTIALS = {
    "email": "admin@mykalamaenglish.com",
    "password": "adminco",
}
SECRETARY_CODE = "secretaire2025"


def _login(payload, endpoint="/api/auth/login"):
    response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=30)
    if response.status_code != 200:
        pytest.fail(f"Authentication failed at {endpoint}: {response.status_code} {response.text[:300]}")
    data = response.json()
    assert isinstance(data.get("access_token"), str) and data["access_token"]
    assert isinstance(data.get("user"), dict)
    return data


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _expected_earned(start_date):
    parsed = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    months = max(0, (now.year - parsed.year) * 12 + now.month - parsed.month)
    return months, min(30.0, round(months * 2.5, 1))


@pytest.fixture(scope="session")
def admin_auth():
    data = _login(ADMIN_CREDENTIALS)
    assert data["user"]["role"] == "admin"
    return data


@pytest.fixture(scope="session")
def secretary_auth():
    data = _login({"code": SECRETARY_CODE}, "/api/auth/secretary-login")
    assert data["user"]["role"] == "secretary"
    return data


@pytest.fixture(scope="session")
def teacher_auth(admin_auth):
    """Create an isolated teacher because preview teacher passwords are not stable."""
    suffix = uuid4().hex[:8]
    create_response = requests.post(
        f"{BASE_URL}/api/admin/create-teacher",
        json={"first_name": f"TEST_{suffix}", "last_name": "LeaveBalance"},
        headers=_headers(admin_auth["access_token"]),
        timeout=30,
    )
    assert create_response.status_code == 200, create_response.text
    created = create_response.json()
    data = _login({"email": created["email"], "password": created["temporary_password"]})
    assert data["user"]["role"] == "teacher"
    yield data

    user_id = data["user"]["id"]
    delete_response = requests.delete(
        f"{BASE_URL}/api/admin/delete-user/{user_id}",
        headers=_headers(admin_auth["access_token"]),
        timeout=30,
    )
    assert delete_response.status_code == 200, delete_response.text
    purge_response = requests.delete(
        f"{BASE_URL}/api/admin/permanent-delete/{user_id}",
        headers=_headers(admin_auth["access_token"]),
        timeout=30,
    )
    assert purge_response.status_code == 200, purge_response.text

    # User deletion intentionally retains related records, so remove only this test user's artifacts.
    from pymongo import MongoClient

    backend_env = dotenv_values("/app/backend/.env")
    mongo_url = backend_env.get("MONGO_URL")
    db_name = backend_env.get("DB_NAME")
    if mongo_url and db_name:
        client = MongoClient(mongo_url)
        test_db = client[db_name]
        test_db.leave_balances.delete_many({"user_id": user_id})
        test_db.welcome_letters.delete_many({"user_id": user_id})
        client.close()


class TestLeaveBalanceAuthorization:
    """Role and authentication checks for employee leave APIs."""

    @pytest.mark.parametrize(
        "path",
        ["/api/admin/leave-balances", "/api/admin/leave-balance/nonexistent-user"],
    )
    def test_admin_leave_routes_require_authentication(self, path):
        response = requests.get(f"{BASE_URL}{path}", timeout=30)
        assert response.status_code in (401, 403)
        assert isinstance(response.json().get("detail"), str)

    def test_secretary_can_access_employee_balances(self, secretary_auth):
        response = requests.get(
            f"{BASE_URL}/api/admin/leave-balances",
            headers=_headers(secretary_auth["access_token"]),
            timeout=30,
        )
        assert response.status_code == 200, response.text
        assert isinstance(response.json(), list)

    def test_unknown_user_detail_returns_404(self, admin_auth):
        response = requests.get(
            f"{BASE_URL}/api/admin/leave-balance/TEST_nonexistent_user",
            headers=_headers(admin_auth["access_token"]),
            timeout=30,
        )
        assert response.status_code == 404
        assert response.json().get("detail") == "User not found"


class TestAdminLeaveBalances:
    """All-employee and detailed leave balance response validation."""

    def test_all_employee_balances_and_calculation(self, admin_auth):
        response = requests.get(
            f"{BASE_URL}/api/admin/leave-balances",
            headers=_headers(admin_auth["access_token"]),
            timeout=30,
        )
        assert response.status_code == 200, response.text
        employees = response.json()
        assert isinstance(employees, list) and employees, "Expected at least one employee"
        assert any(emp["role"] == "teacher" for emp in employees)
        assert any(emp["role"] == "admin" for emp in employees)
        assert any(emp["role"] == "secretary" for emp in employees)

        required = {
            "user_id", "first_name", "last_name", "email", "role",
            "total_earned", "total_taken", "remaining", "start_date",
        }
        for employee in employees:
            assert required <= employee.keys()
            assert employee["role"] in {"teacher", "secretary", "admin"}
            assert isinstance(employee["user_id"], str) and employee["user_id"]
            assert isinstance(employee["email"], str) and "@" in employee["email"]
            assert "password_hash" not in employee and "temporary_password" not in employee
            assert isinstance(employee["total_earned"], (int, float))
            assert isinstance(employee["total_taken"], (int, float))
            assert isinstance(employee["remaining"], (int, float))
            assert 0 <= employee["total_earned"] <= 30
            assert employee["remaining"] == pytest.approx(
                employee["total_earned"] - employee["total_taken"]
            )
            _, expected = _expected_earned(employee["start_date"])
            assert employee["total_earned"] == expected

    def test_specific_teacher_detail_matches_list(self, admin_auth):
        headers = _headers(admin_auth["access_token"])
        list_response = requests.get(
            f"{BASE_URL}/api/admin/leave-balances", headers=headers, timeout=30
        )
        assert list_response.status_code == 200
        teacher = next(emp for emp in list_response.json() if emp["role"] == "teacher")

        detail_response = requests.get(
            f"{BASE_URL}/api/admin/leave-balance/{teacher['user_id']}",
            headers=headers,
            timeout=30,
        )
        assert detail_response.status_code == 200, detail_response.text
        detail = detail_response.json()
        assert detail["user_id"] == teacher["user_id"]
        assert detail["first_name"] == teacher["first_name"]
        assert detail["last_name"] == teacher["last_name"]
        assert detail["role"] == "teacher"
        assert detail["total_earned"] == teacher["total_earned"]
        assert detail["total_taken"] == teacher["total_taken"]
        assert detail["remaining"] == teacher["remaining"]
        assert isinstance(detail["months_worked"], int) and detail["months_worked"] >= 0
        assert detail["total_earned"] == min(30.0, detail["months_worked"] * 2.5)
        assert isinstance(detail["approved_leaves"], list)


class TestTeacherOwnLeaveBalance:
    """Logged-in teacher leave counter response and identity checks."""

    def test_teacher_own_leave_balance(self, teacher_auth, admin_auth):
        teacher_response = requests.get(
            f"{BASE_URL}/api/teacher/my-leave-balance",
            headers=_headers(teacher_auth["access_token"]),
            timeout=30,
        )
        assert teacher_response.status_code == 200, teacher_response.text
        balance = teacher_response.json()
        assert set(balance) == {"months_worked", "total_earned", "total_taken", "remaining"}
        assert isinstance(balance["months_worked"], int) and balance["months_worked"] >= 0
        assert balance["total_earned"] == min(30.0, balance["months_worked"] * 2.5)
        assert balance["remaining"] == pytest.approx(balance["total_earned"] - balance["total_taken"])

        detail_response = requests.get(
            f"{BASE_URL}/api/admin/leave-balance/{teacher_auth['user']['id']}",
            headers=_headers(admin_auth["access_token"]),
            timeout=30,
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        for field in ("months_worked", "total_earned", "total_taken", "remaining"):
            assert balance[field] == detail[field]


class TestIntermediateQuestions:
    """Public intermediate placement test contains 20 valid unique MCQs."""

    def test_intermediate_returns_twenty_mcqs(self):
        response = requests.get(f"{BASE_URL}/api/tests/intermediate", timeout=30)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data.get("level") == "intermediate"
        questions = data.get("questions")
        assert isinstance(questions, list) and len(questions) == 20
        ids = []
        texts = []
        for question in questions:
            assert isinstance(question.get("id"), str) and question["id"]
            assert isinstance(question.get("question"), str) and question["question"].strip()
            assert isinstance(question.get("options"), list) and len(question["options"]) == 4
            assert all(isinstance(option, str) and option.strip() for option in question["options"])
            assert len(set(question["options"])) == 4
            ids.append(question["id"])
            texts.append(question["question"])
        assert len(set(ids)) == 20
        assert len(set(texts)) == 20
