"""
JSON yapısı analizi birim testleri
"""
import pytest
from app.shared.json_structure import analyze_structure, set_nested_value, JsonSchemaInfo


class TestJsonStructure:
    """JSON yapısı analizi testleri"""
    
    def test_analyze_structure_basic(self):
        """Temel JSON yapısı analizi"""
        template = {
            "header": {
                "id": "TEST-001",
                "issueDate": "2024-01-01",
                "totalAmount": 1000.50
            },
            "lines": [
                {
                    "lineId": 1,
                    "unitPrice": 100.0,
                    "quantity": 10
                }
            ]
        }
        
        schema_info = analyze_structure(template)
        
        # Path'lerin doğru çıkarıldığını kontrol et
        assert "header.id" in schema_info.paths
        assert "header.issueDate" in schema_info.paths
        assert "header.totalAmount" in schema_info.paths
        assert "lines[0].lineId" in schema_info.paths
        assert "lines[0].unitPrice" in schema_info.paths
        assert "lines[0].quantity" in schema_info.paths
        
        # Tip'lerin doğru belirlendiğini kontrol et
        assert schema_info.types["header.id"] == "id"
        assert schema_info.types["header.issueDate"] == "date"
        assert schema_info.types["header.totalAmount"] == "amount"
        assert schema_info.types["lines[0].lineId"] == "id"
        assert schema_info.types["lines[0].unitPrice"] == "amount"
        assert schema_info.types["lines[0].quantity"] == "number"
        
        # Zorunlu alanların doğru belirlendiğini kontrol et
        assert "header.id" in schema_info.mandatory
        assert "lines[0].lineId" in schema_info.mandatory
    
    def test_set_nested_value_simple(self):
        """Basit nested değer atama"""
        doc = {"header": {"id": "old"}}
        
        set_nested_value(doc, "header.id", "new_value")
        
        assert doc["header"]["id"] == "new_value"
    
    def test_set_nested_value_array(self):
        """Array index ile nested değer atama"""
        doc = {"lines": [{"price": 100}]}
        
        set_nested_value(doc, "lines[0].price", 200)
        
        assert doc["lines"][0]["price"] == 200
    
    def test_set_nested_value_create_missing(self):
        """Eksik nested objeleri oluştur"""
        doc = {}
        
        set_nested_value(doc, "header.details.id", "TEST-001")
        
        assert doc["header"]["details"]["id"] == "TEST-001"
    
    def test_set_nested_value_array_create(self):
        """Eksik array elemanlarını oluştur"""
        doc = {"lines": []}
        
        set_nested_value(doc, "lines[0].id", 1)
        
        assert len(doc["lines"]) == 1
        assert doc["lines"][0]["id"] == 1
    
    def test_analyze_structure_complex(self):
        """Karmaşık JSON yapısı analizi"""
        template = {
            "document": {
                "header": {
                    "id": "DOC-001",
                    "issueDate": "2024-01-01T10:00:00Z",
                    "totalAmount": 1500.75,
                    "currency": {"id": "TRY", "unit": 0},
                    "vatRate": {"id": "18", "ratio": {"denominator": 100, "numerator": 18}}
                },
                "lineList": [
                    {
                        "lineId": 1,
                        "productCode": "PROD-001",
                        "quantity": 5,
                        "unitPrice": 100.0,
                        "totalPrice": 500.0
                    },
                    {
                        "lineId": 2,
                        "productCode": "PROD-002",
                        "quantity": 3,
                        "unitPrice": 200.0,
                        "totalPrice": 600.0
                    }
                ]
            }
        }
        
        schema_info = analyze_structure(template)
        
        # Tüm path'lerin çıkarıldığını kontrol et
        expected_paths = [
            "document.header.id",
            "document.header.issueDate",
            "document.header.totalAmount",
            "document.header.currency.id",
            "document.header.currency.unit",
            "document.header.vatRate.id",
            "document.header.vatRate.ratio.denominator",
            "document.header.vatRate.ratio.numerator",
            "document.lineList[0].lineId",
            "document.lineList[0].productCode",
            "document.lineList[0].quantity",
            "document.lineList[0].unitPrice",
            "document.lineList[0].totalPrice"
        ]
        
        for path in expected_paths:
            assert path in schema_info.paths, f"Path bulunamadı: {path}"
        
        # Tip'lerin doğru belirlendiğini kontrol et
        assert schema_info.types["document.header.id"] == "id"
        assert schema_info.types["document.header.issueDate"] == "date"
        assert schema_info.types["document.header.totalAmount"] == "amount"
        assert schema_info.types["document.header.currency.id"] == "id"
        assert schema_info.types["document.header.vatRate.ratio.denominator"] == "number"
        
        # Array tipinin doğru belirlendiğini kontrol et
        assert "array<object>" in schema_info.types["document.lineList[0]"]
