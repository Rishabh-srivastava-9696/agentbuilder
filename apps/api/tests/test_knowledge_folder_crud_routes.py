"""Routing/contract tests for folder filesystem CRUD.

Folder ids are paths with slashes ("/Guides"). They used to ride in the URL path
param (`/items/{item_id}/move`), which broke routing once the slash was encoded —
that was the 404. These tests pin the body/query-based routes that carry the id
safely, and that delete is folder-aware (delete_item, not delete_document).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import knowledge as knowledge_module
from app.auth.dependencies import require_dashboard_access
from app.dependencies import get_knowledge_service


@pytest.fixture
def client_and_service():
    service = AsyncMock()
    app = FastAPI()
    app.include_router(knowledge_module.router, prefix="/api/v1/knowledge")
    app.dependency_overrides[require_dashboard_access] = lambda: None
    app.dependency_overrides[get_knowledge_service] = lambda: service
    return TestClient(app), service


def test_move_by_body_passes_slash_folder_id(client_and_service):
    client, service = client_and_service
    service.move_item.return_value = {"id": "/Reports/Guides", "type": "folder", "path": "/Reports/Guides"}

    resp = client.patch(
        "/api/v1/knowledge/items/move",
        json={"brand_id": "b1", "item_id": "/Guides", "target_folder": "/Reports"},
    )

    assert resp.status_code == 200
    # The slash-bearing folder id reached the service intact — the original bug.
    kwargs = service.move_item.call_args.kwargs
    assert kwargs["item_id"] == "/Guides"
    assert kwargs["target_folder"] == "/Reports"


def test_move_by_body_requires_item_id(client_and_service):
    client, _ = client_and_service
    resp = client.patch("/api/v1/knowledge/items/move", json={"brand_id": "b1", "target_folder": "/x"})
    assert resp.status_code == 400


def test_move_into_itself_is_400(client_and_service):
    client, service = client_and_service
    service.move_item.side_effect = ValueError("Cannot move a folder into itself")
    resp = client.patch(
        "/api/v1/knowledge/items/move",
        json={"brand_id": "b1", "item_id": "/Guides", "target_folder": "/Guides/sub"},
    )
    assert resp.status_code == 400


def test_rename_by_body_passes_slash_folder_id(client_and_service):
    client, service = client_and_service
    service.rename_item.return_value = {"id": "/Manuals", "type": "folder", "name": "Manuals", "path": "/Manuals"}

    resp = client.patch(
        "/api/v1/knowledge/items/rename",
        json={"brand_id": "b1", "item_id": "/Guides", "name": "Manuals"},
    )

    assert resp.status_code == 200
    assert service.rename_item.call_args.kwargs["item_id"] == "/Guides"


def test_delete_by_query_is_folder_aware(client_and_service):
    client, service = client_and_service
    service.delete_item.return_value = {"deleted": True, "type": "folder", "deleted_folders": 1, "reparented_documents": 2}

    resp = client.delete("/api/v1/knowledge/items", params={"item_id": "/Guides", "brand_id": "b1"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "folder"
    assert body["reparented_documents"] == 2
    # Folder delete must go through delete_item (folder-aware), not delete_document.
    service.delete_item.assert_awaited_once()
    assert service.delete_item.call_args.args[0] == "/Guides"


def test_delete_by_query_missing_item_is_404(client_and_service):
    client, service = client_and_service
    service.delete_item.return_value = {"deleted": False}
    resp = client.delete("/api/v1/knowledge/items", params={"item_id": "/ghost", "brand_id": "b1"})
    assert resp.status_code == 404
