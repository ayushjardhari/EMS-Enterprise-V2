"""
MinIO client, created once per process, and a helper to make sure the
document bucket exists before the app starts serving upload requests.
"""
from minio import Minio

from app.core.config import settings

minio_client = Minio(
    f"{settings.MINIO_HOST}:{settings.MINIO_API_PORT}",
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=False,
)


def ensure_bucket_exists() -> None:
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
