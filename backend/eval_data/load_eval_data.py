"""Load the 30 synthetic employees (+ resumes) into the database.

Run inside the backend container, after `python seed.py`:

    docker compose exec backend python -m eval_data.load_eval_data
    docker compose exec backend python -m eval_data.load_eval_data --reset   # delete EVAL-* employees first

Each resume is uploaded through the real upload path (MinIO storage, text
extraction, section chunking, embeddings), so this also exercises the
pipeline end to end. Employees are tagged with codes EVAL-001 .. EVAL-030
so they are easy to find and remove.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO

from starlette.datastructures import Headers, UploadFile

import app.models  # noqa: F401
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.document import Document
from app.models.employee import AvailabilityStatus, Employee, EmploymentStatus
from app.models.employee_skill import EmployeeSkill, ProficiencyLevel
from app.models.job_role import JobRole
from app.models.skill import Skill
from app.models.user import User, UserRole
from app.services.document_extraction import extract_text
from app.services.document_indexing_service import DocumentIndexingService
from app.services.document_service import DocumentService
from eval_data.personas import PERSONAS
from eval_data.resume_builder import build_docx, email_for

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
CODE_PREFIX = "EVAL-"


def get_or_create(db, model, lookup: dict, extra: dict | None = None):
    obj = db.query(model).filter_by(**lookup).first()
    if obj is None:
        obj = model(**lookup, **(extra or {}))
        db.add(obj)
        db.flush()
    return obj


def reset(db, remove_from_storage: bool) -> int:
    employees = db.query(Employee).filter(Employee.employee_code.like(f"{CODE_PREFIX}%")).all()
    if remove_from_storage:
        from app.core.minio_client import minio_client
        for employee in employees:
            for document in employee.documents:
                try:
                    minio_client.remove_object(settings.MINIO_BUCKET_NAME, document.storage_path)
                except Exception as exc:  # keep going: the file may already be gone
                    print(f"  could not remove {document.storage_path}: {exc}")
    for employee in employees:
        db.delete(employee)
    db.commit()
    return len(employees)


def create_employees(db) -> list[Employee]:
    created = []
    for number, persona in enumerate(PERSONAS, start=1):
        code = f"{CODE_PREFIX}{number:03d}"
        if db.query(Employee).filter_by(employee_code=code).first():
            print(f"  {code} {persona.name}: already exists, skipping (use --reset to rebuild)")
            continue
        department = get_or_create(db, Department, {"name": persona.department})
        role = get_or_create(db, JobRole, {"title": persona.role})
        employee = Employee(
            employee_code=code, full_name=persona.name, email=email_for(persona),
            location=persona.location, profile_info=persona.summary,
            department_id=department.id, job_role_id=role.id,
            joining_date=date.today() - timedelta(days=365 * min(persona.years, 4)),
            employment_status=EmploymentStatus.ACTIVE,
            availability_status=AvailabilityStatus(persona.availability),
        )
        db.add(employee)
        db.flush()
        for name, category, level, years in persona.skills:
            skill = get_or_create(db, Skill, {"name": name}, {"category": category})
            db.add(EmployeeSkill(employee_id=employee.id, skill_id=skill.id,
                                 proficiency_level=ProficiencyLevel(level), years_of_experience=Decimal(years)))
        created.append(employee)
    db.commit()
    return created


def attach_resume(db, employee: Employee, persona, use_storage: bool) -> None:
    data = build_docx(persona)
    filename = f"{persona.name.replace(' ', '_')}_resume.docx"
    if use_storage:
        upload = UploadFile(file=BytesIO(data), filename=filename, headers=Headers({"content-type": DOCX_MIME}))
        admin = User(user_role=UserRole.ADMIN)  # transient: only used for the permission check
        DocumentService(db).upload_document(employee.id, upload, admin)
        return
    # No MinIO available: store only the database record and extracted text.
    document = Document(
        employee_id=employee.id, filename=filename, file_type=DOCX_MIME,
        storage_path=f"eval/{employee.employee_code}/{filename}",
        extracted_text=extract_text(data, DOCX_MIME), extraction_status="COMPLETED",
        extracted_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    if settings.AUTO_INDEX_ON_UPLOAD:
        DocumentIndexingService(db).index_document_safely(document)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="delete existing EVAL-* employees first")
    parser.add_argument("--no-storage", action="store_true", help="skip MinIO (database record + text only)")
    parser.add_argument("--no-index", action="store_true", help="do not chunk/embed (run reindex_documents later)")
    args = parser.parse_args()
    if args.no_index:
        settings.AUTO_INDEX_ON_UPLOAD = False

    with SessionLocal() as db:
        if args.reset:
            print(f"Removed {reset(db, remove_from_storage=not args.no_storage)} existing EVAL-* employee(s)")
        employees = create_employees(db)
        by_name = {p.name: p for p in PERSONAS}
        print(f"Created {len(employees)} employee(s); uploading resumes...")
        for employee in employees:
            attach_resume(db, employee, by_name[employee.full_name], use_storage=not args.no_storage)
            print(f"  {employee.employee_code} {employee.full_name}")
    print("Done. Check with: python -m scripts.reindex_documents --query \"container orchestration\"")


if __name__ == "__main__":
    main()
