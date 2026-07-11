"""Built-in chat artifact registry.

Chat artifacts are structured, visual payloads an agent can attach to a reply
(rendered by the widget as rich components — e.g. the Lal Kitab kundali
chart). Which artifacts an agent emits is configurable per agent from the
admin under `configuration.artifacts`:

    "artifacts": {
        "kundali_chart": {"enabled": false, "options": {"style": "north_indian"}}
    }

Absent config falls back to each artifact's `default_enabled`, so existing
agents keep working without a config migration. The registry is the single
source of truth the admin UI lists artifact types from — adding a new
artifact type here makes it configurable everywhere.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


BUILT_IN_ARTIFACT_TYPES: dict[str, dict[str, Any]] = {
    "kundali_chart": {
        "id": "kundali_chart",
        "name": "Kundali Chart",
        "description": (
            "North-Indian style Lal Kitab kundali diagram rendered as a visual "
            "artifact above the astrologer's reading. Built only from the "
            "calculated chart context — never guessed."
        ),
        # Templates this artifact applies to. Empty list = applies to any agent.
        "applies_to_templates": ["astrology_lalkitab"],
        "default_enabled": True,
        "options_schema": {
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": ["north_indian"],
                    "default": "north_indian",
                    "description": "Chart drawing style.",
                },
            },
        },
        "default_options": {"style": "north_indian"},
    },
}


def list_artifact_types() -> list[dict[str, Any]]:
    """All built-in artifact types, for the admin UI."""
    return [deepcopy(artifact) for artifact in BUILT_IN_ARTIFACT_TYPES.values()]


def get_artifact_type(artifact_id: str) -> dict[str, Any] | None:
    artifact = BUILT_IN_ARTIFACT_TYPES.get(artifact_id)
    return deepcopy(artifact) if artifact else None


def _agent_template(config: dict[str, Any] | None) -> str:
    config = config or {}
    domain = config.get("domain") if isinstance(config.get("domain"), dict) else {}
    return str(
        domain.get("template")
        or config.get("agent_template")
        or config.get("template")
        or "generic"
    ).lower()


def artifact_types_for_config(config: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Artifact types applicable to this agent's template."""
    template = _agent_template(config)
    applicable = []
    for artifact in BUILT_IN_ARTIFACT_TYPES.values():
        templates = artifact.get("applies_to_templates") or []
        if not templates or template in templates:
            applicable.append(deepcopy(artifact))
    return applicable


def resolve_artifact_settings(config: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Merge per-agent artifact config onto registry defaults.

    Returns {artifact_id: {"enabled": bool, "options": {...}}} for every
    artifact type applicable to the agent.
    """
    config = config or {}
    stored = config.get("artifacts") if isinstance(config.get("artifacts"), dict) else {}
    resolved: dict[str, dict[str, Any]] = {}
    for artifact in artifact_types_for_config(config):
        artifact_id = artifact["id"]
        entry = stored.get(artifact_id) if isinstance(stored.get(artifact_id), dict) else {}
        options = dict(artifact.get("default_options") or {})
        if isinstance(entry.get("options"), dict):
            options.update({k: v for k, v in entry["options"].items() if v is not None})
        enabled = entry.get("enabled")
        if not isinstance(enabled, bool):
            enabled = bool(artifact.get("default_enabled", True))
        resolved[artifact_id] = {"enabled": enabled, "options": options}
    return resolved


def is_artifact_enabled(config: dict[str, Any] | None, artifact_id: str) -> bool:
    """Whether this agent should emit the given artifact (default-on unless
    the artifact type doesn't apply to the agent or admin disabled it)."""
    settings = resolve_artifact_settings(config)
    entry = settings.get(artifact_id)
    return bool(entry and entry.get("enabled"))


def artifact_options(config: dict[str, Any] | None, artifact_id: str) -> dict[str, Any]:
    settings = resolve_artifact_settings(config)
    entry = settings.get(artifact_id) or {}
    return dict(entry.get("options") or {})
