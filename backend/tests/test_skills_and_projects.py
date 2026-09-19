def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _create_employee(client, admin_token, department, job_role, email="skill.test@acmecorp.example"):
    payload = {
        "full_name": "Skill Test",
        "email": email,
        "department_id": str(department.id),
        "job_role_id": str(job_role.id),
        "joining_date": "2023-01-01",
    }
    return client.post("/api/v1/employees", json=payload, headers=auth_header(admin_token)).json()


def test_assign_skill_to_employee(client, admin_token, sample_department, sample_job_role):
    employee = _create_employee(client, admin_token, sample_department, sample_job_role)
    skill = client.post(
        "/api/v1/skills", json={"name": "Python", "category": "Programming"}, headers=auth_header(admin_token)
    ).json()

    response = client.post(
        f"/api/v1/employees/{employee['id']}/skills",
        json={"skill_id": skill["id"], "proficiency_level": "ADVANCED", "years_of_experience": 4},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 201
    assert response.json()["skill"]["name"] == "Python"


def test_create_project(client, admin_token, sample_department):
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": "Test Project",
            "department_id": str(sample_department.id),
            "start_date": "2024-01-01",
        },
        headers=auth_header(admin_token),
    )
    assert response.status_code == 201
    assert response.json()["project_code"].startswith("PRJ-")


def test_document_upload_requires_valid_type(client, admin_token, sample_department, sample_job_role):
    employee = _create_employee(client, admin_token, sample_department, sample_job_role, email="doc.test@acmecorp.example")
    response = client.post(
        f"/api/v1/employees/{employee['id']}/documents",
        files={"file": ("resume.exe", b"fake-binary", "application/x-msdownload")},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 400
