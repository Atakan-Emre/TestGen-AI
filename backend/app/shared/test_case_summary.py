import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract_test_case_summary(payload: Any) -> Dict[str, Optional[str]]:
    if not isinstance(payload, dict):
        return {
            "description": None,
            "scenario_type": None,
            "expected_result": None,
            "expected_message": None,
        }

    return {
        "description": payload.get("description"),
        "scenario_type": payload.get("scenario_type"),
        "expected_result": payload.get("expected_result"),
        "expected_message": payload.get("expected_message"),
    }


def build_test_case_list_item(file_path: str, include_content: bool = False) -> Dict[str, Any]:
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        payload = None

    item = {
        "name": path.name,
        "created_at": datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
        "file_path": str(path),
        **extract_test_case_summary(payload),
    }

    if include_content:
        item["content"] = content

    return item


def list_test_case_directory(test_dir: str, include_content: bool = False) -> List[Dict[str, Any]]:
    directory = Path(test_dir)
    if not directory.exists():
        return []

    return [
        build_test_case_list_item(str(file_path), include_content=include_content)
        for file_path in sorted(
            directory.glob("*.json"),
            key=lambda item: item.stat().st_ctime,
            reverse=True,
        )
    ]
