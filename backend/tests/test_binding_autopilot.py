from pathlib import Path

from app.services.binding_autopilot_service import BindingAutopilotService
from app.services.binding_profile_service import BindingProfileService
from app.services.binding_validation_agent import BindingValidationAgent
from app.services.variables_loader import VariablesLoader


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
            }
        ],
    }


def _sample_suggestion():
    return {
        "json_file_id": 17,
        "variables_profile": "variablesHeader",
        "total_fields": 4,
        "matched_fields": 1,
        "unmatched_fields": 3,
        "generated_at": "2026-04-04T11:20:00+00:00",
        "fields": [
            {
                "json_path": "header.id",
                "schema_type": "id",
                "suggested_variable_key": "header.id",
                "variable_key": "header.id",
                "confidence": 0.995,
                "status": "matched",
                "action": "bind",
                "locked": False,
                "approved": True,
                "generators": ["bsc", "ngi", "ngv", "opt"],
            },
            {
                "json_path": "header.issueDate",
                "schema_type": "date",
                "suggested_variable_key": "header.issueDate",
                "variable_key": "header.issueDate",
                "confidence": 0.83,
                "status": "suggested",
                "action": "bind",
                "locked": False,
                "approved": False,
                "generators": ["bsc", "ngi", "ngv", "opt"],
            },
            {
                "json_path": "header.customerName",
                "schema_type": "string",
                "suggested_variable_key": None,
                "variable_key": None,
                "confidence": 0.12,
                "status": "generated",
                "action": "generate",
                "locked": False,
                "approved": False,
                "generators": ["bsc", "ngi", "ngv", "opt"],
            },
            {
                "json_path": "lineList[0].quantity",
                "schema_type": "number",
                "suggested_variable_key": None,
                "variable_key": None,
                "confidence": 1.0,
                "status": "template",
                "action": "keep_template",
                "locked": False,
                "approved": True,
                "generators": ["bsc", "ngi", "ngv", "opt"],
            },
        ],
    }


def test_auto_resolve_persists_profile_with_summary(tmp_path):
    binding_service = BindingProfileService(profiles_dir=tmp_path / "binding_profiles")
    autopilot = BindingAutopilotService(binding_profile_service=binding_service)

    binding_service.suggest_bindings_for_json_file = lambda **_kwargs: _sample_suggestion()

    result = autopilot.resolve_auto_profile(
        json_file={"id": 17, "name": "sample.json"},
        variables_profile="variablesHeader",
        generators=["bsc", "ngi", "ngv", "opt"],
        profile_name="auto_sample_profile",
        description="auto binding smoke",
    )

    assert result["profile_name"] == "auto_sample_profile"
    assert result["review_recommended"] is True
    assert result["summary"]["total_fields"] == 4
    assert result["summary"]["generated_fields"] == 1
    assert result["summary"]["suggested_fields"] == 1
    assert result["saved_profile"]["profile_kind"] == "auto"
    assert result["saved_profile"]["review_recommended"] is True

    loaded = binding_service.load_profile("auto_sample_profile")
    assert loaded["generated_by"] == "binding_autopilot_service"
    assert loaded["summary"]["review_recommended"] is True
    assert loaded["generator_scope"] == ["bsc", "ngi", "ngv", "opt"]


def test_validation_agent_runs_all_generators_and_saves_report(tmp_path, monkeypatch):
    binding_service = BindingProfileService(profiles_dir=tmp_path / "binding_profiles")
    variables_dir = tmp_path / "Variables"
    variables_dir.mkdir(parents=True, exist_ok=True)
    (variables_dir / "variablesHeader.txt").write_text(
        "header.id=DOC-001\nheader.issueDate=2026-01-01T10:00:00Z\n",
        encoding="utf-8",
    )

    variables_loader = VariablesLoader(variables_dir=str(variables_dir))
    agent = BindingValidationAgent(
        binding_profile_service=binding_service,
        variables_loader=variables_loader,
        output_dir=tmp_path / "validation_reports",
    )

    binding_service.suggest_bindings_for_json_file = lambda **_kwargs: _sample_suggestion()

    class DummyBSCGenerator:
        def generate_bsc_test_with_variables(self, **kwargs):
            return {
                "test_name": kwargs["test_name"],
                "file_path": str(tmp_path / "bsc_result.json"),
                "success": True,
            }

    class DummyNGIGenerator:
        def __init__(self):
            self.variables = {}
            self.binding_ignored_fields = set()
            self.binding_mutation_blocked_fields = set()

        def generate_ngi_tests(self, scenario_path, test_name, json_file_id):
            return [
                {
                    "scenario_type": "NGI",
                    "description": "dummy ngi",
                    "file_path": str(tmp_path / "ngi_result.json"),
                }
            ]

    class DummyNGVGenerator(DummyNGIGenerator):
        def generate_ngv_tests(self, scenario_path, test_name, json_file_id):
            return [
                {
                    "scenario_type": "NGV",
                    "description": "dummy ngv",
                    "file_path": str(tmp_path / "ngv_result.json"),
                }
            ]

    class DummyOPTGenerator(DummyNGIGenerator):
        def generate_opt_tests(self, scenario_path, test_name, json_file_id):
            return [
                {
                    "scenario_type": "OPT",
                    "description": "dummy opt",
                    "file_path": str(tmp_path / "opt_result.json"),
                }
            ]

    monkeypatch.setattr("app.services.binding_validation_agent.BSCGenerator", DummyBSCGenerator)
    monkeypatch.setattr("app.services.binding_validation_agent.NGIGenerator", DummyNGIGenerator)
    monkeypatch.setattr("app.services.binding_validation_agent.NGVGenerator", DummyNGVGenerator)
    monkeypatch.setattr("app.services.binding_validation_agent.OPTGenerator", DummyOPTGenerator)
    monkeypatch.setattr(
        "app.services.binding_validation_agent.load_template",
        lambda _json_file_id: _sample_template(),
    )
    monkeypatch.setattr(
        "app.services.binding_validation_agent.apply_binding_profile",
        lambda binding_profile_name, variables, template, generator_type: (
            dict(variables),
            set(),
            set(),
            {"name": binding_profile_name, "bindings": []},
        ),
    )

    scenario_path = tmp_path / "scenario.txt"
    scenario_path.write_text("Örnek senaryo satırı", encoding="utf-8")

    report = agent.run_validation(
        scenario_path=str(scenario_path),
        json_file={"id": 17, "name": "sample.json"},
        variables_profile="variablesHeader",
        generators=["bsc", "ngi", "ngv", "opt"],
        auto_resolve=True,
        auto_profile_name="auto_sample_profile",
    )

    assert report["overall_success"] is True
    assert report["binding_profile_name"] == "auto_sample_profile"
    assert report["auto_binding"]["profile_name"] == "auto_sample_profile"
    assert set(report["generator_results"].keys()) == {"bsc", "ngi", "ngv", "opt"}
    assert report["generator_results"]["bsc"]["success"] is True
    assert report["generator_results"]["ngi"]["success"] is True
    assert report["generator_results"]["ngv"]["success"] is True
    assert report["generator_results"]["opt"]["success"] is True

    report_path = Path(report["report_path"])
    assert report_path.exists()
    persisted = report_path.read_text(encoding="utf-8")
    assert "auto_sample_profile" in persisted
    assert "generator_results" in persisted
