from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.document_chunk_repository import DocumentChunkRepository

BODY = {"requirement": "Engineers with Kubernetes and infrastructure as code experience", "top_k": 5}


def test_matching_requires_authentication(client):
    assert client.post("/api/v1/matching/search", json=BODY).status_code == 401


def test_matching_forbidden_for_plain_employee(client, db_session):
    db_session.add(User(email="emp@acmecorp.example", hashed_password=hash_password("Emp@12345"), user_role=UserRole.EMPLOYEE))
    db_session.commit()
    token = client.post("/api/v1/auth/login", json={"email": "emp@acmecorp.example", "password": "Emp@12345"}).json()["access_token"]
    response = client.post("/api/v1/matching/search", json=BODY, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_matching_validates_input(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    assert client.post("/api/v1/matching/search", json={"requirement": "short"}, headers=headers).status_code == 422
    assert client.post("/api/v1/matching/search", json={**BODY, "top_k": 500}, headers=headers).status_code == 422


def test_matching_with_no_candidates_returns_empty_list(client, admin_token):
    response = client.post("/api/v1/matching/search", json=BODY, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == {"requirement": BODY["requirement"], "candidates_considered": 0, "results": []}
