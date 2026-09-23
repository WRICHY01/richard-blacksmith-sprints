import os
from datetime import datetime, timezone, timedelta

import pytest
import hashlib
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

from main import app, supabase, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH, ph

test_password = "supersecure12"
hashed_password = ph.hash(test_password)
expiration_time = datetime.now(timezone.utc) + timedelta(days=1)

client = TestClient(app)

TRACKED_TEST_EMAILS = set()

@pytest.fixture(autouse=True)
def run_around_tests():
    """Safely cleans up only the specific test accounts generated during the active test run."""

    yield

    if TRACKED_TEST_EMAILS:
        emails_to_wipe = list(TRACKED_TEST_EMAILS)
        supabase.table("user_sessions").delete().in_("user_email", emails_to_wipe).execute()
        supabase.table("users").delete().in_("email", emails_to_wipe).execute()

        TRACKED_TEST_EMAILS.clear()

# --- 1. Root & Health Check Tests ---

def test_read_root():
    """
    Verifies that the home endpoint is working
    """
    response = client.get('/')

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the homepage!"}

def test_health_check():
    """
    Verifies that at health endpoint is working as expected
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- 2. Signup Endpoint Tests ---

def test_signup_duplicate_email():
    """
    Verifies that /signup endpoint prevents account duplication
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")

    supabase.table("users").insert({
        "email": "EoihD@gmai.com".lower(),
        "hashed_password": hashed_password
    }).execute()

    response = client.post("/signup", json={"email": "EoihD@gmai.com", "password": "secret_password"})
    
    assert response.status_code == 409
    assert response.json() == {"detail": "That email is already in use"}

def test_signup_invalid_email():
    """
    Verifies that /signup endpoint catches invalid emails via Pydantic (422).
    """
    response = client.post("/signup", json={"email": "eoihdgmaicom", "password": "12345678" })

    error_detail = response.json()["detail"][0]
    assert response.status_code == 422
    assert error_detail["loc"] == ["body", "email"]
    assert "value is not a valid email address:" in error_detail["msg"]

def test_missing_field_parameter():
    """
    Verifies that /signup endpoint catches missing field parameter via Pydantic (422).
    """
    response = client.post("/signup", json={"email": "eoihd@gmai.com"})

    error_detail = response.json()["detail"][0]
    assert response.status_code == 422
    assert error_detail["loc"] == ["body", "password"]
    assert error_detail["msg"] == "Field required"
    

def test_signup_empty_password():
    """
    Verifies that /signup endpoint prevents empty password
    """
    response = client.post(url="/signup", json={"email": "eoihd@gmai.com", "password": ""})

    assert response.status_code == 400
    assert response.json() == {"detail": "Password cannot be empty!"}

def test_signup_password_too_short():
    """
    Verifies that the /signup endpoint prevents password length less than the minimum allowable length.
    """
    response = client.post(url="/signup", json={"email": "eoihd@gmai.com", "password": "1234" })

    assert response.status_code == 400
    assert response.json() == {"detail": f"Password must have a min of {MIN_PASSWORD_LENGTH} characters long"}

