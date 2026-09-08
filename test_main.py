import os

import pytest
from fastapi.testclient import TestClient
from main import app, users_db, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH, ph

test_password = "supersecure12"
hashed_password = ph.hash(test_password)

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    """Resets the mock in-memory database before and after every single test."""
    users_db.clear()
    yield

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
    users_db["eoihd@gmai.com"] = hashed_password
    response = client.post("/signup", json={"email": "EoihD@gmai.com", "password": test_password})

    assert response.status_code == 400
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
    response = client.post("/signup", json={"email": "eoihd@gmai.com", "password": test_password})

    assert response.status_code == 201
    assert response.json() == {"message": "Your credentials have been saved! you can now log in"}
    assert "eoihd@gmai.com" in users_db

    stored_hash = users_db["eoihd@gmai.com"]

    assert stored_hash != test_password
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
    users_db["eoihd@gmai.com"] = hashed_password
    response = client.post(url="/signin", json={"email": "eoihd@gmai.com", "password": ""})

    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

def test_signin_email_doesnt_match():
    """
    Verifies that the /signin endpoint prevents user signing in with non-existent email
    """
    users_db["eoihd@gmai.com"] = hashed_password
    response = client.post(url="/signin", json={"email": "geoihd@gmai.com", "password": test_password})

    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

def test_signin_password_doesnt_match():
    """
    Verifies that the /signin endpoint prevents user signing in with wrong password
    """
    users_db["eoihd@gmai.com"] = hashed_password
    response = client.post(url="/signin", json={"email": "eoihd@gmai.com", "password": "supersecure123"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

def test_signin_succesful():
    """
    Verifies that the /signin endpoint signs in the user successfully.
    """
    users_db["eoihd@gmai.com"] = hashed_password
    response = client.post("/signin", json={"email": "eoihd@gmai.com", "password": test_password})

    assert response.status_code == 202
    assert response.json() == {"message": "Welcome back!"}