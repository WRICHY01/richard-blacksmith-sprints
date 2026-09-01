from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """
    Verifies that the home endpoint returns a 200 status code and
    the correct welcom message payload.
    """

    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Authentication Core."}


def test_health_check():
    """
    Verifies that the health check endpoint returns a 200 status code and
    a clean operational status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}