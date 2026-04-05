import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.models.json_file import JsonFile
from app.routes import binding_profile_routes
from app.routes.binding_profile_routes import router
from app.services.binding_profile_service import BindingProfileService


def _build_service(tmp_path: Path) -> BindingProfileService:
    return BindingProfileService(profiles_dir=tmp_path / "binding_profiles")


def _sample_template():
    return {
        "header": {
            "id": "DOC-001",
            "issueDate": "2026-01-01T10:00:00Z",
            "customerName": "Example Customer",
        },
        "lineList": [
            {
                "productCode": "PRD-001",
                "quantity": 5,
                "unitPrice": 100.0,
            }
        ],
    }


def _sample_variables():
    return {
        "header.id": "{{header_id}}",
        "header.issueDate": "{{issue_date}}",
        "lineList[0].productCode": "{{product_code}}",
    }


def test_suggest_bindings_from_template(tmp_path):
    service = _build_service(tmp_path)

    result = service.suggest_bindings_from_template(
        template=_sample_template(),
        variables=_sample_variables(),
        json_file_id=11,
        variables_profile="variablesHeader",
    )

    assert result["json_file_id"] == 11
    assert result["variables_profile"] == "variablesHeader"
    assert result["total_fields"] == 6
    assert result["matched_fields"] >= 3

    fields = {field["json_path"]: field for field in result["fields"]}

    assert fields["header.id"]["suggested_variable_key"] == "header.id"
    assert fields["header.id"]["variable_key"] == "header.id"
    assert fields["header.id"]["status"] == "matched"
    assert fields["header.issueDate"]["suggested_variable_key"] == "header.issueDate"
    assert fields["lineList[0].productCode"]["suggested_variable_key"] == "lineList[0].productCode"
    assert fields["lineList[0].quantity"]["action"] == "keep_template"
    assert fields["lineList[0].quantity"]["variable_key"] is None
    assert fields["header.customerName"]["action"] == "keep_template"
    assert fields["header.customerName"]["variable_key"] is None


def test_binding_matcher_avoids_false_positive_id_suggestions(tmp_path):
    service = _build_service(tmp_path)
    template = {
        "branchDocumentSeries": {"id": "28052c8b-15a8-46d9-ba7f-86b848c60c3e"},
        "cardCurrencyDescription": {"id": "a1af9bc0-8d79-4004-9298-8e720442e57a"},
        "checkNoteCaseCard": {"id": "713f8a32-fd58-4ef6-8bef-940f09735752"},
        "currencyDescription": {"id": "a1af9bc0-8d79-4004-9298-8e720442e57a"},
        "documentDate": "2025-09-12T20:20:42+00:00",
        "documentDescription": None,
        "documentNumber": "5831233848",
        "externalId": None,
        "financeCard": {"id": "5fbfdff0-7751-4510-b1ca-b20ecb3cfdcf"},
        "financeCardType": "CUSTOMER",
        "user": {"id": "jplatformuser Admin"},
    }
    variables = {
        "branchDocumentSeries.id": "28052c8b-15a8-46d9-ba7f-86b848c60c3e",
        "cardCurrencyDescription.id": "a1af9bc0-8d79-4004-9298-8e720442e57a",
        "checkNoteCaseCard.id": "713f8a32-fd58-4ef6-8bef-940f09735752",
        "currencyDescription.id": "a1af9bc0-8d79-4004-9298-8e720442e57a",
        "financeCard.id": "5fbfdff0-7751-4510-b1ca-b20ecb3cfdcf",
        "financeCardType": "CUSTOMER",
        "user.id": "jplatformuser Admin",
    }

    result = service.suggest_bindings_from_template(
        template=template,
        variables=variables,
        json_file_id=3,
        variables_profile="variablesHeader",
    )

    fields = {field["json_path"]: field for field in result["fields"]}

    assert fields["branchDocumentSeries.id"]["variable_key"] == "branchDocumentSeries.id"
    assert fields["financeCardType"]["variable_key"] == "financeCardType"
    assert fields["user.id"]["variable_key"] == "user.id"
    assert fields["documentDescription"]["variable_key"] is None
    assert fields["documentDescription"]["action"] == "generate"
    assert fields["documentNumber"]["variable_key"] is None
    assert fields["documentNumber"]["action"] == "keep_template"
    assert fields["externalId"]["variable_key"] is None


def test_binding_profile_crud(tmp_path):
    service = _build_service(tmp_path)
    payload = {
        "json_file_id": 11,
        "variables_profile": "variablesHeader",
        "description": "sample profile",
        "bindings": [
            {
                "json_path": "header.id",
                "schema_type": "id",
                "suggested_variable_key": "header.id",
                "variable_key": "header.id",
                "confidence": 1.0,
                "status": "matched",
                "action": "bind",
                "locked": False,
                "generators": ["bsc", "ngi", "ngv", "opt"],
            }
        ],
    }

    saved = service.save_profile("sample_profile", payload)
    assert saved["name"] == "sample_profile"
    assert service.load_profile("sample_profile")["bindings"][0]["json_path"] == "header.id"

    profiles = service.list_profiles()
    assert len(profiles) == 1
    assert profiles[0]["binding_count"] == 1

    assert service.delete_profile("sample_profile") is True
    assert service.list_profiles() == []


def test_binding_profile_routes(tmp_path, monkeypatch):
    service = _build_service(tmp_path)
    service.variables_loader.load_profile = lambda _name: _sample_variables()
    monkeypatch.setattr(binding_profile_routes, "binding_profile_service", service)

    fake_json = JsonFile(
        id=7,
        name="sample.json",
        content=_sample_template(),
        size=123,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )

    class FakeQuery:
        def __init__(self, value):
            self.value = value

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return self.value

    class FakeDb:
        def query(self, _model):
            return FakeQuery(fake_json)

    app = FastAPI()
    app.include_router(router, prefix="/api/bindings")
    app.dependency_overrides[get_db] = lambda: FakeDb()

    client = TestClient(app)

    suggestion_response = client.post(
        "/api/bindings/suggest",
        json={
            "json_file_id": 7,
            "variables_profile": "variablesHeader",
            "generators": ["bsc", "ngi"],
        },
    )

    assert suggestion_response.status_code == 200
    suggestion_data = suggestion_response.json()["data"]
    assert suggestion_data["json_file_id"] == 7
    assert suggestion_data["variables_profile"] == "variablesHeader"
    assert suggestion_data["matched_fields"] >= 3

    fields = {field["json_path"]: field for field in suggestion_data["fields"]}
    profile_payload = {
        "json_file_id": 7,
        "variables_profile": "variablesHeader",
        "description": "saved binding profile",
        "bindings": [fields["header.id"], fields["header.issueDate"]],
    }

    save_response = client.put("/api/bindings/profiles/sample_binding", json=profile_payload)
    assert save_response.status_code == 200
    assert save_response.json()["data"]["name"] == "sample_binding"

    list_response = client.get("/api/bindings/profiles")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["profiles"][0]["name"] == "sample_binding"

    load_response = client.get("/api/bindings/profiles/sample_binding")
    assert load_response.status_code == 200
    saved_bindings = load_response.json()["data"]["bindings"]
    assert saved_bindings[0]["json_path"] == "header.id"
    assert saved_bindings[1]["json_path"] == "header.issueDate"

    delete_response = client.delete("/api/bindings/profiles/sample_binding")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["name"] == "sample_binding"
