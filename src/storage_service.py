from __future__ import annotations

"""
Storage service for uploading captures to Supabase Storage and logging DB entries.

Relies on an existing Supabase client adapter providing:
- create_pilab_client() -> client
- A client with:
  - storage_upload(bucket: str, key: str, data: bytes, *, upsert: bool = False, make_public: bool | None = None) -> dict
  - db_insert(table: str, record: dict) -> dict
  - optional helpers or properties for convenience

If your adapter exposes different method names, adapt the calls in upload_and_log().
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def _infer_tag_from_path(local_path: Path) -> Optional[str]:
    """
    Attempt to infer tag by parsing parent directory name:
      YYYY-MM-DD or YYYY-MM-DD_<tag>

    Returns a tag string if found, else None.
    """
    parent = local_path.parent.name
    if "_" in parent:
        parts = parent.split("_", 1)
        if len(parts) == 2 and parts[0].count("-") == 2:
            return parts[1] or None
    return None


def _build_remote_key(local_path: Path, *, prefix: str = "") -> str:
    """
    Build remote storage key mirroring local folder structure relative to the captures root.
    Uses the last two path components: day_folder and filename.
    Example:
      local: ./captures/2025-08-01_testname/HHMMSS_xxxxxx.jpg
      key:   [prefix/]2025-08-01_testname/HHMMSS_xxxxxx.jpg
    """
    day_folder = local_path.parent.name
    filename = local_path.name
    key = f"{day_folder}/{filename}"
    if prefix:
        key = f"{prefix.rstrip('/')}/{key}"
    return key


def upload_and_log(
    local_path: Path,
    *,
    supa,
    bucket: str,
    table: str,
    metadata: Optional[Dict[str, Any]] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Upload a file to Supabase Storage and insert a DB row.

    Args:
      local_path: Path to the locally saved capture
      supa: Supabase client adapter instance
      bucket: Storage bucket name
      table: Database table for logging rows
      metadata: Extra fields to include in the DB record (dict)
      cfg: Policy/behavior flags, e.g.:
           {
             "prefix": "captures",
             "upsert": False,
             "make_public": False
           }

    Returns:
      {
        "ok": bool,
        "remote_path": str | None,
        "record": dict | None,
        "error": str | None
      }
    """
    result: Dict[str, Any] = {"ok": False, "remote_path": None, "record": None, "error": None}

    try:
        local_path = Path(local_path)
        if not local_path.exists() or not local_path.is_file():
            result["error"] = f"Local file not found: {local_path}"
            logger.error(result["error"])
            return result

        cfg = cfg or {}
        prefix = cfg.get("prefix", "")
        upsert = bool(cfg.get("upsert", False))
        make_public = cfg.get("make_public", None)

        # Read file bytes
        data = local_path.read_bytes()

        # Compute remote key
        key = _build_remote_key(local_path, prefix=prefix)

        # Upload to storage
        logger.info(f"Uploading to storage bucket={bucket}, key={key}, upsert={upsert}")
        # Expecting adapter method like: storage_upload(bucket, key, data, upsert=False, make_public=None)
        upload_resp = supa.storage_upload(bucket, key, data, upsert=upsert, make_public=make_public)
        if isinstance(upload_resp, dict) and upload_resp.get("error"):
            result["error"] = f"Storage upload failed: {upload_resp['error']}"
            logger.error(result["error"])
            return result

        # Prepare DB record
        now_utc = datetime.utcnow().isoformat()
        tag = _infer_tag_from_path(local_path)

        record = {
            "local_path": str(local_path),
            "storage_bucket": bucket,
            "storage_key": key,
            "created_at": now_utc,
            "tag": tag,
        }
        if metadata:
            # Merge metadata keys without clobbering core fields
            for k, v in metadata.items():
                if k not in record:
                    record[k] = v

        logger.info(f"Inserting DB record into table={table}")
        # Expecting adapter method like: db_insert(table, record) -> dict
        db_resp = supa.db_insert(table, record)
        if isinstance(db_resp, dict) and db_resp.get("error"):
            result["error"] = f"DB insert failed after successful upload: {db_resp['error']}"
            logger.error(result["error"])
            # We do not delete the uploaded file here; caller can decide remediation
            return result

        result["ok"] = True
        result["remote_path"] = key
        result["record"] = db_resp if db_resp is not None else {"inserted": True}
        logger.info(f"upload_and_log() succeeded: key={key}")
        return result

    except Exception as e:
        logger.exception("upload_and_log() error")
        result["error"] = str(e)
        return result
