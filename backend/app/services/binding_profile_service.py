import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.shared.json_structure import analyze_structure
from app.services.domain_tuning import normalize_text, resolve_preferred_field_type
from app.services.variables_loader import VariablesLoader
from app.models.json_file import JsonFile


ACTIVE_GENERATORS = ["bsc", "ngi", "ngv", "opt"]
GENERIC_MATCH_TOKENS = {
    "id",
    "code",
    "number",
    "nr",
    "no",
    "name",
    "description",
    "date",
    "time",
    "type",
    "status",
    "value",
    "values",
}


class BindingProfileService:
    def __init__(
        self,
        profiles_dir: str | Path = "/app/data/input/BindingProfiles",
        variables_loader: Optional[VariablesLoader] = None,
    ) -> None:
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.variables_loader = variables_loader or VariablesLoader()

    def list_profiles(self) -> List[Dict[str, Any]]:
        profiles: List[Dict[str, Any]] = []
        for file_path in sorted(self.profiles_dir.glob("*.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            stat = file_path.stat()
            bindings = data.get("bindings") or []
            profiles.append(
                {
                    "name": data.get("name") or file_path.stem,
                    "json_file_id": data.get("json_file_id"),
                    "variables_profile": data.get("variables_profile"),
                    "description": data.get("description"),
                    "binding_count": len(bindings),
                    "size_bytes": stat.st_size,
                    "updated_at": data.get("updated_at")
                    or datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        return profiles

    def load_profile(self, name: str) -> Dict[str, Any]:
        file_path = self._profile_path(name)
        if not file_path.exists():
            raise FileNotFoundError(f"Binding profili bulunamadı: {name}")
        return json.loads(file_path.read_text(encoding="utf-8"))

    def save_profile(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_profile_name(name)
        file_path = self._profile_path(name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()

        base_keys = {
            "name",
            "json_file_id",
            "variables_profile",
            "description",
            "bindings",
            "created_at",
            "updated_at",
        }
        data = {
            "name": name,
            "json_file_id": payload.get("json_file_id"),
            "variables_profile": payload.get("variables_profile"),
            "description": payload.get("description"),
            "bindings": payload.get("bindings") or [],
            "created_at": payload.get("created_at"),
            "updated_at": now,
        }
        extra_fields = {
            key: value
            for key, value in payload.items()
            if key not in base_keys and value is not None
        }
        data.update(extra_fields)

        if file_path.exists():
            existing = json.loads(file_path.read_text(encoding="utf-8"))
            data["created_at"] = existing.get("created_at") or now
        else:
            data["created_at"] = now

        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data

    def delete_profile(self, name: str) -> bool:
        file_path = self._profile_path(name)
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def suggest_bindings_for_json_file(
        self,
        json_file: JsonFile | Dict[str, Any],
        variables_profile: str,
        generators: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        template = json_file.content if hasattr(json_file, "content") else json_file
        if isinstance(template, str):
            template = json.loads(template)
        if not isinstance(template, dict):
            raise ValueError("JSON şablonu sözlük yapısında olmalıdır")

        variables = self.variables_loader.load_profile(variables_profile)
        return self.suggest_bindings_from_template(
            template=template,
            variables=variables,
            json_file_id=getattr(json_file, "id", None),
            variables_profile=variables_profile,
            generators=generators,
        )

    def suggest_bindings_from_template(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any],
        json_file_id: Optional[int] = None,
        variables_profile: Optional[str] = None,
        generators: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        schema = analyze_structure(template)
        variable_entries = list(variables.items())
        generator_list = list(generators or ACTIVE_GENERATORS)
        template_fields = self._extract_leaf_fields(template, schema.types)

        suggestions = []
        matched = 0
        for field in template_fields:
            json_path = field["json_path"]
            schema_type = field["schema_type"]
            template_value = field["template_value"]
            template_has_value = self._has_template_value(template_value)
            best = self._best_variable_match(json_path, schema_type, variable_entries)
            best_key = best["key"]
            best_value = best["value"]
            confidence = best["confidence"]

            if confidence >= 0.92:
                status = "matched"
                action = "bind"
                variable_key = best_key
                locked = False
                matched += 1
                approved = True
            elif confidence >= 0.78 and best_key and not template_has_value:
                status = "suggested"
                action = "bind"
                variable_key = best_key
                locked = False
                approved = False
            elif template_has_value:
                status = "template"
                action = "keep_template"
                variable_key = None
                locked = False
                approved = True
            else:
                status = "generated"
                action = "generate"
                variable_key = None
                locked = False
                approved = False

            suggestions.append(
                {
                    "json_path": json_path,
                    "schema_type": schema_type,
                    "suggested_variable_key": best_key,
                    "variable_key": variable_key,
                    "confidence": round(confidence, 3),
                    "status": status,
                    "action": action,
                    "locked": locked,
                    "approved": approved,
                    "generators": generator_list,
                    "template_value_preview": self._preview_value(template_value),
                    "variable_value_preview": self._preview_value(best_value),
                }
            )

        return {
            "json_file_id": json_file_id,
            "variables_profile": variables_profile,
            "total_fields": len(suggestions),
            "matched_fields": matched,
            "unmatched_fields": len(suggestions) - matched,
            "fields": suggestions,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _profile_path(self, name: str) -> Path:
        self._validate_profile_name(name)
        return self.profiles_dir / f"{name}.json"

    def _validate_profile_name(self, name: str) -> None:
        if not name or len(name) > 100:
            raise ValueError("Geçersiz binding profili adı")
        if re.fullmatch(r"[A-Za-z0-9._-]+", name) is None:
            raise ValueError("Binding profili adı yalnızca harf, rakam, nokta, tire ve alt çizgi içerebilir")

    def _best_variable_match(
        self,
        json_path: str,
        schema_type: str,
        variable_entries: List[tuple[str, Any]],
    ) -> Dict[str, Any]:
        best_key = None
        best_value = None
        best_score = 0.0
        for variable_key, variable_value in variable_entries:
            score = self._score_variable_match(json_path, schema_type, variable_key, variable_value)
            if score > best_score:
                best_score = score
                best_key = variable_key
                best_value = variable_value
        return {"key": best_key, "value": best_value, "confidence": best_score}

    def _score_variable_match(self, json_path: str, schema_type: str, variable_key: str, variable_value: Any) -> float:
        normalized_path = normalize_text(json_path)
        normalized_key = normalize_text(variable_key)
        path_tokens = self._tokenize(json_path)
        key_tokens = self._tokenize(variable_key)
        specific_path_tokens = [token for token in path_tokens if token not in GENERIC_MATCH_TOKENS]
        specific_key_tokens = [token for token in key_tokens if token not in GENERIC_MATCH_TOKENS]
        variable_type = self._infer_variable_type(variable_key, variable_value)

        if not path_tokens or not key_tokens:
            return 0.0

        if normalized_path == normalized_key:
            return 1.0

        if not self._types_compatible(schema_type, variable_type):
            return 0.0

        path_leaf = [token for token in self._tokenize(json_path.split(".")[-1]) if token not in GENERIC_MATCH_TOKENS]
        key_leaf = [token for token in self._tokenize(variable_key.split(".")[-1]) if token not in GENERIC_MATCH_TOKENS]
        path_context = set(specific_path_tokens[:-len(path_leaf)] if path_leaf else specific_path_tokens)
        key_context = set(specific_key_tokens[:-len(key_leaf)] if key_leaf else specific_key_tokens)
        shared_specific = set(specific_path_tokens).intersection(specific_key_tokens)
        shared_context = path_context.intersection(key_context)

        if path_leaf and key_leaf and path_leaf == key_leaf and (shared_context or len(path_leaf) > 1):
            return 0.96

        if not shared_specific:
            return 0.0

        score = 0.0
        overlap = len(shared_specific)
        union = len(set(specific_path_tokens).union(specific_key_tokens))
        if overlap and union:
            score = max(score, 0.58 + 0.28 * (overlap / union))

        key_joined = " ".join(key_tokens)

        if schema_type == "date" and any(token in key_joined for token in ["date", "time", "day"]):
            score = max(score, 0.88)
        if schema_type == "number" and any(token in key_joined for token in ["amount", "quantity", "rate", "ratio", "count"]):
            score = max(score, 0.86)
        if schema_type == "id" and shared_specific and any(
            token in key_joined for token in ["id", "code", "serial", "reference", "order", "number"]
        ):
            score = max(score, 0.91)
        if schema_type == "bool" and any(token in key_joined for token in ["flag", "active", "enabled", "bool"]):
            score = max(score, 0.8)
        if schema_type in {"string", "enum"} and shared_specific and any(
            token in key_joined for token in ["name", "description", "note", "title", "type"]
        ):
            score = max(score, 0.82)

        return min(score, 1.0)

    def _tokenize(self, value: str) -> List[str]:
        if not value:
            return []
        value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
        normalized = normalize_text(value)
        normalized = normalized.replace(".", " ").replace("[", " ").replace("]", " ").replace("_", " ")
        tokens: List[str] = []
        for raw in re.split(r"[^a-z0-9]+", normalized):
            if raw and len(raw) > 1:
                tokens.append(raw)
        return list(dict.fromkeys(tokens))

    def _extract_leaf_fields(self, template: Dict[str, Any], schema_types: Dict[str, str]) -> List[Dict[str, Any]]:
        fields: List[Dict[str, Any]] = []

        def _walk(value: Any, path: str = "") -> None:
            if isinstance(value, dict):
                for key, nested_value in value.items():
                    next_path = f"{path}.{key}" if path else key
                    _walk(nested_value, next_path)
                return

            if isinstance(value, list):
                if value:
                    _walk(value[0], f"{path}[0]")
                else:
                    fields.append(
                        {
                            "json_path": path,
                            "schema_type": "array",
                            "template_value": [],
                        }
                    )
                return

            fields.append(
                {
                    "json_path": path,
                    "schema_type": self._resolve_leaf_schema_type(path, value, schema_types.get(path)),
                    "template_value": value,
                }
            )

        _walk(template)
        return fields

    def _resolve_leaf_schema_type(self, json_path: str, template_value: Any, schema_type: Optional[str]) -> str:
        resolved = resolve_preferred_field_type(None, schema_type)
        if resolved in {"bool", "date", "number", "id", "enum"}:
            return resolved

        path_text = normalize_text(json_path)
        if template_value is None:
            if any(token in path_text for token in ["date", "time", "tarih", "saat"]):
                return "date"
            if any(token in path_text for token in ["amount", "quantity", "rate", "ratio", "count", "total", "exchange"]):
                return "number"
            if any(token in path_text for token in ["status", "flag", "turnover", "accounting"]):
                return "bool"
            if path_text.endswith("id") or ".id" in path_text or any(
                token in path_text for token in ["serial", "document number", "document no", "reference", "code"]
            ):
                return "id"
            return "string"

        if isinstance(template_value, bool):
            return "bool"
        if isinstance(template_value, (int, float)):
            return "number"
        if isinstance(template_value, str):
            if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", template_value, re.IGNORECASE):
                return "id"
            if re.match(r"^\d{4}-\d{2}-\d{2}", template_value):
                return "date"
        return resolved

    def _infer_variable_type(self, variable_key: str, variable_value: Any) -> str:
        key_text = normalize_text(variable_key)
        value_text = normalize_text(str(variable_value))

        if value_text in {"true", "false"} or any(token in key_text for token in ["status", "flag", "enabled", "active"]):
            return "bool"
        if re.match(r"^\d{4}-\d{2}-\d{2}", value_text) or any(token in key_text for token in ["date", "time", "tarih", "saat"]):
            return "date"
        if re.match(r"^-?\d+(\.\d+)?$", value_text) and any(
            token in key_text for token in ["amount", "quantity", "rate", "ratio", "count", "total", "exchange"]
        ):
            return "number"
        if re.match(r"^[0-9a-f-]{16,}$", value_text, re.IGNORECASE) or key_text.endswith("id") or ".id" in key_text:
            return "id"
        if any(token in key_text for token in ["type", "class", "kind"]):
            return "enum"
        return "string"

    def _types_compatible(self, schema_type: str, variable_type: str) -> bool:
        if schema_type == variable_type:
            return True
        if schema_type == "string" and variable_type in {"string", "enum"}:
            return True
        if schema_type == "enum" and variable_type in {"string", "enum"}:
            return True
        if schema_type == "id" and variable_type in {"id", "string"}:
            return True
        return False

    def _has_template_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    def _preview_value(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value if len(value) <= 80 else f"{value[:77]}..."
        try:
            serialized = json.dumps(value, ensure_ascii=False)
        except Exception:
            serialized = str(value)
        return serialized if len(serialized) <= 80 else f"{serialized[:77]}..."
