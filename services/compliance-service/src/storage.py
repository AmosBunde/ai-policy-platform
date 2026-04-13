"""File storage abstraction: local filesystem and S3."""
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)

_SAFE_FILENAME_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-z]{2,4}$")


def generate_safe_filename(extension: str) -> str:
    """Generate a UUID-based filename. No user-supplied names allowed."""
    ext = extension.lower().strip(".")
    if ext not in ("pdf", "docx", "html"):
        raise ValueError(f"Invalid extension: {ext}")
    return f"{uuid.uuid4()}.{ext}"


def validate_filename(filename: str) -> bool:
    """Validate that a filename is safe (UUID format, no traversal)."""
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    return bool(_SAFE_FILENAME_RE.match(filename))


class FileStorage(ABC):
    """Abstract file storage interface."""

    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """Save file and return the storage path/URL."""

    @abstractmethod
    async def retrieve(self, filename: str) -> bytes | None:
        """Retrieve file content by filename."""

    @abstractmethod
    async def exists(self, filename: str) -> bool:
        """Check if file exists."""


class LocalFileStorage(FileStorage):
    """Local filesystem storage with UUID filenames."""

    def __init__(self, base_dir: str = "/data/reports"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        if not validate_filename(filename):
            raise ValueError(f"Invalid filename: {filename!r}")

        file_path = self._base_dir / filename
        # Ensure resolved path is within base directory (prevent traversal)
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(self._base_dir.resolve())):
            raise ValueError("Path traversal detected")

        file_path.write_bytes(content)
        logger.info("Saved report: %s", filename)
        return str(file_path)

    async def retrieve(self, filename: str) -> bytes | None:
        if not validate_filename(filename):
            raise ValueError(f"Invalid filename: {filename!r}")

        file_path = self._base_dir / filename
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(self._base_dir.resolve())):
            raise ValueError("Path traversal detected")

        if not file_path.exists():
            return None
        return file_path.read_bytes()

    async def exists(self, filename: str) -> bool:
        if not validate_filename(filename):
            return False
        file_path = self._base_dir / filename
        return file_path.exists()


class S3FileStorage(FileStorage):
    """S3 storage with pre-signed URLs (1hr expiry)."""

    def __init__(self, bucket: str, region: str = "us-east-1"):
        self._bucket = bucket
        self._region = region
        self._prefix = "reports/"

    async def save(self, filename: str, content: bytes) -> str:
        if not validate_filename(filename):
            raise ValueError(f"Invalid filename: {filename!r}")

        import boto3
        s3 = boto3.client("s3", region_name=self._region)
        key = f"{self._prefix}{filename}"
        s3.put_object(Bucket=self._bucket, Key=key, Body=content)
        logger.info("Saved report to S3: %s/%s", self._bucket, key)
        return f"s3://{self._bucket}/{key}"

    async def retrieve(self, filename: str) -> bytes | None:
        if not validate_filename(filename):
            raise ValueError(f"Invalid filename: {filename!r}")

        import boto3
        s3 = boto3.client("s3", region_name=self._region)
        key = f"{self._prefix}{filename}"
        try:
            response = s3.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except Exception:
            return None

    async def exists(self, filename: str) -> bool:
        if not validate_filename(filename):
            return False

        import boto3
        s3 = boto3.client("s3", region_name=self._region)
        key = f"{self._prefix}{filename}"
        try:
            s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    def generate_presigned_url(self, filename: str, expiry: int = 3600) -> str:
        """Generate a pre-signed download URL with 1hr default expiry."""
        if not validate_filename(filename):
            raise ValueError(f"Invalid filename: {filename!r}")

        import boto3
        s3 = boto3.client("s3", region_name=self._region)
        key = f"{self._prefix}{filename}"
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expiry,
        )
