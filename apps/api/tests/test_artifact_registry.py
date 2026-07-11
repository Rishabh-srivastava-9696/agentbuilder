"""Artifact registry: admin-configurable chat artifacts per agent."""
from app.services.artifact_registry import (
    artifact_options,
    artifact_types_for_config,
    is_artifact_enabled,
    list_artifact_types,
    resolve_artifact_settings,
)


LALKITAB_CONFIG = {"domain": {"template": "astrology_lalkitab"}}


def test_registry_lists_kundali_chart():
    types = list_artifact_types()
    ids = [t["id"] for t in types]
    assert "kundali_chart" in ids


def test_kundali_applies_only_to_lalkitab_template():
    assert [t["id"] for t in artifact_types_for_config(LALKITAB_CONFIG)] == ["kundali_chart"]
    assert artifact_types_for_config({"domain": {"template": "ecommerce"}}) == []
    assert artifact_types_for_config({}) == []


def test_kundali_enabled_by_default_for_lalkitab_agents():
    assert is_artifact_enabled(LALKITAB_CONFIG, "kundali_chart") is True
    # Not applicable to other templates → not emitted.
    assert is_artifact_enabled({"domain": {"template": "generic"}}, "kundali_chart") is False


def test_admin_can_disable_artifact():
    config = {**LALKITAB_CONFIG, "artifacts": {"kundali_chart": {"enabled": False}}}
    assert is_artifact_enabled(config, "kundali_chart") is False


def test_admin_options_merge_onto_defaults():
    config = {
        **LALKITAB_CONFIG,
        "artifacts": {"kundali_chart": {"enabled": True, "options": {"style": "north_indian"}}},
    }
    assert artifact_options(config, "kundali_chart") == {"style": "north_indian"}
    # Defaults survive when options are omitted.
    assert artifact_options(LALKITAB_CONFIG, "kundali_chart")["style"] == "north_indian"


def test_resolve_settings_handles_malformed_config():
    config = {**LALKITAB_CONFIG, "artifacts": {"kundali_chart": "yes"}}
    settings = resolve_artifact_settings(config)
    assert settings["kundali_chart"]["enabled"] is True  # falls back to default
