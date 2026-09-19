# EMS Enterprise v2

Enterprise-grade Employee Management System foundation for HR operations and future AI-assisted workforce intelligence.

## What is included

- Role-based workspaces for Admin, HR, Manager and Employee
- Employee directory, departments, roles, skills and projects
- Attendance command center with date, status and employee filtering
- Attendance KPIs and workforce analytics
- Leave types, balances, requests and approval workflow
- Payroll profiles, monthly payroll runs, deductions, allowances, bonuses and payslip history
- Audit trail for sensitive HR actions
- Employee self-service for attendance, leave and payslips
- Document storage with MinIO and document text extraction/chunking foundation
- JWT authentication and server-side RBAC
- Repository/service/router backend architecture
- PostgreSQL + Alembic migrations
- Docker Compose deployment
- Seed data with Indian employee names and realistic HR/payroll data
- AI-ready employee, skill, project and document structure; embeddings/RAG/agents remain intentionally separated as the next intelligence layer

## Run

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python seed.py
```

Open `http://localhost:5173`.

Demo accounts:

- Admin: `admin@acmecorp.example` / `Admin@123`
- HR: `hr@acmecorp.example` / `Hr@12345`
- Manager: `manager@acmecorp.example` / `Manager@123`
- Employee: `employee@acmecorp.example` / `Employee@123`

API documentation: `http://localhost:8000/docs`

## Product architecture

```text
React + TypeScript
        ↓
FastAPI /api/v1
        ↓
Auth + RBAC + validation
        ↓
Services
        ↓
Repositories
        ↓
PostgreSQL
   ↙         ↘
MinIO      structured HR data
              ↓
       future embeddings
              ↓
          vector search
              ↓
             RAG
              ↓
           agents
```

## Engineering notes

The v2 implementation is designed as a strong development/staging foundation. Before a real production deployment, rotate secrets, configure TLS, backups, centralized logging/monitoring, object-storage policies, database migrations in CI/CD, and a full security/load test suite.

## Sprint 3
The Employee Profile is now an Employee 360 workspace with tabbed overview, attendance, projects, skills, documents, and activity views. It uses the existing FastAPI APIs and does not introduce a new backend migration.
