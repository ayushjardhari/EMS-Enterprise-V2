from app.core.security import hash_password
from app.models.user import User, UserRole


def test_login_success(client, db_session):
    user = User(email="hr@acmecorp.example", hashed_password=hash_password("Hr@12345"), user_role=UserRole.HR)
    db_session.add(user)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={"email": "hr@acmecorp.example", "password": "Hr@12345"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, db_session):
    user = User(email="hr2@acmecorp.example", hashed_password=hash_password("Hr@12345"), user_role=UserRole.HR)
    db_session.add(user)
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={"email": "hr2@acmecorp.example", "password": "wrong"})
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token(client, admin_token):
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "admin@acmecorp.example"
