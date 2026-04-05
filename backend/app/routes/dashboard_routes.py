from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.csv_model import CsvFile
from ..models.json_file import JsonFile

router = APIRouter()

SCENARIOS_DIR = Path("/app/data/output/test_scenarios")
TEST_CASES_DIR = Path("/app/data/output/test_cases")
VARIABLES_DIR = Path("/app/data/input/Variables")

TEST_TYPE_LABELS = {
    "bsc": "Basic Tests",
    "ngv": "Negative Value Tests",
    "ngi": "Negative Tests",
    "opt": "Optional Tests",
}


def _isoformat(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).isoformat()


def _split_scenario_name(stem: str) -> tuple[str, str]:
    parts = stem.rsplit("_", 2)
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        return parts[0], f"{parts[1]}_{parts[2]}"
    return stem, ""


def _get_recent_scenarios(limit: int = 5) -> list[dict]:
    if not SCENARIOS_DIR.exists():
        return []

    scenarios: list[dict] = []
    for file_path in SCENARIOS_DIR.glob("*.txt"):
        stat = file_path.stat()
        name, date = _split_scenario_name(file_path.stem)
        scenarios.append(
            {
                "id": file_path.stem,
                "name": name,
                "date": date,
                "filename": file_path.name,
                "updated_at": _isoformat(stat.st_mtime),
                "size": stat.st_size,
            }
        )

    scenarios.sort(key=lambda item: item["updated_at"], reverse=True)
    return scenarios[:limit]


def _get_test_summary(limit: int = 5) -> tuple[int, int, list[dict], list[dict]]:
    total_suites = 0
    total_cases = 0
    recent_tests: list[dict] = []
    test_types = {
        key: {
            "key": key,
            "label": label,
            "suite_count": 0,
            "case_count": 0,
        }
        for key, label in TEST_TYPE_LABELS.items()
    }

    if not TEST_CASES_DIR.exists():
        return total_suites, total_cases, list(test_types.values()), recent_tests

    for test_dir in TEST_CASES_DIR.iterdir():
        if not test_dir.is_dir():
            continue

        total_suites += 1
        dir_stat = test_dir.stat()
        updated_at = dir_stat.st_mtime
        total_files = 0
        types: list[dict] = []

        for test_type, label in TEST_TYPE_LABELS.items():
            generator_dir = test_dir / test_type
            if not generator_dir.exists():
                continue

            files = [file_path for file_path in generator_dir.glob("*.json") if file_path.is_file()]
            if not files:
                continue

            file_count = len(files)
            total_files += file_count
            total_cases += file_count
            updated_at = max(updated_at, max(file_path.stat().st_mtime for file_path in files))
            test_types[test_type]["suite_count"] += 1
            test_types[test_type]["case_count"] += file_count
            types.append(
                {
                    "key": test_type,
                    "label": label,
                    "count": file_count,
                }
            )

        recent_tests.append(
            {
                "name": test_dir.name,
                "created_at": _isoformat(dir_stat.st_ctime),
                "updated_at": _isoformat(updated_at),
                "total_files": total_files,
                "types": types,
            }
        )

    recent_tests.sort(key=lambda item: item["updated_at"], reverse=True)
    return total_suites, total_cases, list(test_types.values()), recent_tests[:limit]


def _count_variable_files() -> int:
    if not VARIABLES_DIR.exists():
        return 0
    return len([file_path for file_path in VARIABLES_DIR.iterdir() if file_path.is_file()])


@router.get("/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    csv_count = db.query(CsvFile).count()
    json_count = db.query(JsonFile).count()
    variable_count = _count_variable_files()
    scenario_count = len([file_path for file_path in SCENARIOS_DIR.glob("*.txt")]) if SCENARIOS_DIR.exists() else 0
    test_suite_count, test_case_count, test_types, recent_tests = _get_test_summary()
    recent_scenarios = _get_recent_scenarios()

    return {
        "status": "healthy",
        "generated_at": datetime.now().isoformat(),
        "counts": {
            "csv_files": csv_count,
            "json_files": json_count,
            "variable_files": variable_count,
            "input_files": csv_count + json_count + variable_count,
            "scenarios": scenario_count,
            "test_suites": test_suite_count,
            "test_cases": test_case_count,
        },
        "input_breakdown": [
            {"key": "csv", "label": "CSV", "count": csv_count},
            {"key": "json", "label": "JSON", "count": json_count},
            {"key": "variables", "label": "Variables", "count": variable_count},
        ],
        "test_types": test_types,
        "recent_scenarios": recent_scenarios,
        "recent_tests": recent_tests,
    }
