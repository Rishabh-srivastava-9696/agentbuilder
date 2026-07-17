"""Artifact registry: admin-configurable chat artifacts per agent."""
from app.services.artifact_registry import (
    artifact_options,
    artifact_types_for_config,
    is_artifact_enabled,
    list_artifact_types,
    normalize_agent_template,
    resolve_artifact_settings,
)
from app.services.lalkitab_runtime import is_lalkitab_agent


LALKITAB_CONFIG = {"domain": {"template": "astrology_lalkitab"}}


def test_registry_lists_kundali_chart():
    types = list_artifact_types()
    ids = [t["id"] for t in types]
    assert "kundali_chart" in ids


def test_kundali_applies_only_to_lalkitab_template():
    assert [t["id"] for t in artifact_types_for_config(LALKITAB_CONFIG)] == ["kundali_chart"]
    assert artifact_types_for_config({"domain": {"template": "ecommerce"}}) == []
    assert artifact_types_for_config({}) == []


def test_lalkitab_template_aliases_normalize_to_canonical_id():
    for alias in (
        "lalkitab",
        "lal_kitab",
        "lal-kitab",
        "lal kitab",
        "astrology_lal_kitab",
        "astrology-lal-kitab",
        "lalkitab_astrology",
    ):
        assert normalize_agent_template(alias) == "astrology_lalkitab"
        assert artifact_types_for_config({"domain": {"template": alias}})[0]["id"] == "kundali_chart"
        assert is_lalkitab_agent({"domain": {"template": alias}}) is True

    assert normalize_agent_template("astrology") == "astrology"


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
    assert resolve_artifact_settings({"domain": "not-an-object", "artifacts": []}) == {}
    assert resolve_artifact_settings(None) == {}


def test_non_lalkitab_artifact_defaults_to_disabled_and_legacy_config_is_preserved():
    assert is_artifact_enabled({"domain": {"template": "ecommerce"}}, "kundali_chart") is False
    config = {
        "domain": {"template": "lal_kitab"},
        "artifacts": {"kundali_chart": {"enabled": False, "options": {"style": "north_indian"}}},
    }
    assert resolve_artifact_settings(config)["kundali_chart"] == {
        "enabled": False,
        "options": {"style": "north_indian"},
    }


def test_admin_artifact_route_returns_registry_shape():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1.admin.artifacts import router
    from app.auth.dependencies import require_dashboard_access

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/admin/artifacts")
    app.dependency_overrides[require_dashboard_access] = lambda: None

    response = TestClient(app).get("/api/v1/admin/artifacts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["artifacts"][0]["id"] == "kundali_chart"
    assert payload["artifacts"][0]["options_schema"]["properties"]["style"]["enum"] == ["north_indian"]
