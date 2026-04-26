import pytest

from app.services.strapi_client import StrapiClient


@pytest.mark.asyncio
async def test_sync_saves_turn_messages_sequentially(monkeypatch):
    client = StrapiClient("http://strapi.local", "token")
    events = []

    async def fake_ensure_session(*_args, **_kwargs):
        events.append("session")

    async def fake_save_message(_conversation_id, _content, role, **_kwargs):
        events.append(f"{role}:start")
        if role == "user":
            assert "agent:start" not in events
        events.append(f"{role}:end")

    monkeypatch.setattr(client, "_ensure_session", fake_ensure_session)
    monkeypatch.setattr(client, "_save_message", fake_save_message)

    await client._sync("conv-1", "hello", "hi", brand_slug="essco-bathware", agent_id="agent-1")

    assert events == ["session", "user:start", "user:end", "agent:start", "agent:end"]


@pytest.mark.asyncio
async def test_message_sync_error_records_role(monkeypatch):
    client = StrapiClient("http://strapi.local", "token")
    recorded_events = []

    async def allow_sync(*_args, **_kwargs):
        return True

    async def fail_post(*_args, **_kwargs):
        raise RuntimeError("strapi down")

    async def record_sync_event(*args, **kwargs):
        recorded_events.append((args, kwargs))

    monkeypatch.setattr(client, "_allow_sync", allow_sync)
    monkeypatch.setattr(client, "_post_with_retry", fail_post)
    monkeypatch.setattr(client, "_record_sync_event", record_sync_event)

    await client._save_message("conv-1", "hello", "agent", brand_slug="essco-bathware", agent_id="agent-1")

    assert recorded_events[0][0][:3] == ("message", "error", "conv-1")
    assert recorded_events[0][1]["role"] == "agent"
    assert recorded_events[0][1]["error"] == "strapi down"
