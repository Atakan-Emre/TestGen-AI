import json

from app.shared.binding_runtime import apply_binding_profile


def test_apply_binding_profile_maps_variable_preserve_and_ignore(tmp_path):
    binding_dir = tmp_path / "Bindings"
    binding_dir.mkdir()
    (binding_dir / "header_binding.json").write_text(
        json.dumps(
            {
                "name": "header_binding",
                "entries": [
                    {
                        "json_path": "branchDocumentSeries.id",
                        "variable_key": "branchDocumentSeries.id",
                        "action": "variable",
                        "approved": True,
                        "locked": True,
                        "generators": ["all"],
                    },
                    {
                        "json_path": "documentDescription",
                        "action": "preserve",
                        "approved": True,
                        "generators": ["bsc"],
                    },
                    {
                        "json_path": "currentCardType",
                        "action": "ignore",
                        "approved": True,
                        "generators": ["ngi", "ngv"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    template = {
        "branchDocumentSeries": {"id": "template-branch"},
        "documentDescription": "Template description",
        "currentCardType": "CUSTOMER",
    }
    variables = {"branchDocumentSeries.id": "VAR-123"}

    resolved_bsc, ignored_bsc, blocked_bsc, _payload = apply_binding_profile(
        "header_binding",
        variables,
        template,
        "bsc",
        binding_dir=binding_dir,
    )
    assert resolved_bsc["branchDocumentSeries.id"] == "VAR-123"
    assert resolved_bsc["documentDescription"] == "Template description"
    assert "documentDescription" in blocked_bsc
    assert "currentCardType" not in ignored_bsc

    resolved_ngi, ignored_ngi, blocked_ngi, _payload = apply_binding_profile(
        "header_binding",
        variables,
        template,
        "ngi",
        binding_dir=binding_dir,
    )
    assert resolved_ngi["branchDocumentSeries.id"] == "VAR-123"
    assert "currentCardType" in ignored_ngi
    assert "currentCardType" in blocked_ngi


def test_apply_binding_profile_accepts_inline_json_payload():
    template = {
        "branchDocumentSeries": {"id": "template-branch"},
        "documentDescription": "Template description",
    }
    variables = {"branchDocumentSeries.id": "VAR-123"}
    inline_payload = json.dumps(
        {
            "name": "inline_auto_profile",
            "bindings": [
                {
                    "json_path": "branchDocumentSeries.id",
                    "variable_key": "branchDocumentSeries.id",
                    "action": "bind",
                    "approved": True,
                    "locked": True,
                    "generators": ["bsc"],
                },
                {
                    "json_path": "documentDescription",
                    "action": "keep_template",
                    "approved": True,
                    "locked": False,
                    "generators": ["bsc"],
                },
            ],
        }
    )

    resolved, ignored, blocked, payload = apply_binding_profile(
        inline_payload,
        variables,
        template,
        "bsc",
    )

    assert payload["name"] == "inline_auto_profile"
    assert resolved["branchDocumentSeries.id"] == "VAR-123"
    assert resolved["documentDescription"] == "Template description"
    assert not ignored
    assert "branchDocumentSeries.id" in blocked
