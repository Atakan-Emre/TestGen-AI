import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from app.models.json_file import JsonFile

from .binding_profile_service import ACTIVE_GENERATORS, BindingProfileService


class BindingAutopilotService:
    def __init__(
        self,
        binding_profile_service: Optional[BindingProfileService] = None,
        profiles_dir: str | Path = "/app/data/input/BindingProfiles",
    ) -> None:
        self.binding_profile_service = binding_profile_service or BindingProfileService(
            profiles_dir=profiles_dir
        )

    def resolve_auto_profile(
        self,
        json_file: JsonFile | Dict[str, Any],
        variables_profile: str,
        generators: Optional[Iterable[str]] = None,
        profile_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        suggestion = self.binding_profile_service.suggest_bindings_for_json_file(
            json_file=json_file,
            variables_profile=variables_profile,
            generators=generators,
        )
        summary = self._build_summary(suggestion)
        auto_profile_name = profile_name or self._build_profile_name(json_file, variables_profile)
        payload = {
            "json_file_id": suggestion.get("json_file_id"),
            "variables_profile": variables_profile,
            "description": description or self._build_description(json_file, variables_profile),
            "bindings": suggestion.get("fields") or [],
            "summary": summary,
            "review_recommended": summary["review_recommended"],
            "profile_kind": "auto",
            "generated_by": "binding_autopilot_service",
            "generated_at": suggestion.get("generated_at"),
            "generator_scope": list(generators or ACTIVE_GENERATORS),
        }
        saved_profile = self.binding_profile_service.save_profile(auto_profile_name, payload)
        return {
            "profile_name": auto_profile_name,
            "review_recommended": summary["review_recommended"],
            "summary": summary,
            "suggestion": suggestion,
            "saved_profile": saved_profile,
        }

    def _build_summary(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        fields = suggestion.get("fields") or []
        total_fields = len(fields)
        matched_fields = sum(1 for field in fields if field.get("status") == "matched")
        suggested_fields = sum(1 for field in fields if field.get("status") == "suggested")
        generated_fields = sum(1 for field in fields if field.get("action") == "generate")
        template_fields = sum(1 for field in fields if field.get("action") == "keep_template")
        bind_fields = sum(1 for field in fields if field.get("action") == "bind")
        approved_fields = sum(1 for field in fields if field.get("approved"))
        confidence_values = [float(field.get("confidence") or 0.0) for field in fields]
        average_confidence = round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else 0.0
        min_confidence = round(min(confidence_values), 3) if confidence_values else 0.0

        review_reasons = []
        if generated_fields:
            review_reasons.append("generated_fields_present")
        if suggested_fields:
            review_reasons.append("manual_review_for_mid_confidence_fields")
        if total_fields and matched_fields / total_fields < 0.6:
            review_reasons.append("low_match_ratio")
        if any(
            (field.get("action") == "bind" and float(field.get("confidence") or 0.0) < 0.92)
            for field in fields
        ):
            review_reasons.append("low_confidence_bindings")

        review_recommended = bool(review_reasons)
        return {
            "total_fields": total_fields,
            "matched_fields": matched_fields,
            "suggested_fields": suggested_fields,
            "generated_fields": generated_fields,
            "template_fields": template_fields,
            "bound_fields": bind_fields,
            "approved_fields": approved_fields,
            "match_ratio": round(matched_fields / total_fields, 3) if total_fields else 0.0,
            "average_confidence": average_confidence,
            "min_confidence": min_confidence,
            "review_recommended": review_recommended,
            "review_reasons": review_reasons,
        }

    def _build_profile_name(self, json_file: JsonFile | Dict[str, Any], variables_profile: str) -> str:
        json_name = self._json_file_name(json_file)
        base_name = self._slugify(json_name)
        variable_name = self._slugify(variables_profile)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"auto_{base_name}_{variable_name}_{timestamp}"

    def _build_description(self, json_file: JsonFile | Dict[str, Any], variables_profile: str) -> str:
        return f"Auto binding profile for {self._json_file_name(json_file)} using {variables_profile}"

    def _json_file_name(self, json_file: JsonFile | Dict[str, Any]) -> str:
        if isinstance(json_file, JsonFile):
            return json_file.name
        if isinstance(json_file, dict):
            return str(json_file.get("name") or json_file.get("json_name") or json_file.get("file_name") or "json_file")
        return "json_file"

    def _slugify(self, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9._-]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "value"
