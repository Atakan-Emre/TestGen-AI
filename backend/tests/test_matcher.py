"""
Matcher birim testleri
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from app.generators.bsc.matcher import DefaultMatcher
from app.shared.types import Constraints, JsonSchemaInfo


class TestMatcher:
    """Matcher testleri"""
    
    def setup_method(self):
        """Test setup"""
        self.matcher = DefaultMatcher()
    
    def test_score_by_rules_type_match(self):
        """Tip uyumu skorlama testi"""
        constraints = Constraints(
            name_hints=["tarih"],
            field_type="date",
            required=True,
            max_len=None,
            pattern=None,
            enum=None,
            locale=None
        )
        
        path_tokens = ["issue", "date"]
        schema_type = "date"
        
        score = self.matcher.score_by_rules(constraints, path_tokens, schema_type)
        
        # Tip uyumu ve isim benzerliği nedeniyle yüksek skor bekleniyor
        assert score >= 0.5
    
    def test_score_by_rules_name_similarity(self):
        """İsim benzerliği skorlama testi"""
        constraints = Constraints(
            name_hints=["tutar", "amount"],
            field_type="number",
            required=True,
            max_len=None,
            pattern=None,
            enum=None,
            locale=None
        )
        
        path_tokens = ["total", "amount"]
        schema_type = "number"
        
        score = self.matcher.score_by_rules(constraints, path_tokens, schema_type)
        
        # İsim benzerliği nedeniyle yüksek skor bekleniyor
        assert score > 0.3
    
    def test_score_by_rules_mandatory_field(self):
        """Zorunlu alan skorlama testi"""
        constraints = Constraints(
            name_hints=["id"],
            field_type="string",
            required=True,
            max_len=None,
            pattern=None,
            enum=None,
            locale=None
        )
        
        path_tokens = ["document", "id"]
        schema_type = "string"
        
        score = self.matcher.score_by_rules(constraints, path_tokens, schema_type)
        
        # Zorunlu alan ve önemli keyword nedeniyle yüksek skor bekleniyor
        assert score > 0.4
    
    def test_score_by_rules_dictionary_similarity(self):
        """Sözlük benzerliği skorlama testi"""
        constraints = Constraints(
            name_hints=["vergi"],
            field_type="string",
            required=True,
            max_len=None,
            pattern=None,
            enum=None,
            locale=None
        )
        
        path_tokens = ["tax", "id"]
        schema_type = "string"
        
        score = self.matcher.score_by_rules(constraints, path_tokens, schema_type)
        
        # Türkçe-İngilizce sözlük benzerliği nedeniyle skor bekleniyor
        assert score > 0.2
    
    @patch('app.generators.bsc.matcher.SentenceTransformer')
    def test_find_best_match(self, mock_transformer):
        """En iyi eşleşme bulma testi"""
        # Mock transformer setup
        mock_model = Mock()
        mock_model.encode.side_effect = lambda texts, convert_to_numpy=True: np.array(
            [[float(index + 1)] * 16 for index, _ in enumerate(texts)]
        )
        mock_transformer.return_value = mock_model
        DefaultMatcher._model_instance = None
        DefaultMatcher._model_name = None
        
        # Schema info oluştur
        schema_info = JsonSchemaInfo(
            paths=["header.issueDate", "header.totalAmount", "lines[0].unitPrice"],
            types={
                "header.issueDate": "date",
                "header.totalAmount": "amount", 
                "lines[0].unitPrice": "amount"
            },
            mandatory={"header.issueDate", "header.totalAmount"}
        )
        
        # Constraints oluştur
        constraints = Constraints(
            name_hints=["tarih", "date"],
            field_type="date",
            required=True,
            max_len=None,
            pattern=None,
            enum=None,
            locale=None
        )
        
        # Matcher'ı yeniden başlat (mock ile)
        matcher = DefaultMatcher()
        
        # En iyi eşleşmeyi bul
        result = matcher.find_best_match(constraints, schema_info)
        
        assert result is not None
        assert result.path in schema_info.paths
        assert result.score > 0
        assert result.rationale is not None
    
    def test_simple_similarity(self):
        """Basit string benzerliği testi"""
        # Tam eşleşme
        assert self.matcher._simple_similarity("test", "test") == 1.0
        
        # Kısmi eşleşme
        similarity = self.matcher._simple_similarity("test", "testing")
        assert 0 < similarity < 1.0
        
        # Farklı stringler
        similarity = self.matcher._simple_similarity("test", "hello")
        assert similarity < 0.5
        
        # Boş stringler
        assert self.matcher._simple_similarity("", "") == 0.0
        assert self.matcher._simple_similarity("test", "") == 0.0
    
    def test_check_type_match(self):
        """Tip uyumu kontrolü testi"""
        # Tam eşleşme
        assert self.matcher._check_type_match("string", "string") == 1.0
        
        # Mapping eşleşmesi
        assert self.matcher._check_type_match("id", "uuid") == 0.8
        assert self.matcher._check_type_match("number", "amount") == 0.8
        
        # Kısmi eşleşme
        assert self.matcher._check_type_match("string", "string_value") == 0.5
        
        # Eşleşmeyen
        assert self.matcher._check_type_match("string", "id") == 0.0
        assert self.matcher._check_type_match("string", "number") == 0.0

    def test_generic_path_penalty_discourages_non_id_hint_for_id_path(self):
        constraints = Constraints(
            name_hints=["belge adı", "doc name"],
            field_type="string",
            required=True,
            max_len=None,
            pattern=None,
            enum=None,
            locale=None,
            source_field_tr="Belge Adı",
            source_field_en="Doc Name",
        )

        penalty = self.matcher._generic_path_penalty(
            constraints,
            ["branch", "document", "series", "id"],
            "id",
            0.18,
        )

        assert penalty == 0.15
    
    def test_check_mandatory_field(self):
        """Zorunlu alan kontrolü testi"""
        # Önemli keyword'ler
        assert self.matcher._check_mandatory_field(["id"]) == 1.0
        assert self.matcher._check_mandatory_field(["code"]) == 1.0
        assert self.matcher._check_mandatory_field(["name"]) == 1.0
        
        # Normal token'ler
        assert self.matcher._check_mandatory_field(["description"]) == 0.5
        assert self.matcher._check_mandatory_field(["value"]) == 0.5
    
    def test_check_dictionary_similarity(self):
        """Sözlük benzerliği kontrolü testi"""
        # Türkçe-İngilizce eşleşme
        assert self.matcher._check_dictionary_similarity(["tarih"], ["date"]) == 1.0
        assert self.matcher._check_dictionary_similarity(["vergi"], ["tax"]) == 1.0
        assert self.matcher._check_dictionary_similarity(["tutar"], ["amount"]) == 1.0
        
        # Eşleşmeyen
        assert self.matcher._check_dictionary_similarity(["test"], ["hello"]) == 0.0
        assert self.matcher._check_dictionary_similarity([], ["test"]) == 0.0
    
    def test_check_name_similarity(self):
        """İsim benzerliği kontrolü testi"""
        # Tam eşleşme
        score = self.matcher._check_name_similarity(["date"], ["date"])
        assert score == 1.0
        
        # Kısmi eşleşme
        score = self.matcher._check_name_similarity(["date"], ["issue_date"])
        assert score > 0.5
        
        # Eşleşmeyen
        score = self.matcher._check_name_similarity(["date"], ["amount"])
        assert score == 0.0
        
        # Boş listeler
        assert self.matcher._check_name_similarity([], ["test"]) == 0.0
        assert self.matcher._check_name_similarity(["test"], []) == 0.0
