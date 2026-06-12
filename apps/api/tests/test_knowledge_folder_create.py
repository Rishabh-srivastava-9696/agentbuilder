"""Regression test for the knowledge-folder create crash.

create_folder used an upsert that put `updated_at` in BOTH $setOnInsert (via the
full folder doc) and $set. MongoDB rejects the same field path in both update
operators (WriteError 40), so every folder create threw and no folder ever
persisted — which made the whole KB folder tree appear empty and forced all
uploads into root. This test pins the update operators so the conflict can't
return.
"""

from __future__ import annotations

import pytest

from app.services.knowledge_service import KnowledgeService


class CapturingCollection:
    def __init__(self):
        self.update_calls = []

    async def update_one(self, filter_, update, upsert=False):
        self.update_calls.append({"filter": filter_, "update": update, "upsert": upsert})


@pytest.mark.asyncio
async def test_create_folder_does_not_conflict_updated_at(monkeypatch):
    service = KnowledgeService.__new__(KnowledgeService)

    async def fake_scope(identifier):
        return {"brand_id": "brand-1", "brand_slug": "brand-1", "aliases": ["brand-1"], "db_name": "brand-1"}

    collection = CapturingCollection()

    async def fake_folders_collection(brand_id):
        return collection

    monkeypatch.setattr(service, "_resolve_brand_scope", fake_scope)
    monkeypatch.setattr(service, "_get_knowledge_folders_collection", fake_folders_collection)

    result = await service.create_folder(brand_id="brand-1", path="/guides", agent_id=None)

    assert result["path"] == "/guides"
    assert result["type"] == "folder"
    assert len(collection.update_calls) == 1

    update = collection.update_calls[0]["update"]
    set_on_insert = update["$setOnInsert"]
    set_fields = update["$set"]

    # The exact Mongo-40 trigger: updated_at must not be in both operators.
    assert "updated_at" not in set_on_insert
    assert "updated_at" in set_fields
    # Insert-only fields still carry the folder identity.
    assert set_on_insert["path"] == "/guides"
    assert set_on_insert["parent_path"] == "/"
    assert collection.update_calls[0]["upsert"] is True


@pytest.mark.asyncio
async def test_create_folder_rejects_root(monkeypatch):
    service = KnowledgeService.__new__(KnowledgeService)
    with pytest.raises(ValueError):
        await service.create_folder(brand_id="brand-1", path="/", agent_id=None)
