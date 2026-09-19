"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-02

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create_type=False on every enum below is required: without it,
    # SQLAlchemy automatically tries to CREATE TYPE a second time the
    # moment the enum is used as a column type inside op.create_table() —
    # even though it was just created explicitly a few lines below with
    # checkfirst=True. That second, uncontrolled creation attempt is what
    # raised psycopg2.errors.DuplicateObject. Setting create_type=False
    # makes the explicit .create() loop below the ONLY place these types
    # are ever created, regardless of how many tables reference them.
    user_role = pg.ENUM("ADMIN", "HR", "MANAGER", "EMPLOYEE", name="user_role", create_type=False)
    employment_status = pg.ENUM("ACTIVE", "INACTIVE", "ON_LEAVE", name="employment_status", create_type=False)
    availability_status = pg.ENUM(
        "AVAILABLE", "PARTIALLY_AVAILABLE", "UNAVAILABLE", name="availability_status", create_type=False
    )
    proficiency_level = pg.ENUM(
        "BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT", name="proficiency_level", create_type=False
    )
    project_status = pg.ENUM("PLANNED", "ACTIVE", "ON_HOLD", "COMPLETED", name="project_status", create_type=False)

    bind = op.get_bind()
    for enum in (user_role, employment_status, availability_status, proficiency_level, project_status):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "departments",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_departments_name", "departments", ["name"])
    op.create_index("ix_departments_is_active", "departments", ["is_active"])

    op.create_table(
        "job_roles",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_roles_title", "job_roles", ["title"])

    op.create_table(
        "skills",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_skills_name", "skills", ["name"])

    op.create_table(
        "employees",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_code", sa.String(20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("location", sa.String(150), nullable=True),
        sa.Column("profile_info", sa.String(2000), nullable=True),
        sa.Column("department_id", pg.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("job_role_id", pg.UUID(as_uuid=True), sa.ForeignKey("job_roles.id"), nullable=False),
        sa.Column("joining_date", sa.Date, nullable=False),
        sa.Column("employment_status", employment_status, nullable=False, server_default="ACTIVE"),
        sa.Column("availability_status", availability_status, nullable=False, server_default="AVAILABLE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"])
    op.create_index("ix_employees_email", "employees", ["email"])
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_job_role_id", "employees", ["job_role_id"])
    op.create_index("ix_employees_employment_status", "employees", ["employment_status"])
    op.create_index("ix_employees_availability_status", "employees", ["availability_status"])

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("user_role", user_role, nullable=False),
        sa.Column("employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "employee_skills",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", pg.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proficiency_level", proficiency_level, nullable=False),
        sa.Column("years_of_experience", sa.Numeric(4, 1), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill"),
    )
    op.create_index("ix_employee_skills_employee_id", "employee_skills", ["employee_id"])
    op.create_index("ix_employee_skills_skill_id", "employee_skills", ["skill_id"])

    op.create_table(
        "projects",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_code", sa.String(20), nullable=False, unique=True),
        sa.Column("project_name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("department_id", pg.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("status", project_status, nullable=False, server_default="PLANNED"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_projects_project_code", "projects", ["project_code"])
    op.create_index("ix_projects_department_id", "projects", ["department_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "employee_projects",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", pg.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_role", sa.String(150), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("employee_id", "project_id", name="uq_employee_project"),
    )
    op.create_index("ix_employee_projects_employee_id", "employee_projects", ["employee_id"])
    op.create_index("ix_employee_projects_project_id", "employee_projects", ["project_id"])

    op.create_table(
        "documents",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", pg.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False, unique=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_employee_id", "documents", ["employee_id"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("employee_projects")
    op.drop_table("projects")
    op.drop_table("employee_skills")
    op.drop_table("users")
    op.drop_table("employees")
    op.drop_table("skills")
    op.drop_table("job_roles")
    op.drop_table("departments")

    bind = op.get_bind()
    for enum_name in ("project_status", "proficiency_level", "availability_status", "employment_status", "user_role"):
        pg.ENUM(name=enum_name).drop(bind, checkfirst=True)