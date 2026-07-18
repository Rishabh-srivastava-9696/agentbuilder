"""Durable ingestion-job state with Redis as a best-effort cache.

MongoDB's system database is the authoritative source for job state so that a
job can be read by another API worker. Redis speeds up reads but is never the
only copy while the system database is available. The process-local fallback
is deliberately limited to isolated development and tests where both MongoDB
and Redis are unavailable.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import structlog

from ..connections import connection_manager

logger = structlog.get_logger()

JOB_TTL_SECONDS = 86400  # 24 hours
KEY_PREFIX = "job:"
JOBS_COLLECTION = "ingestion_jobs"
_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_TIMESTAMP_FIELDS = {"created_at", "updated_at", "completed_at", "cancelled_at"}
_IMMUTABLE_FIELDS = {"agent_id", "brand_id"}


class JobStoreUnavailableError(RuntimeError):
    """Raised when a durable job store is configured but cannot be reached."""


class JobStore:
    """Persist ingestion jobs in MongoDB and cache complete documents in Redis."""

    def __init__(self):
        self._fallback: Dict[str, Dict[str, Any]] = {}
        self._indexes_checked = False

    def _key(self, job_id: str) -> str:
        return f"{KEY_PREFIX}{job_id}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def _utc_timestamp(cls, value: datetime | None = None) -> str:
        timestamp = value or cls._utc_now()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @classmethod
    def _normalize_timestamp(cls, value: Any, default: str) -> str:
        if isinstance(value, datetime):
            return cls._utc_timestamp(value)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return default
            return cls._utc_timestamp(parsed)
        return default

    @staticmethod
    def _validate_job_id(job_id: str) -> str:
        if not isinstance(job_id, str) or not _JOB_ID_PATTERN.fullmatch(job_id):
            raise ValueError("Invalid job identifier")
        return job_id

    def _get_collection(self):
        """Return the system job collection, or ``None`` when Mongo is offline."""
        try:
            return connection_manager.get_system_db()[JOBS_COLLECTION]
        except (RuntimeError, AttributeError, KeyError, TypeError):
            return None

    async def _ensure_indexes(self, collection: Any) -> None:
        """Best-effort TTL index; job writes must not fail on index setup."""
        if self._indexes_checked:
            return
        self._indexes_checked = True
        try:
            await collection.create_index(
                "expires_at",
                expireAfterSeconds=0,
                name="ingestion_jobs_expiry_idx",
            )
        except Exception as exc:
            logger.warning(
                "job_store_index_setup_failed",
                error_type=type(exc).__name__,
            )

    @classmethod
    def _document_for_cache(cls, job_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
        cached = dict(document)
        cached.pop("_id", None)
        cached["job_id"] = job_id
        for field in _TIMESTAMP_FIELDS | {"expires_at"}:
            value = cached.get(field)
            if isinstance(value, datetime):
                cached[field] = cls._utc_timestamp(value)
        return cached

    @classmethod
    def _cache_ttl(cls, document: Dict[str, Any]) -> int:
        expires_at = document.get("expires_at")
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except ValueError:
                expires_at = None
        if isinstance(expires_at, datetime):
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            remaining = int((expires_at - cls._utc_now()).total_seconds())
            return max(1, remaining)
        return JOB_TTL_SECONDS

    async def _cache_set(self, job_id: str, document: Dict[str, Any]) -> bool:
        redis = connection_manager.redis_client
        if redis is None:
            return False
        try:
            cached = self._document_for_cache(job_id, document)
            await redis.set(
                self._key(job_id),
                json.dumps(cached, default=str),
                ex=self._cache_ttl(document),
            )
            return True
        except Exception as exc:
            logger.warning(
                "job_store_redis_write_failed",
                job_id=job_id,
                error_type=type(exc).__name__,
            )
            return False

    async def _cache_get(self, job_id: str) -> tuple[Optional[Dict[str, Any]], bool]:
        redis = connection_manager.redis_client
        if redis is None:
            return None, False
        try:
            raw = await redis.get(self._key(job_id))
            if not raw:
                return None, True
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            document = json.loads(raw)
            if not isinstance(document, dict):
                raise ValueError("Cached job value is not an object")
            return self._document_for_cache(job_id, document), True
        except Exception as exc:
            logger.warning(
                "job_store_redis_read_failed",
                job_id=job_id,
                error_type=type(exc).__name__,
            )
            return None, False

    async def _cache_delete(self, job_id: str) -> bool:
        redis = connection_manager.redis_client
        if redis is None:
            return False
        try:
            await redis.delete(self._key(job_id))
            return True
        except Exception as exc:
            logger.warning(
                "job_store_redis_delete_failed",
                job_id=job_id,
                error_type=type(exc).__name__,
            )
            return False

    async def _read_db_document(self, collection: Any, job_id: str) -> Optional[Dict[str, Any]]:
        try:
            document = await collection.find_one({"_id": job_id})
        except Exception as exc:
            logger.warning(
                "job_store_mongodb_read_failed",
                job_id=job_id,
                error_type=type(exc).__name__,
            )
            raise JobStoreUnavailableError("Durable job storage is unavailable") from exc
        return self._document_for_cache(job_id, document) if document else None

    def _write_payload(self, job_id: str, data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        now = self._utc_timestamp()
        payload = dict(data)
        payload.pop("_id", None)
        payload.pop("job_id", None)
        payload.pop("expires_at", None)

        created_at = self._normalize_timestamp(payload.pop("created_at", None), now)
        for field in _TIMESTAMP_FIELDS - {"created_at", "updated_at"}:
            if field in payload and payload[field] is not None:
                payload[field] = self._normalize_timestamp(payload[field], now)

        payload["job_id"] = job_id
        payload["updated_at"] = now
        insert_fields = {
            "created_at": created_at,
            "expires_at": self._utc_now() + timedelta(seconds=JOB_TTL_SECONDS),
        }
        return payload, insert_fields

    async def set(self, job_id: str, data: Dict[str, Any]) -> None:
        """Create or merge a job document without replacing required fields."""
        job_id = self._validate_job_id(job_id)
        payload, insert_fields = self._write_payload(job_id, data)
        for field in _IMMUTABLE_FIELDS:
            if field in payload:
                insert_fields[field] = payload.pop(field)
        collection = self._get_collection()

        if collection is not None:
            await self._ensure_indexes(collection)
            try:
                await collection.update_one(
                    {"_id": job_id},
                    {"$set": payload, "$setOnInsert": insert_fields},
                    upsert=True,
                )
            except Exception as exc:
                logger.warning(
                    "job_store_mongodb_write_failed",
                    job_id=job_id,
                    error_type=type(exc).__name__,
                )
                raise JobStoreUnavailableError("Durable job storage is unavailable") from exc

            document = await self._read_db_document(collection, job_id)
            if document:
                if not await self._cache_set(job_id, document):
                    await self._cache_delete(job_id)
            else:
                await self._cache_delete(job_id)
            self._fallback.pop(job_id, None)
            return

        fallback_document = dict(insert_fields)
        fallback_document.update(payload)
        if not await self._cache_set(job_id, fallback_document):
            self._fallback[job_id] = fallback_document

    async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Read cached state first, falling back to MongoDB and repopulating Redis."""
        try:
            job_id = self._validate_job_id(job_id)
        except ValueError:
            return None

        cached, redis_available = await self._cache_get(job_id)
        if cached is not None:
            return cached

        collection = self._get_collection()
        if collection is not None:
            document = await self._read_db_document(collection, job_id)
            if document:
                if not await self._cache_set(job_id, document):
                    await self._cache_delete(job_id)
                self._fallback.pop(job_id, None)
            return document

        if redis_available:
            return None
        fallback = self._fallback.get(job_id)
        return self._document_for_cache(job_id, fallback) if fallback else None

    async def update(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Atomically update existing durable state while preserving other fields."""
        try:
            job_id = self._validate_job_id(job_id)
        except ValueError:
            return False

        payload, _ = self._write_payload(job_id, updates)
        for field in _IMMUTABLE_FIELDS:
            payload.pop(field, None)
        collection = self._get_collection()
        if collection is not None:
            try:
                result = await collection.update_one({"_id": job_id}, {"$set": payload})
            except Exception as exc:
                logger.warning(
                    "job_store_mongodb_update_failed",
                    job_id=job_id,
                    error_type=type(exc).__name__,
                )
                raise JobStoreUnavailableError("Durable job storage is unavailable") from exc

            if getattr(result, "matched_count", 1) == 0:
                await self._cache_delete(job_id)
                return False

            document = await self._read_db_document(collection, job_id)
            if document:
                if not await self._cache_set(job_id, document):
                    await self._cache_delete(job_id)
            else:
                await self._cache_delete(job_id)
                return False
            self._fallback.pop(job_id, None)
            return True

        cached, redis_available = await self._cache_get(job_id)
        if cached is not None:
            cached.update(payload)
            await self._cache_set(job_id, cached)
            return True
        if redis_available:
            return False

        fallback = self._fallback.get(job_id)
        if fallback is None:
            return False
        fallback.update(payload)
        return True

    async def delete(self, job_id: str) -> bool:
        """Remove a job from MongoDB and Redis, regardless of cache availability."""
        try:
            job_id = self._validate_job_id(job_id)
        except ValueError:
            return False

        collection = self._get_collection()
        db_error: Exception | None = None
        deleted = False
        if collection is not None:
            try:
                result = await collection.delete_one({"_id": job_id})
                deleted = bool(getattr(result, "deleted_count", 1))
            except Exception as exc:
                db_error = exc
                logger.warning(
                    "job_store_mongodb_delete_failed",
                    job_id=job_id,
                    error_type=type(exc).__name__,
                )

        cache_deleted = await self._cache_delete(job_id)
        fallback_deleted = self._fallback.pop(job_id, None) is not None

        if db_error is not None:
            raise JobStoreUnavailableError("Durable job storage is unavailable") from db_error
        if collection is not None:
            return deleted
        return cache_deleted or fallback_deleted
