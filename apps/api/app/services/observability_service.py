"""
Per-agent observability events and summaries.

Prometheus remains the low-cardinality service-health layer. This service stores
agent-scoped reliability events in each brand database so the dashboard can show
responsible-AI metrics by brand, agent, and time range without putting agent_id
labels into Prometheus.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from ..connections import connection_manager

logger = structlog.get_logger(__name__)

COLLECTION_NAME = "observability_events"
_indexed_brand_dbs: set[str] = set()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_number(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


class ObservabilityService:
    async def _ensure_indexes(self, brand_slug: str) -> None:
        db = connection_manager.get_brand_db(brand_slug)
        db_name = db.name
        if db_name in _indexed_brand_dbs:
            return

        collection = db[COLLECTION_NAME]
        await collection.create_index([("timestamp", -1)])
        await collection.create_index([("agent_id", 1), ("timestamp", -1)])
        await collection.create_index([("event_type", 1), ("timestamp", -1)])
        await collection.create_index([("conversation_id", 1), ("timestamp", -1)])
        _indexed_brand_dbs.add(db_name)
        logger.info("observability_indexes_created", brand_slug=brand_slug)

    async def track_event(
        self,
        *,
        event_type: str,
        brand_slug: str | None,
        agent_id: str | None,
        conversation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if not brand_slug or not agent_id:
            return

        try:
            await self._ensure_indexes(brand_slug)
            db = connection_manager.get_brand_db(brand_slug)
            await db[COLLECTION_NAME].insert_one({
                "id": str(uuid.uuid4()),
                "event_type": event_type,
                "brand_slug": brand_slug,
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "payload": payload or {},
                "timestamp": _utc_now(),
            })
        except Exception as exc:
            logger.warning(
                "observability_event_write_failed",
                event_type=event_type,
                brand_slug=brand_slug,
                agent_id=agent_id,
                error=str(exc),
            )

    async def summarize(
        self,
        *,
        brand_slug: str | None = None,
        agent_id: str | None = None,
        range_hours: int = 24,
    ) -> dict[str, Any]:
        range_hours = max(1, min(int(range_hours or 24), 24 * 30))
        from_ts = _utc_now() - timedelta(hours=range_hours)
        to_ts = _utc_now()

        agents = await self._list_agents(brand_slug=brand_slug, agent_id=agent_id)
        brands = await self._list_brands()
        events = await self._load_events(agents, from_ts=from_ts, to_ts=to_ts)

        totals = self._build_totals(events)
        sections = self._build_sections(events)
        agent_rows = self._build_agent_rows(events, agents, brands)

        return {
            "filters": {
                "brand_slug": brand_slug,
                "agent_id": agent_id,
                "range_hours": range_hours,
                "from": from_ts.isoformat(),
                "to": to_ts.isoformat(),
            },
            "brands": sorted(brands.values(), key=lambda brand: brand["name"].lower()),
            "agents": agent_rows,
            "totals": totals,
            "sections": sections,
        }

    async def _list_agents(
        self,
        *,
        brand_slug: str | None,
        agent_id: str | None,
    ) -> list[dict[str, Any]]:
        system_db = connection_manager.get_system_db()
        query: dict[str, Any] = {}
        if brand_slug:
            query["brand_slug"] = brand_slug
        if agent_id:
            query["id"] = agent_id

        cursor = system_db.agents.find(
            query,
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "brand_id": 1,
                "brand_slug": 1,
                "status": 1,
            },
        )
        return await cursor.to_list(length=None)

    async def _list_brands(self) -> dict[str, dict[str, str]]:
        system_db = connection_manager.get_system_db()
        cursor = system_db.brands.find({}, {"_id": 0, "id": 1, "name": 1, "slug": 1})
        rows = await cursor.to_list(length=None)
        return {
            row.get("slug") or row.get("id"): {
                "id": row.get("id", ""),
                "name": row.get("name") or row.get("slug") or "Unknown brand",
                "slug": row.get("slug") or row.get("id") or "",
            }
            for row in rows
            if row.get("slug") or row.get("id")
        }

    async def _load_events(
        self,
        agents: list[dict[str, Any]],
        *,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[dict[str, Any]]:
        agent_ids_by_brand: dict[str, list[str]] = defaultdict(list)
        for agent in agents:
            if agent.get("brand_slug") and agent.get("id"):
                agent_ids_by_brand[agent["brand_slug"]].append(agent["id"])

        events: list[dict[str, Any]] = []
        for brand_slug, agent_ids in agent_ids_by_brand.items():
            try:
                await self._ensure_indexes(brand_slug)
                db = connection_manager.get_brand_db(brand_slug)
                query = {
                    "timestamp": {"$gte": from_ts, "$lte": to_ts},
                    "agent_id": {"$in": agent_ids},
                }
                rows = await db[COLLECTION_NAME].find(query, {"_id": 0}).to_list(length=20000)
                events.extend(rows)
            except Exception as exc:
                logger.warning("observability_event_read_failed", brand_slug=brand_slug, error=str(exc))
        return events

    def _build_totals(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        message_events = [event for event in events if event.get("event_type") == "message_processed"]
        guardrail_events = [event for event in events if event.get("event_type") == "guardrail_decision"]
        fallback_events = [event for event in events if event.get("event_type") == "fallback_used"]
        rate_limit_blocks = [
            event for event in events
            if event.get("event_type") == "rate_limit" and event.get("payload", {}).get("outcome") == "blocked"
        ]
        strapi_errors = [
            event for event in events
            if event.get("event_type") == "strapi_sync" and event.get("payload", {}).get("status") != "success"
        ]

        grounded_count = sum(1 for event in message_events if event.get("payload", {}).get("grounded"))
        low_confidence_count = sum(
            1 for event in message_events
            if event.get("payload", {}).get("low_confidence_prevented")
        )
        latency_values = [
            _safe_number(event.get("payload", {}).get("latency_ms"))
            for event in message_events
            if event.get("payload", {}).get("latency_ms") is not None
        ]
        confidence_values = [
            _safe_number(event.get("payload", {}).get("confidence_score"))
            for event in message_events
            if event.get("payload", {}).get("confidence_score") is not None
        ]

        return {
            "messages": len(message_events),
            "grounded": grounded_count,
            "grounded_rate": grounded_count / len(message_events) if message_events else 0,
            "low_confidence_prevented": low_confidence_count,
            "guardrails": len(guardrail_events),
            "fallbacks": len(fallback_events),
            "rate_limit_blocks": len(rate_limit_blocks),
            "strapi_errors": len(strapi_errors),
            "avg_latency_ms": sum(latency_values) / len(latency_values) if latency_values else 0,
            "avg_confidence": sum(confidence_values) / len(confidence_values) if confidence_values else 0,
        }

    def _build_sections(self, events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]] | dict[str, Any]]:
        return {
            "rate_limits": self._count_rows(events, "rate_limit", ["policy", "outcome"]),
            "guardrails": self._count_rows(events, "guardrail_decision", ["action", "reason"]),
            "fallbacks": self._count_rows(events, "fallback_used", ["stage", "reason"]),
            "strapi_sync": self._count_rows(events, "strapi_sync", ["operation", "status"]),
            "latency": self._latency_rows(events),
            "hallucination": self._hallucination_summary(events),
        }

    def _count_rows(
        self,
        events: list[dict[str, Any]],
        event_type: str,
        fields: list[str],
    ) -> list[dict[str, Any]]:
        counts: dict[tuple[str, ...], int] = defaultdict(int)
        for event in events:
            if event.get("event_type") != event_type:
                continue
            payload = event.get("payload", {})
            key = tuple(str(payload.get(field) or "unknown") for field in fields)
            counts[key] += 1

        rows = []
        for key, count in counts.items():
            row = {field: key[index] for index, field in enumerate(fields)}
            row["count"] = count
            rows.append(row)
        return sorted(rows, key=lambda row: row["count"], reverse=True)

    def _latency_rows(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        buckets: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"count": 0, "total_ms": 0})
        for event in events:
            if event.get("event_type") != "message_processed":
                continue
            payload = event.get("payload", {})
            key = (str(payload.get("mode") or "unknown"), str(payload.get("status") or "unknown"))
            buckets[key]["count"] += 1
            buckets[key]["total_ms"] += _safe_number(payload.get("latency_ms"))

        rows = []
        for (mode, status), data in buckets.items():
            count = data["count"]
            rows.append({
                "mode": mode,
                "status": status,
                "count": count,
                "average_ms": data["total_ms"] / count if count else 0,
            })
        return sorted(rows, key=lambda row: row["count"], reverse=True)

    def _hallucination_summary(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        message_events = [event for event in events if event.get("event_type") == "message_processed"]
        if not message_events:
            return {
                "responses_checked": 0,
                "grounded": 0,
                "ungrounded": 0,
                "low_confidence_prevented": 0,
                "avg_confidence": 0,
                "citations": 0,
            }

        grounded = sum(1 for event in message_events if event.get("payload", {}).get("grounded"))
        low_confidence_prevented = sum(
            1 for event in message_events
            if event.get("payload", {}).get("low_confidence_prevented")
        )
        confidence_values = [
            _safe_number(event.get("payload", {}).get("confidence_score"))
            for event in message_events
        ]
        citations = sum(int(_safe_number(event.get("payload", {}).get("citations_count"))) for event in message_events)
        return {
            "responses_checked": len(message_events),
            "grounded": grounded,
            "ungrounded": len(message_events) - grounded,
            "low_confidence_prevented": low_confidence_prevented,
            "avg_confidence": sum(confidence_values) / len(confidence_values),
            "citations": citations,
        }

    def _build_agent_rows(
        self,
        events: list[dict[str, Any]],
        agents: list[dict[str, Any]],
        brands: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        events_by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            if event.get("agent_id"):
                events_by_agent[event["agent_id"]].append(event)

        rows = []
        for agent in agents:
            agent_events = events_by_agent.get(agent.get("id"), [])
            totals = self._build_totals(agent_events)
            brand = brands.get(agent.get("brand_slug"), {})
            rows.append({
                "agent_id": agent.get("id"),
                "agent_name": agent.get("name") or "Unnamed agent",
                "agent_status": agent.get("status") or "unknown",
                "brand_slug": agent.get("brand_slug"),
                "brand_name": brand.get("name") or agent.get("brand_slug") or "Unknown brand",
                **totals,
            })

        return sorted(rows, key=lambda row: (row["messages"], row["guardrails"], row["fallbacks"]), reverse=True)
