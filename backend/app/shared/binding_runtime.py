import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple


DEFAULT_BINDING_DIR = Path("/app/data/input/BindingProfiles")


def load_binding_profile(
    name: Optional[str | Dict[str, Any]],
    binding_dir: Path = DEFAULT_BINDING_DIR,
) -> Dict[str, Any]:
    if not name:
        return {}

    if isinstance(name, dict):
        return name

    raw_value = str(name).strip()
    if not raw_value:
        return {}

    if raw_value.startswith("{"):
        payload = json.loads(raw_value)
        if not isinstance(payload, dict):
            raise ValueError("Geçersiz binding payload formatı")
        return payload

    profile_name = Path(raw_value).stem
    profile_path = binding_dir / f"{profile_name}.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"Binding profile bulunamadı: {profile_name}")

    with open(profile_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def apply_binding_profile(
    binding_profile_name: Optional[str | Dict[str, Any]],
    variables: Optional[Dict[str, Any]],
    template: Dict[str, Any],
    generator_type: str,
    binding_dir: Path = DEFAULT_BINDING_DIR,
) -> Tuple[Dict[str, Any], Set[str], Set[str], Dict[str, Any]]:
    payload = load_binding_profile(binding_profile_name, binding_dir=binding_dir)
    if not payload:
        return dict(variables or {}), set(), set(), {}

    resolved_variables = dict(variables or {})
    ignored_fields: Set[str] = set()
    mutation_blocked_fields: Set[str] = set()

    entries = payload.get("entries") or payload.get("bindings") or []
    for entry in entries:
        if not _entry_applies(entry, generator_type):
            continue
        if not _is_approved(entry):
            continue

        json_path = str(entry.get("json_path") or entry.get("path") or "").strip()
        if not json_path:
            continue

        action = str(entry.get("action") or "generate").strip().lower()
        variable_key = entry.get("variable_key") or entry.get("suggested_variable_key")
        locked = bool(entry.get("locked", False))

        if action in {"variable", "bind"}:
            if variable_key and variable_key in resolved_variables:
                resolved_variables[json_path] = resolved_variables[variable_key]
                if locked:
                    mutation_blocked_fields.add(json_path)
        elif action in {"preserve", "keep_template", "do_not_touch"}:
            resolved_variables[json_path] = _get_nested_value(template, json_path)
            mutation_blocked_fields.add(json_path)
        elif action == "force_null":
            resolved_variables[json_path] = None
            mutation_blocked_fields.add(json_path)
        elif action == "ignore":
            ignored_fields.add(json_path)
            mutation_blocked_fields.add(json_path)
        elif action == "generate":
            if locked:
                mutation_blocked_fields.add(json_path)

        if entry.get("exclude_negative") and generator_type in {"ngi", "ngv"}:
            mutation_blocked_fields.add(json_path)

    return resolved_variables, ignored_fields, mutation_blocked_fields, payload


def filter_bound_fields(fields: Dict[str, Any], ignored_fields: Iterable[str]) -> Dict[str, Any]:
    ignored = {str(path) for path in ignored_fields}
    return {path: value for path, value in fields.items() if path not in ignored}


def _is_approved(entry: Dict[str, Any]) -> bool:
    if "approved" in entry:
        return bool(entry["approved"])
    status = str(entry.get("status") or "approved").lower()
    return status in {"approved", "active", "locked", "matched", "suggested"}


def _entry_applies(entry: Dict[str, Any], generator_type: str) -> bool:
    raw_generators = entry.get("generators")
    if not raw_generators:
        return True

    if isinstance(raw_generators, str):
        generators = [raw_generators]
    else:
        generators = list(raw_generators)

    normalized = {str(item).strip().lower() for item in generators if str(item).strip()}
    return not normalized or "all" in normalized or generator_type.lower() in normalized


def _get_nested_value(data: Any, path: str) -> Any:
    current = data
    for token in _parse_path(path):
        if isinstance(token, int):
            if not isinstance(current, list) or len(current) <= token:
                return None
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return None
            current = current[token]
    return current


def _parse_path(path: str) -> list[Any]:
    tokens: list[Any] = []
    for part in path.split("."):
        if "[" not in part:
            tokens.append(part)
            continue

        head = part.split("[", 1)[0]
        if head:
            tokens.append(head)

        remaining = part[len(head):]
        while remaining.startswith("["):
            index_str, _, remaining = remaining[1:].partition("]")
            if index_str.isdigit():
                tokens.append(int(index_str))
            if remaining.startswith("["):
                continue
    return tokens
