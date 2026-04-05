import json

from app.services.scenario_intelligence import get_bundle_path, load_scenario_bundle, load_scenario_constraints


def test_load_scenario_bundle_from_sidecar(tmp_path):
    scenario_path = tmp_path / "sample_scenario.txt"
    scenario_path.write_text("Belge Tarihi (Document Date) alanı doldurulması zorunludur.", encoding="utf-8")

    bundle_payload = {
        "scenario_name": "sample_scenario",
        "source_csv": "sample.csv",
        "generator_type": "nlp_hybrid",
        "generated_at": "2026-04-04T00:00:00",
        "scenario_file": scenario_path.name,
        "fields": [
            {
                "field_name_tr": "Belge Tarihi",
                "field_name_en": "Document Date",
                "field_type": "date",
                "raw_type": "Date",
                "required": True,
                "optional": False,
                "unique": False,
                "max_len": None,
                "min_len": None,
                "pattern": None,
                "enum_values": [],
                "semantic_tags": ["document", "date"],
                "ner_entities": [],
                "scenario_lines": ["Belge Tarihi (Document Date) alanı doldurulması zorunludur."],
                "confidence": 0.91,
                "source_text": "Date | Zorunlu",
                "locale": "tr-TR",
            }
        ],
    }
    get_bundle_path(scenario_path).write_text(json.dumps(bundle_payload), encoding="utf-8")

    bundle = load_scenario_bundle(str(scenario_path))
    assert bundle is not None
    assert bundle.generator_type == "nlp_hybrid"
    assert bundle.fields[0].field_name_en == "Document Date"

    constraints = load_scenario_constraints(str(scenario_path))
    assert len(constraints) == 1
    assert constraints[0].required is True
    assert constraints[0].field_type == "date"
    assert constraints[0].source_field_en == "Document Date"
