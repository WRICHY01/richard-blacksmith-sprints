from fastapi.testclient import TestClient
from main import app, MIN_PASSWORD_LENGTH


client = TestClient(app)

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

def test_signup_flows():
    """
    Verifies that the /signup endpoint validates data inputs correctly.
    """
    response = client.post("/signup", json={"email": "eoihdgmaicom", "password": "12345678" })
    assert response.status_code == 422

    response = client.post(url="/signup", json={"email": "eoihd@gmai.com", "password": "" })
    assert response.status_code == 400
    assert response.json() == {"detail": "Password cannot be empty!"}

    response = client.post(url="/signup", json={"email": "eoihd@gmai.com", "password": "1234" })
    assert response.status_code == 400
    assert response.json() == {"detail": f"Password must have a min of {MIN_PASSWORD_LENGTH} characters long"}

    response = client.post("/signup", json={"email": "eoihd@gmai.com", "password": "supersecure12"})
    assert response.status_code == 200
    assert response.json() == {"message": "Your credentials have been saved! you can now log in"}

    response = client.post("/signup", json={"email": "eoihd@gmai.com", "password": "supersecure12"})
    assert response.status_code == 400
    assert response.json() == {"detail": "That email is already in use!"}


def test_signin_flows():
    """
    Verifies that the /signin endpoint validates data inputs correctly.
    """
    response = client.post("/signin", json={"email": "eoihdgmaicom", "password": "12345678" })
    assert response.status_code == 422
    
    response = client.post(url="/signin", json={"email": "eoihd@gmai.com", "password": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Password cannot be empty!"}

    response = client.post(url="/signin", content='{"email": "geoihd@gmai.com", "password": "123456578"}')
    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

    response = client.post(url="/signin", json={"email": "eoihd@gmai.com", "password": "supersecure123"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Email or Password doesnt match"}

    response = client.post("/signin", json={"email": "eoihd@gmai.com", "password": "supersecure12"})
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome back!"}