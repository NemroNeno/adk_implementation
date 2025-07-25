from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_access_token():
    # First, you need a test user. You'd typically use fixtures to create one.
    # For simplicity, we'll assume a user exists.
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "test@example.com", "password": "password123"}
    )
    # This will fail until you set up a test DB and user fixtures
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"