import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.generators.bsc import BSCGenerator
from app.models.json_file import JsonFile
from app.services.binding_autopilot_service import BindingAutopilotService
from app.services.binding_profile_service import ACTIVE_GENERATORS, BindingProfileService
from app.services.variables_loader import VariablesLoader
from app.shared.binding_runtime import apply_binding_profile
from app.shared.io_loader import load_template
from src.generators.ngi_generator import NGIGenerator
from src.generators.ngv_generator import NGVGenerator
from src.generators.opt_generator import OPTGenerator


VALIDATION_OUTPUT_DIR = Path("/app/data/output/binding_validation_reports")


class BindingValidationAgent:
    def __init__(
        self,
        binding_profile_service: Optional[BindingProfileService] = None,
        variables_loader: Optional[VariablesLoader] = None,
        output_dir: str | Path = VALIDATION_OUTPUT_DIR,
    ) -> None:
        self.binding_profile_service = binding_profile_service or BindingProfileService()
        self.variables_loader = variables_loader or VariablesLoader()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_validation(
        self,
        *,
        scenario_id: Optional[str] = None,
        scenario_path: Optional[str] = None,
        json_file: JsonFile | Dict[str, Any],
        variables_profile: str,
        generators: Optional[Iterable[str]] = None,
        binding_profile_name: Optional[str] = None,
        auto_resolve: bool = True,
        auto_profile_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved_scenario_path = self._resolve_scenario_path(scenario_id=scenario_id, scenario_path=scenario_path)
        selected_generators = self._normalize_generators(generators)
        auto_binding: Optional[Dict[str, Any]] = None

        if binding_profile_name:
            binding_profile = self.binding_profile_service.load_profile(binding_profile_name)
            binding_summary = self._summarize_binding_profile(binding_profile)
        else:
            if not auto_resolve:
                raise ValueError("Binding profili belirtilmedi ve auto_resolve kapalı")
            auto_binding = BindingAutopilotService(self.binding_profile_service).resolve_auto_profile(
                json_file=json_file,
                variables_profile=variables_profile,
                generators=selected_generators,
                profile_name=auto_profile_name,
                description=description,
            )
            binding_profile_name = auto_binding["profile_name"]
            binding_summary = auto_binding["summary"]

        validation_name = self._build_validation_name(
            scenario_id=scenario_id,
            json_file=json_file,
            variables_profile=variables_profile,
            binding_profile_name=binding_profile_name,
        )

        report = {
            "scenario_id": scenario_id,
            "scenario_path": str(resolved_scenario_path),
            "json_file_id": getattr(json_file, "id", None) if isinstance(json_file, JsonFile) else json_file.get("id"),
            "variables_profile": variables_profile,
            "binding_profile_name": binding_profile_name,
            "binding_summary": binding_summary,
            "auto_binding": auto_binding,
            "validation_name": validation_name,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "generator_results": {},
        }

        template = load_template(report["json_file_id"])
        variables = self._load_variables_profile(variables_profile)

        for generator_name in selected_generators:
            report["generator_results"][generator_name] = self._run_generator(
                generator_name=generator_name,
                scenario_path=resolved_scenario_path,
                validation_name=validation_name,
                json_file_id=report["json_file_id"],
                variables=variables,
                template=template,
                binding_profile_name=binding_profile_name,
                variables_profile=variables_profile,
            )

        report["overall_success"] = all(
            bool(result.get("success")) for result in report["generator_results"].values()
        )
        report_path = self._save_report(report, validation_name)
        report["report_path"] = str(report_path)
        return report

    def _normalize_generators(self, generators: Optional[Iterable[str]]) -> List[str]:
        if not generators:
            return list(ACTIVE_GENERATORS)
        normalized = []
        seen = set()
        for generator in generators:
            name = str(generator).strip().lower()
            if not name or name not in ACTIVE_GENERATORS or name in seen:
                continue
            seen.add(name)
            normalized.append(name)
        return normalized or list(ACTIVE_GENERATORS)

    def _resolve_scenario_path(self, scenario_id: Optional[str], scenario_path: Optional[str]) -> Path:
        if scenario_path:
            resolved = Path(scenario_path)
        elif scenario_id:
            resolved = Path("/app/data/output/test_scenarios") / scenario_id
        else:
            raise ValueError("scenario_id veya scenario_path gerekli")

        if not resolved.exists():
            raise FileNotFoundError(f"Senaryo dosyası bulunamadı: {resolved}")
        return resolved

    def _load_variables_profile(self, profile_name: str) -> Dict[str, Any]:
        try:
            return self.variables_loader.load_profile(profile_name)
        except FileNotFoundError:
            raise FileNotFoundError(f"Variables profili bulunamadı: {profile_name}")

    def _run_generator(
        self,
        *,
        generator_name: str,
        scenario_path: Path,
        validation_name: str,
        json_file_id: int,
        variables: Dict[str, Any],
        template: Dict[str, Any],
        binding_profile_name: Optional[str],
        variables_profile: str,
    ) -> Dict[str, Any]:
        start = datetime.now(timezone.utc)
        try:
            if generator_name == "bsc":
                result = self._run_bsc(
                    scenario_path=scenario_path,
                    validation_name=validation_name,
                    json_file_id=json_file_id,
                    variables_profile=variables_profile,
                    binding_profile_name=binding_profile_name,
                )
            elif generator_name == "ngi":
                result = self._run_ngi(
                    scenario_path=scenario_path,
                    validation_name=validation_name,
                    json_file_id=json_file_id,
                    variables=variables,
                    template=template,
                    binding_profile_name=binding_profile_name,
                )
            elif generator_name == "ngv":
                result = self._run_ngv(
                    scenario_path=scenario_path,
                    validation_name=validation_name,
                    json_file_id=json_file_id,
                    variables=variables,
                    template=template,
                    binding_profile_name=binding_profile_name,
                )
            elif generator_name == "opt":
                result = self._run_opt(
                    scenario_path=scenario_path,
                    validation_name=validation_name,
                    json_file_id=json_file_id,
                    variables=variables,
                    template=template,
                    binding_profile_name=binding_profile_name,
                )
            else:
                raise ValueError(f"Desteklenmeyen generator: {generator_name}")

            normalized = self._normalize_result(generator_name, result)
            normalized["duration_ms"] = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            return normalized
        except Exception as exc:
            return {
                "generator": generator_name,
                "success": False,
                "error": str(exc),
                "duration_ms": int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
            }

    def _run_bsc(
        self,
        *,
        scenario_path: Path,
        validation_name: str,
        json_file_id: int,
        variables_profile: str,
        binding_profile_name: Optional[str],
    ) -> Any:
        generator = BSCGenerator()
        variables_file = self.variables_loader.resolve_profile_path(variables_profile)
        selected_variables = None
        if variables_file:
            selected_variables = [f"variables_file:{variables_file.name}"]
        return generator.generate_bsc_test_with_variables(
            scenario_path=str(scenario_path),
            test_name=validation_name,
            json_file_id=json_file_id,
            selected_variables=selected_variables,
            binding_profile=binding_profile_name,
        )

    def _run_ngi(
        self,
        *,
        scenario_path: Path,
        validation_name: str,
        json_file_id: int,
        variables: Dict[str, Any],
        template: Dict[str, Any],
        binding_profile_name: Optional[str],
    ) -> Any:
        generator = NGIGenerator()
        generator.variables = variables
        if binding_profile_name:
            bound_variables, ignored_fields, mutation_blocked_fields, _ = apply_binding_profile(
                binding_profile_name,
                generator.variables,
                template,
                "ngi",
            )
            generator.variables = bound_variables
            generator.binding_ignored_fields = ignored_fields
            generator.binding_mutation_blocked_fields = mutation_blocked_fields
        return generator.generate_ngi_tests(str(scenario_path), validation_name, json_file_id)

    def _run_ngv(
        self,
        *,
        scenario_path: Path,
        validation_name: str,
        json_file_id: int,
        variables: Dict[str, Any],
        template: Dict[str, Any],
        binding_profile_name: Optional[str],
    ) -> Any:
        generator = NGVGenerator()
        generator.variables = variables
        if binding_profile_name:
            bound_variables, ignored_fields, mutation_blocked_fields, _ = apply_binding_profile(
                binding_profile_name,
                generator.variables,
                template,
                "ngv",
            )
            generator.variables = bound_variables
            generator.binding_ignored_fields = ignored_fields
            generator.binding_mutation_blocked_fields = mutation_blocked_fields
        return generator.generate_ngv_tests(str(scenario_path), validation_name, json_file_id)

    def _run_opt(
        self,
        *,
        scenario_path: Path,
        validation_name: str,
        json_file_id: int,
        variables: Dict[str, Any],
        template: Dict[str, Any],
        binding_profile_name: Optional[str],
    ) -> Any:
        generator = OPTGenerator()
        generator.variables = variables
        if binding_profile_name:
            bound_variables, ignored_fields, mutation_blocked_fields, _ = apply_binding_profile(
                binding_profile_name,
                generator.variables,
                template,
                "opt",
            )
            generator.variables = bound_variables
            generator.binding_ignored_fields = ignored_fields
            generator.binding_mutation_blocked_fields = mutation_blocked_fields
        return generator.generate_opt_tests(str(scenario_path), validation_name, json_file_id)

    def _normalize_result(self, generator_name: str, result: Any) -> Dict[str, Any]:
        if result is None:
            return {
                "generator": generator_name,
                "success": False,
                "result_count": 0,
                "output_files": [],
                "message": "No result returned",
            }

        if isinstance(result, list):
            output_files = [str(item.get("file_path")) for item in result if isinstance(item, dict) and item.get("file_path")]
            return {
                "generator": generator_name,
                "success": True,
                "result_count": len(result),
                "output_files": output_files,
                "preview": self._preview_list(result),
            }

        if isinstance(result, dict):
            output_files = []
            if result.get("file_path"):
                output_files.append(str(result["file_path"]))
            if isinstance(result.get("result"), list):
                output_files.extend(
                    str(item.get("file_path"))
                    for item in result["result"]
                    if isinstance(item, dict) and item.get("file_path")
                )
            return {
                "generator": generator_name,
                "success": True,
                "result_count": max(len(output_files), 1 if result else 0),
                "output_files": output_files,
                "preview": self._preview_dict(result),
            }

        return {
            "generator": generator_name,
            "success": True,
            "result_count": 1,
            "output_files": [],
            "preview": str(result),
        }

    def _preview_list(self, items: List[Any]) -> List[Any]:
        preview = []
        for item in items[:3]:
            if isinstance(item, dict):
                preview.append({key: item.get(key) for key in ("scenario_type", "description", "expected_result", "file_path") if key in item})
            else:
                preview.append(str(item))
        return preview

    def _preview_dict(self, value: Dict[str, Any]) -> Dict[str, Any]:
        keys = ("message", "test_name", "file_path", "success", "error")
        return {key: value.get(key) for key in keys if key in value}

    def _save_report(self, report: Dict[str, Any], validation_name: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"{validation_name}_{timestamp}.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report_path

    def _summarize_binding_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        bindings = payload.get("bindings") or payload.get("entries") or []
        fields = [self._normalize_binding_field(binding) for binding in bindings]
        total_fields = len(fields)
        matched_fields = sum(1 for field in fields if field.get("status") == "matched")
        suggested_fields = sum(1 for field in fields if field.get("status") == "suggested")
        generated_fields = sum(1 for field in fields if field.get("action") == "generate")
        template_fields = sum(1 for field in fields if field.get("action") == "keep_template")
        bind_fields = sum(1 for field in fields if field.get("action") == "bind")
        confidence_values = [float(field.get("confidence") or 0.0) for field in fields]
        average_confidence = round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else 0.0
        review_recommended = bool(
            payload.get("review_recommended")
            or suggested_fields
            or generated_fields
            or (total_fields and matched_fields / total_fields < 0.6)
        )
        return {
            "total_fields": total_fields,
            "matched_fields": matched_fields,
            "suggested_fields": suggested_fields,
            "generated_fields": generated_fields,
            "template_fields": template_fields,
            "bound_fields": bind_fields,
            "average_confidence": average_confidence,
            "review_recommended": review_recommended,
        }

    def _normalize_binding_field(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(entry, dict):
            return {}
        return {
            "json_path": entry.get("json_path") or entry.get("path"),
            "status": entry.get("status"),
            "action": entry.get("action"),
            "confidence": entry.get("confidence"),
        }

    def _build_validation_name(
        self,
        *,
        scenario_id: Optional[str],
        json_file: JsonFile | Dict[str, Any],
        variables_profile: str,
        binding_profile_name: Optional[str],
    ) -> str:
        scenario_root = Path(scenario_id).stem if scenario_id else Path(str(getattr(json_file, "name", "json_file"))).stem
        variable_root = Path(variables_profile).stem
        binding_root = Path(binding_profile_name or "auto_binding").stem
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"validation_{scenario_root}_{variable_root}_{binding_root}_{timestamp}"
