import json

from app.shared.test_case_summary import build_test_case_list_item


def test_build_test_case_list_item_extracts_visible_summary_fields(tmp_path):
    file_path = tmp_path / "ngi_case.json"
    file_path.write_text(
        json.dumps(
            {
                "scenario_type": "NGI",
                "description": "Zorunlu alan bos birakildi",
                "expected_result": "VALIDATION_ERROR",
                "expected_message": "documentNumber bos gecilemez",
                "test_data": {"documentNumber": None},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    item = build_test_case_list_item(str(file_path))

    assert item["name"] == "ngi_case.json"
    assert item["scenario_type"] == "NGI"
    assert item["description"] == "Zorunlu alan bos birakildi"
    assert item["expected_result"] == "VALIDATION_ERROR"
    assert item["expected_message"] == "documentNumber bos gecilemez"
    assert item["file_path"] == str(file_path)


def test_build_test_case_list_item_handles_non_json_content(tmp_path):
    file_path = tmp_path / "broken.json"
    file_path.write_text("json degil", encoding="utf-8")

    item = build_test_case_list_item(str(file_path))

    assert item["name"] == "broken.json"
    assert item["description"] is None
    assert item["scenario_type"] is None
    assert item["expected_result"] is None
    assert item["expected_message"] is None
