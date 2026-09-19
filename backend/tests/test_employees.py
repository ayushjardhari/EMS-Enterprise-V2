def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_employee(client, admin_token, sample_department, sample_job_role):
    payload = {
        "full_name": "Jane Doe",
        "email": "jane.doe@acmecorp.example",
        "department_id": str(sample_department.id),
        "job_role_id": str(sample_job_role.id),
        "joining_date": "2024-01-15",
    }
    response = client.post("/api/v1/employees", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Jane Doe"
    assert body["employee_code"].startswith("EMP-")


def test_create_employee_duplicate_email_rejected(client, admin_token, sample_department, sample_job_role):
    payload = {
        "full_name": "Jane Doe",
        "email": "dup@acmecorp.example",
        "department_id": str(sample_department.id),
        "job_role_id": str(sample_job_role.id),
        "joining_date": "2024-01-15",
    }
    first = client.post("/api/v1/employees", json=payload, headers=auth_header(admin_token))
    assert first.status_code == 201
    second = client.post("/api/v1/employees", json=payload, headers=auth_header(admin_token))
    assert second.status_code == 409


def test_get_employee(client, admin_token, sample_department, sample_job_role):
    payload = {
        "full_name": "John Roe",
        "email": "john.roe@acmecorp.example",
        "department_id": str(sample_department.id),
        "job_role_id": str(sample_job_role.id),
        "joining_date": "2023-06-01",
    }
    created = client.post("/api/v1/employees", json=payload, headers=auth_header(admin_token)).json()

    response = client.get(f"/api/v1/employees/{created['id']}", headers=auth_header(admin_token))
    assert response.status_code == 200
    assert response.json()["email"] == "john.roe@acmecorp.example"


def test_update_employee(client, admin_token, sample_department, sample_job_role):
    payload = {
        "full_name": "Update Me",
        "email": "update.me@acmecorp.example",
        "department_id": str(sample_department.id),
        "job_role_id": str(sample_job_role.id),
        "joining_date": "2023-06-01",
    }
    created = client.post("/api/v1/employees", json=payload, headers=auth_header(admin_token)).json()

    response = client.put(
        f"/api/v1/employees/{created['id']}", json={"full_name": "Updated Name"}, headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_search_employees(client, admin_token, sample_department, sample_job_role):
    for name, email in [("Alpha Smith", "alpha@acmecorp.example"), ("Beta Jones", "beta@acmecorp.example")]:
        client.post(
            "/api/v1/employees",
            json={
                "full_name": name,
                "email": email,
                "department_id": str(sample_department.id),
                "job_role_id": str(sample_job_role.id),
                "joining_date": "2023-01-01",
            },
            headers=auth_header(admin_token),
        )

    response = client.get("/api/v1/employees", params={"search": "Alpha"}, headers=auth_header(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["full_name"] == "Alpha Smith"


def test_employee_crud_requires_authorization(client, sample_department, sample_job_role):
    response = client.post(
        "/api/v1/employees",
        json={
            "full_name": "No Auth",
            "email": "noauth@acmecorp.example",
            "department_id": str(sample_department.id),
            "job_role_id": str(sample_job_role.id),
            "joining_date": "2023-01-01",
        },
    )
    assert response.status_code == 401