def test_signup_password_too_long():
    """
    Verifies that the /signup endpoint prevents excessively long passwords to prevent CPU exhaustion.
    """
    response = client.post(url="/signup", json={"email": "eoihd@gmai.com", "password": "A" * 300})

    assert response.status_code == 400
    assert response.json() == {"detail": f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters"}

def test_signup_successful():
    """
    Verifies that the /signup endpoint validates and saves user data correctly.
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")

    response = client.post("/signup", json={"email": "eoihd@gmai.com", "password": test_password})

    assert response.status_code == 201
    assert response.json() == {"message": "Your credentials have been saved! you can now log in"}

    db_response = supabase.table("users").select("email", "hashed_password").eq("email", "eoihd@gmai.com").execute()

    db_response_session = db_response.data[0]
    print(f"db_response_session is thus: {db_response_session}")
    assert len(db_response.data) == 1
    assert "eoihd@gmai.com" in db_response_session["email"]

    stored_hash = db_response_session["hashed_password"]

    assert stored_hash != test_password
    assert stored_hash.startswith("$argon2id$")
    assert ph.verify(stored_hash, test_password) is True


# --- 3. Signin Endpoint Tests ---

def test_signin_invalid_email():
    """
    Verifies that /signin endpoint prevents invalid email format structure.
    """
    response = client.post("/signin", json={"email": "eoihdgmaicom", "password": "12345678" })

    assert response.status_code == 422

def test_signin_empty_password():
    """
    Verifies that /signin endpoint hides specific database existence data on empty inputs.
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")

    supabase.table("users").insert({
        "email": "eoihd@gmai.com",
        "hashed_password": hashed_password
    }).execute()

    response = client.post(url="/signin", json={"email": "eoihd@gmai.com", "password": ""})

    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

def test_signin_email_doesnt_match():
    """
    Verifies that the /signin endpoint prevents user signing in with non-existent email
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")

    supabase.table("users").insert({
            "email": "eoihd@gmai.com",
            "hashed_password": hashed_password
        }).execute()
    
    response = client.post(url="/signin", json={"email": "geoihd@gmai.com", "password": test_password})

    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

def test_signin_password_doesnt_match():
    """
    Verifies that the /signin endpoint prevents user signing in with wrong password
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")

    supabase.table("users").insert({
                "email": "eoihd@gmai.com",
                "hashed_password": hashed_password
            }).execute()
    
    response = client.post(url="/signin", json={"email": "eoihd@gmai.com", "password": "supersecure123"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

def test_signin_successful():
    """
    Verifies that the /signin endpoint signs in the user successfully.
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")

    supabase.table("users").insert({
                "email": "eoihd@gmai.com",
                "hashed_password": hashed_password
            }).execute()
    response = client.post("/signin", json={"email": "eoihd@gmai.com", "password": test_password})

    assert response.status_code == 202
    assert response.json() == {"message": "Welcome!"}

    db_response = supabase.table("user_sessions").select("session_token", "expiration_time").eq("user_email", "eoihd@gmai.com").execute()
    db_response_session = db_response.data[0]

    assert len(db_response.data) == 1
    assert "session_id" in response.cookies 

def test_no_session_token_returned_from_browser():
    """
    Verifies No active user session found
    """
    response = client.get("/dashboard")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized: No Active Session Found!"}


def test_no_session_token_matching_from_database_due_to_token_mismatch():
    """
    Verifies /dashboard endpoint prevents invalid user session from ever persisting
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")
    hashed_session_token = hashlib.sha256("manually-inserted-token-123".encode()).hexdigest()

    supabase.table("users").insert({
                    "email": "eoihd@gmai.com",
                    "hashed_password": hashed_password
                }).execute()
    
    supabase.table("user_sessions").insert({
                    "user_email": "eoihd@gmai.com",
                    "session_token": hashed_session_token,
                    "expiration_time": expiration_time.isoformat()
                }).execute()

    response = client.get("/dashboard", cookies={"session_id": "manually-inputted-token-123"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized: No Active Session Found!"}

def test_expired_session():
    """
    Verifies the /dashboard endpoint prevents expired session from ever persisting
    """
    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")
    hashed_session_token = hashlib.sha256("manually-inserted-token-123".encode()).hexdigest()
    expired_time = datetime.now(timezone.utc) + timedelta(days=-1) # Expired 1 day ago

    supabase.table("users").insert({
                        "email": "eoihd@gmai.com",
                        "hashed_password": hashed_password
                    }).execute()

    supabase.table("user_sessions").insert(
            {
                "user_email": "eoihd@gmai.com",
                "session_token": hashed_session_token,
                "expiration_time": expired_time.isoformat()
            }
        ).execute()
    
    response = client.get("/dashboard", cookies={"session_id": "manually-inserted-token-123"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized: Session Expired"}

def test_successful_signin_and_dashboard_workflow():
    """
    Verifies that the /dashboard endpoint works as expected and survives context reset.
    """
    global client
    from fastapi.testclient import TestClient
    from main import app

    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")
    supabase.table("users").insert({
                        "email": "eoihd@gmai.com",
                        "hashed_password": hashed_password
                    }).execute()
    
    signin_response = client.post("/signin", json={"email": "eoihd@gmai.com", "password": test_password})

    assert signin_response.status_code == 202
    assert signin_response.json() == {"message": "Welcome!"}

    saved_token_value = signin_response.cookies['session_id']
    assert "session_id" in signin_response.cookies
    assert "Max-Age=" in signin_response.headers.get("set-cookie", "")

    hashed_token_value =  hashlib.sha256(saved_token_value.encode()).hexdigest()

    db_response = supabase.table("user_sessions").select("user_email", "session_token").eq("session_token", hashed_token_value).execute()
    db_response_session = db_response.data

    assert len(db_response_session) == 1
    assert db_response_session[0]["session_token"] == hashed_token_value

    dashboard_response = client.get("/dashboard", cookies={"session_id": saved_token_value})

    assert dashboard_response.status_code == 200
    assert "welcome to your secure identity vault" in dashboard_response.json()['message']
    assert dashboard_response.json()["authenticated_as"] == "eoihd@gmai.com"

    # Mimicking the user closing the browser tab entirely and reopening to see if it persists
    client = TestClient(app)

    new_dashboard_response = client.get("/dashboard", cookies={"session_id": saved_token_value})

    assert new_dashboard_response.status_code == 200
    assert "welcome to your secure identity vault" in new_dashboard_response.json()["message"]
    assert new_dashboard_response.json()["authenticated_as"] == db_response_session[0]["user_email"]

def test_dashboard_with_pre_populated_session():
    """
    Verifies the /dashboard endpoint in pure isolation by 
    manually pre-populating the cloud user_sessions table first.
    """
    global client
    
    from fastapi.testclient import TestClient
    from main import app

    TRACKED_TEST_EMAILS.add("eoihd@gmai.com")
    hashed_session_token = hashlib.sha256("manually-inserted-token-123".encode()).hexdigest()

    expired_time = datetime.now(timezone.utc) + timedelta(days=1)
    supabase.table("users").insert({
                            "email": "eoihd@gmai.com",
                            "hashed_password": hashed_password
                        }).execute()
    
    supabase.table("user_sessions").insert(
                {
                    "user_email": "eoihd@gmai.com",
                    "session_token": hashed_session_token,
                    "expiration_time": expired_time.isoformat()
                }
            ).execute()

    # Mimicking the user closing the browser tab entirely and reopening to see if it persists
    client = TestClient(app)

    response = client.get("/dashboard", cookies={"session_id": "manually-inserted-token-123"})
    assert response.status_code == 200
    assert "welcome to your secure identity vault" in response.json()["message"]
    assert response.json()["authenticated_as"] == "eoihd@gmai.com"