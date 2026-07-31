import os
import pytest
from fastapi.testclient import TestClient

# Mock the environment passwords before importing main
os.environ["EDITOR_PASSWORD"] = "test_editor_pwd"
os.environ["ADMIN_PASSWORD"] = "test_admin_pwd"

from bcsfe_web.main import app

client = TestClient(app)

def test_login_auth_fail():
    # Login with wrong or missing password header should fail with 401
    response = client.post(
        "/login",
        json={
            "transfer_code": "TEST",
            "confirmation_code": "0000",
            "country_code": "tw",
            "game_version": "15.5.0"
        },
        headers={"X-Editor-Password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "密碼錯誤，拒絕存取"

def test_login_auth_success():
    # Login with correct password header should pass auth (though it might fail on test_data not existing,
    # but the authentication check should succeed first).
    # Since TEST/0000 will try to read local test data, let's see:
    response = client.post(
        "/login",
        json={
            "transfer_code": "TEST",
            "confirmation_code": "0000",
            "country_code": "tw",
            "game_version": "15.5.0"
        },
        headers={"X-Editor-Password": "test_editor_pwd"}
    )
    # The auth itself passed, and we expect 200 or 400 (if test data is missing), but NOT 401.
    assert response.status_code != 401

def test_admin_auth_fail_missing_header():
    response = client.get("/admin/history")
    assert response.status_code == 401
    assert response.json()["detail"] == "密碼錯誤，拒絕存取"

def test_admin_auth_fail_wrong_password():
    response = client.get("/admin/history", headers={"X-Admin-Password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "密碼錯誤，拒絕存取"

def test_admin_auth_success():
    # Mock database get_save_history to avoid DB dependency issues
    from bcsfe_web import database
    original_get_history = database.get_save_history
    database.get_save_history = lambda: []
    try:
        response = client.get("/admin/history", headers={"X-Admin-Password": "test_admin_pwd"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    finally:
        database.get_save_history = original_get_history
