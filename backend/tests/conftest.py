"""
Pytest konfigürasyonu ve ortak fixture'lar
"""
import pytest
import tempfile
import json
from pathlib import Path
from app.shared.types import JsonSchemaInfo, Constraints


@pytest.fixture
def sample_template():
    """Örnek JSON template"""
    return {
        "header": {
            "id": "TEST-001",
            "issueDate": "2024-01-01T10:00:00Z",
            "totalAmount": 1500.75,
            "currency": {"id": "TRY", "unit": 0},
            "vatRate": {
                "id": "18",
                "ratio": {"denominator": 100, "numerator": 18}
            }
        },
        "lineList": [
            {
                "lineId": 1,
                "productCode": "PROD-001",
                "quantity": 5,
                "unitPrice": 100.0,
                "totalPrice": 500.0
            }
        ]
    }


@pytest.fixture
def sample_variables():
    """Örnek variables"""
    return {
        "header.id": "{{test_id}}",
        "header.issueDate": "{{issue_date}}",
        "header.totalAmount": "{{total_amount}}",
        "lineList[0].productCode": "{{product_code}}"
    }


@pytest.fixture
def sample_schema_info():
    """Örnek schema info"""
    return JsonSchemaInfo(
        paths=[
            "header.id",
            "header.issueDate", 
            "header.totalAmount",
            "header.currency.id",
            "header.currency.unit",
            "header.vatRate.id",
            "header.vatRate.ratio.denominator",
            "header.vatRate.ratio.numerator",
            "lineList[0].lineId",
            "lineList[0].productCode",
            "lineList[0].quantity",
            "lineList[0].unitPrice",
            "lineList[0].totalPrice"
        ],
        types={
            "header.id": "id",
            "header.issueDate": "date",
            "header.totalAmount": "amount",
            "header.currency.id": "id",
            "header.currency.unit": "number",
            "header.vatRate.id": "id",
            "header.vatRate.ratio.denominator": "number",
            "header.vatRate.ratio.numerator": "number",
            "lineList[0].lineId": "number",
            "lineList[0].productCode": "code",
            "lineList[0].quantity": "number",
            "lineList[0].unitPrice": "amount",
            "lineList[0].totalPrice": "amount"
        },
        mandatory={
            "header.id",
            "header.issueDate",
            "header.totalAmount",
            "lineList[0].lineId",
            "lineList[0].productCode"
        }
    )


@pytest.fixture
def sample_constraints():
    """Örnek constraints"""
    return Constraints(
        name_hints=["tarih", "date"],
        field_type="date",
        required=True,
        max_len=None,
        pattern=None,
        enum=None,
        locale="tr-TR"
    )


@pytest.fixture
def temp_scenario_file():
    """Geçici senaryo dosyası"""
    content = """Tarih alanı zorunludur (issueDate)
Tutar alanı zorunludur (totalAmount)
Ürün kodu maksimum 20 karakterli olmalıdır (productCode)
Miktar alanı sadece rakam olmalıdır (quantity)
IBAN alanı zorunludur (iban)
TC Kimlik No zorunludur (tckn)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_json_file():
    """Geçici JSON dosyası"""
    content = {
        "header": {
            "id": "TEST-001",
            "issueDate": "2024-01-01",
            "totalAmount": 1000.0
        },
        "lines": [
            {
                "lineId": 1,
                "unitPrice": 100.0,
                "quantity": 10
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(content, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_variables_file():
    """Geçici variables dosyası"""
    content = """header.id={{test_id}}
header.issueDate={{issue_date}}
header.totalAmount={{total_amount}}
lines[0].unitPrice={{unit_price}}
lines[0].quantity={{quantity}}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_logger():
    """Mock logger"""
    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    return logger
