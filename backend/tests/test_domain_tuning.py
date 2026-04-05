from app.services.domain_tuning import (
    build_duplicate_seed,
    build_invalid_cases,
    build_valid_value,
    detect_domain_pattern,
    detect_domain_type,
    derive_domain_tags,
)


def test_detect_domain_type_treats_alphanumeric_serial_as_id():
    field_type, confidence = detect_domain_type(
        field_name_tr="Hareket Seri",
        field_name_en="Movement Serial",
        raw_type="Alfenumerik String",
        default_text="",
    )

    assert field_type == "id"
    assert confidence >= 0.95


def test_detect_domain_type_treats_vendor_note_as_string():
    field_type, confidence = detect_domain_type(
        field_name_tr="Tedarikçi Notu",
        field_name_en="Vendor Note",
        raw_type="Alfanumerik String",
        default_text="",
    )

    assert field_type == "string"
    assert confidence >= 0.9


def test_detect_domain_type_treats_check_type_as_enum():
    field_type, confidence = detect_domain_type(
        field_name_tr="Çek Türü",
        field_name_en="Check Type",
        raw_type="",
        default_text="",
    )

    assert field_type == "enum"
    assert confidence >= 0.9


def test_detect_domain_type_treats_lookup_address_as_id():
    field_type, _confidence = detect_domain_type(
        field_name_tr="Sevk Adresi",
        field_name_en="Shipment Address",
        raw_type='Adres Bilgileri listesinden "Birincil Adres" olarak seçilir.',
        default_text="",
    )

    assert field_type == "id"


def test_derive_domain_tags_detects_person_and_time():
    user_tags = derive_domain_tags("Ekleyen Kullanıcı", "User", "Kullanıcı", "")
    time_tags = derive_domain_tags("Saat", "Time", "Time", "")

    assert "person" in user_tags
    assert "time" in time_tags


def test_detect_domain_pattern_recognizes_iban():
    pattern = detect_domain_pattern("Hesap Numarası/IBAN", "Account Number/IBAN", "Alfanumerik String", "")
    assert pattern == r"^TR\d{24}$"


def test_build_invalid_cases_uses_domain_specific_id_policy():
    cases = build_invalid_cases(
        {
            "field_type": "id",
            "field_name_tr": "Belge Para Birimi",
            "field_name_en": "Currency",
            "semantic_tags": ["currency", "card"],
            "max_length": None,
        }
    )

    assert len(cases) == 3
    assert cases[0]["description"] == "geçersiz para birimi referansı"


def test_build_valid_and_duplicate_values_follow_domain_context():
    valid_value = build_valid_value(
        {
            "field_type": "id",
            "field_name_tr": "Cari Kodu",
            "field_name_en": "Current Code",
            "semantic_tags": ["card", "serial"],
            "json_field": "currentAccount.id",
            "max_length": 10,
        }
    )
    duplicate_value = build_duplicate_seed(
        {
            "field_type": "id",
            "field_name_tr": "Hareket Belge No",
            "field_name_en": "Movement Doc Nr",
            "semantic_tags": ["document", "serial"],
            "max_length": 12,
        }
    )

    assert valid_value == "CODE001"
    assert duplicate_value == "DOC-0001"


def test_build_valid_value_keeps_root_id_uuid_like():
    valid_value = build_valid_value(
        {
            "field_type": "bool",
            "field_name_tr": "Avans",
            "field_name_en": "Avans",
            "semantic_tags": [],
            "json_field": "id",
            "max_length": None,
        }
    )

    assert valid_value == "11111111-1111-4111-8111-111111111111"
