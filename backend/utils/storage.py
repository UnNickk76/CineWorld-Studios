"""
Emergent Object Storage helper.
Usage: url = upload_image_bytes(png_bytes, 'image/png', prefix='trailers')
"""
import os
import uuid
import logging
import requests
from typing import Optional, Tuple

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "cineworld"
_storage_key: Optional[str] = None
logger = logging.getLogger(__name__)


def init_storage() -> Optional[str]:
    """Initialize and cache storage session key. Returns None if unavailable."""
    global _storage_key
    if _storage_key:
        return _storage_key
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        logger.warning("EMERGENT_LLM_KEY not set; object storage disabled")
        return None
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": key}, timeout=30)
        resp.raise_for_status()
        _storage_key = resp.json().get("storage_key")
        logger.info("Emergent object storage initialized")
        return _storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise RuntimeError("Storage key unavailable")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str) -> Tuple[bytes, str]:
    key = init_storage()
    if not key:
        raise RuntimeError("Storage key unavailable")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def upload_image_bytes(data: bytes, mime: str = "image/png", prefix: str = "trailers") -> dict:
    """Upload bytes and return {'storage_path': str, 'size': int}. Raises on failure."""
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "bin")
    path = f"{APP_NAME}/{prefix}/{uuid.uuid4()}.{ext}"
    result = put_object(path, data, mime)
    return {"storage_path": result.get("path", path), "size": result.get("size", len(data)), "mime": mime}
