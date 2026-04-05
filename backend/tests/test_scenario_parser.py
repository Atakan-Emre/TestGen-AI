"""
Senaryo ayrıştırma birim testleri
"""
import pytest
from app.generators.bsc.scenario_parser import parse_line, extract_type_and_limits, is_required, is_optional, is_unique


class TestScenarioParser:
    """Senaryo ayrıştırma testleri"""
    
    def test_parse_line_basic(self):
        """Temel satır parse testi"""
        line = "Tarih alanı zorunludur (issueDate)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert "tarih" in [hint.lower() for hint in constraints.name_hints]
        assert constraints.required is True
        assert constraints.field_type == "date"
    
    def test_parse_line_with_limits(self):
        """Limit bilgileri ile satır parse testi"""
        line = "Ürün adı maksimum 50 karakterli olmalıdır (productName)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert constraints.max_len == 50
        assert constraints.field_type == "string"
    
    def test_parse_line_numeric(self):
        """Sayısal alan parse testi"""
        line = "Tutar alanı sadece rakam olmalıdır (amount)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert constraints.field_type == "number"
        assert any("tutar" in hint.lower() for hint in constraints.name_hints)
    
    def test_parse_line_iban(self):
        """IBAN alanı parse testi"""
        line = "IBAN alanı zorunludur (iban)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert "iban" in [hint.lower() for hint in constraints.name_hints]
        assert constraints.pattern is not None
        assert "TR" in constraints.pattern
    
    def test_parse_line_tckn(self):
        """TCKN alanı parse testi"""
        line = "TC Kimlik No zorunludur (tckn)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert "tckn" in [hint.lower() for hint in constraints.name_hints]
        assert constraints.pattern is not None
        assert r"\d{11}" in constraints.pattern
    
    def test_extract_type_and_limits(self):
        """Tip ve limit çıkarma testi"""
        # Tarih testi
        field_type, max_len, pattern = extract_type_and_limits("YYYY-AA-GG formatında tarih")
        assert field_type == "date"
        
        # Maksimum uzunluk testi
        field_type, max_len, pattern = extract_type_and_limits("maksimum 20 karakterli metin")
        assert max_len == 20
        
        # Sayısal test
        field_type, max_len, pattern = extract_type_and_limits("sadece rakam")
        assert field_type == "number"
        
        # Boolean test
        field_type, max_len, pattern = extract_type_and_limits("evet/hayır değeri")
        assert field_type == "bool"
    
    def test_is_required(self):
        """Zorunlu alan tespiti testi"""
        assert is_required("Bu alan zorunludur") is True
        assert is_required("doldurulması zorunlu") is True
        assert is_required("mandatory field") is True
        assert is_required("Bu alan isteğe bağlıdır") is False
        assert is_required("Normal açıklama") is False
    
    def test_parse_line_complex(self):
        """Karmaşık satır parse testi"""
        line = "Vergi kimlik numarası (VKN) maksimum 10 karakterli ve zorunludur (taxId)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert constraints.required is True
        assert constraints.max_len == 10
        assert "vergi" in [hint.lower() for hint in constraints.name_hints]
        assert "tax" in [hint.lower() for hint in constraints.name_hints]
        assert constraints.source_field_en == "taxId"
    
    def test_parse_line_enum(self):
        """Enum değerleri parse testi"""
        line = "Kart tipi STOCK_CARD, VENDOR_CARD olabilir (cardType)"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert constraints.enum is not None
        assert "STOCK_CARD" in constraints.enum
        assert "VENDOR_CARD" in constraints.enum
    
    def test_parse_line_empty(self):
        """Boş satır parse testi"""
        assert parse_line("") is None
        assert parse_line("   ") is None
        assert parse_line("# Yorum satırı") is None
    
    def test_parse_line_tr_en(self):
        """TR-EN format parse testi"""
        line = "Ürün açıklaması (productDescription) maksimum 200 karakterli olmalıdır"
        
        constraints = parse_line(line)
        
        assert constraints is not None
        assert "ürün" in [hint.lower() for hint in constraints.name_hints]
        assert "açıklama" in [hint.lower() for hint in constraints.name_hints]
        assert constraints.max_len == 200
        assert constraints.field_type == "string"

    def test_optional_and_unique_detection(self):
        constraints = parse_line("Belge No (Document No) alanı opsiyoneldir ve tekildir.")

        assert constraints is not None
        assert constraints.optional is True
        assert constraints.unique is True
        assert is_optional("opsiyoneldir") is True
        assert is_unique("tekildir") is True
