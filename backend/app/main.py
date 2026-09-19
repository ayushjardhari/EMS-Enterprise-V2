"""
FastAPI application entrypoint.

Only responsible for: creating the app, wiring middleware (CORS), and
registering routers. All business logic lives in services/, all data
access in repositories/ — this file should stay this short forever.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.minio_client import ensure_bucket_exists
import app.models  # noqa: F401 — registers all models on Base.metadata
from app.routers import attendance, auth, dashboard, departments, documents, employees, job_roles, projects, skills, hr

app = FastAPI(title="Employee Management System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    ensure_bucket_exists()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(employees.router)
app.include_router(departments.router)
app.include_router(job_roles.router)
app.include_router(skills.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(dashboard.router)
app.include_router(hr.router)
