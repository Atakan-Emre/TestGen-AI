"""
BSC Generator facade birim testleri
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from app.generators.bsc import BSCGenerator
from app.shared.types import Constraints, JsonSchemaInfo


class TestBSCGenerator:
    """BSC Generator facade testleri"""
    
    def setup_method(self):
        """Test setup"""
        self.generator = BSCGenerator()
    
    @patch('app.generators.bsc.bsc_generator.save_test_case')
    @patch('app.generators.bsc.bsc_generator.analyze_structure')
    @patch('app.generators.bsc.bsc_generator.load_variables')
    @patch('app.generators.bsc.bsc_generator.load_template')
    def test_generate_bsc_test_success(self, mock_load_template, mock_load_vars, mock_analyze, mock_save):
        """Başarılı BSC test oluşturma testi"""
        # Mock setup
        mock_load_template.return_value = {"header": {"id": "TEST-001"}}
        mock_load_vars.return_value = {"header.id": "{{test_id}}"}
        mock_analyze.return_value = JsonSchemaInfo(
            paths=["header.id"],
            types={"header.id": "string"},
            mandatory={"header.id"}
        )
        mock_save.return_value = Path("/test/output.json")
        mandatory_fields = {
            "header.id": {
                "type": "string",
                "json_field": "header.id",
                "schema_type": "string",
                "max_length": None,
                "constraints": Constraints(
                    name_hints=["id"],
                    field_type="string",
                    required=True,
                    max_len=None,
                    pattern=None,
                    enum=None,
                    locale=None,
                ),
                "match_score": 0.8,
                "rationale": "Test match",
            }
        }

        with patch.object(self.generator, "_process_scenario_lines", return_value=mandatory_fields):
            result = self.generator.generate_bsc_test(
                scenario_path="/test/scenario.txt",
                test_name="test_bsc",
                json_file_id=1
            )
        
        # Assertions
        assert result is not None
        assert "test_data" in result
        assert "scenario_type" in result
        assert result["scenario_type"] == "BSC"
        assert "file_path" in result
        
        # Mock calls kontrolü
        mock_load_template.assert_called_once_with(1)
        mock_load_vars.assert_called_once()
        mock_analyze.assert_called()
        mock_save.assert_called_once()
    
    @patch('app.generators.bsc.bsc_generator.load_template')
    def test_generate_bsc_test_template_error(self, mock_load_template):
        """Template yükleme hatası testi"""
        # Mock setup
        mock_load_template.side_effect = Exception("Template bulunamadı")
        
        # Test
        with pytest.raises(Exception) as exc_info:
            self.generator.generate_bsc_test(
                scenario_path="/test/scenario.txt",
                test_name="test_bsc",
                json_file_id=1
            )
        
        assert "Template bulunamadı" in str(exc_info.value)
    
    @patch('app.generators.bsc.bsc_generator.analyze_structure')
    @patch('app.generators.bsc.bsc_generator.load_variables')
    @patch('app.generators.bsc.bsc_generator.load_template')
    def test_generate_bsc_test_with_variables(self, mock_load_template, mock_load_vars, mock_analyze):
        """Seçili variables ile test oluşturma testi"""
        # Mock setup
        mock_load_template.return_value = {"header": {"id": "TEST-001"}}
        mock_load_vars.return_value = {
            "header.id": "{{test_id}}",
            "header.name": "{{test_name}}",
            "header.description": "{{test_desc}}"
        }
        mock_analyze.return_value = JsonSchemaInfo(
            paths=["header.id", "header.name", "header.description"],
            types={"header.id": "string", "header.name": "string", "header.description": "string"},
            mandatory={"header.id"}
        )
        mandatory_fields = {
            "header.id": {
                "type": "string",
                "json_field": "header.id",
                "schema_type": "string",
                "max_length": None,
                "constraints": Constraints(
                    name_hints=["id"],
                    field_type="string",
                    required=True,
                    max_len=None,
                    pattern=None,
                    enum=None,
                    locale=None,
                ),
                "match_score": 0.8,
                "rationale": "Test match",
            }
        }

        with patch.object(Path, "exists", return_value=True), \
             patch.object(self.generator, "_process_scenario_lines", return_value=mandatory_fields), \
             patch('app.generators.bsc.bsc_generator.save_test_case') as mock_save:
            mock_save.return_value = Path("/test/output.json")

            # Test - seçili variables dosyası ile
            selected_vars = ["variables_file:variablesHeader.txt"]
            result = self.generator.generate_bsc_test_with_variables(
                scenario_path="/test/scenario.txt",
                test_name="test_bsc",
                json_file_id=1,
                selected_variables=selected_vars
            )
        
        # Assertions
        assert result is not None
        assert "test_data" in result
        
        # Seçili variables kullanıldığını kontrol et
        mock_load_vars.assert_called_once()
    
    @patch('app.generators.bsc.bsc_generator.analyze_structure')
    @patch('app.generators.bsc.bsc_generator.load_variables')
    @patch('app.generators.bsc.bsc_generator.load_template')
    def test_generate_dynamic_bsc_test(self, mock_load_template, mock_load_vars, mock_analyze):
        """Dinamik BSC test oluşturma testi"""
        # Mock setup
        mock_load_template.return_value = {"header": {"id": "TEST-001"}}
        mock_load_vars.return_value = {"header.id": "{{test_id}}"}
        mock_analyze.return_value = JsonSchemaInfo(
            paths=["header.id"],
            types={"header.id": "string"},
            mandatory={"header.id"}
        )
        mandatory_fields = {
            "header.id": {
                "type": "string",
                "json_field": "header.id",
                "schema_type": "string",
                "max_length": None,
                "constraints": Constraints(
                    name_hints=["id"],
                    field_type="string",
                    required=True,
                    max_len=None,
                    pattern=None,
                    enum=None,
                    locale=None,
                ),
                "match_score": 0.8,
                "rationale": "Test match",
            }
        }

        with patch.object(self.generator, "_process_scenario_lines", return_value=mandatory_fields), \
             patch('app.generators.bsc.bsc_generator.save_test_case') as mock_save:
            mock_save.return_value = Path("/test/output.json")

            # Test - dinamik parametreler ile
            dynamic_params = {"use_rl": True, "max_iterations": 100}
            result = self.generator.generate_dynamic_bsc_test(
                scenario_path="/test/scenario.txt",
                test_name="test_bsc",
                json_file_id=1,
                dynamic_params=dynamic_params
            )
        
        # Assertions
        assert result is not None
        assert "dynamic_params" in result
        assert result["dynamic_params"] == dynamic_params
        assert result["is_dynamic"] is True
    
    def test_process_scenario_lines(self):
        """Senaryo satırları işleme testi"""
        # Mock schema info
        schema_info = JsonSchemaInfo(
            paths=["header.issueDate", "header.totalAmount"],
            types={"header.issueDate": "date", "header.totalAmount": "amount"},
            mandatory={"header.issueDate", "header.totalAmount"}
        )
        
        # Mock scenario file
        scenario_content = [
            "Tarih alanı zorunludur (issueDate)\n",
            "Tutar alanı zorunludur (amount)\n",
            "Açıklama alanı isteğe bağlıdır (description)\n"
        ]
        
        with patch('app.generators.bsc.bsc_generator.load_scenario_profiles', return_value=[]), \
             patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", MagicMock()) as mock_file:
            mock_file.return_value.__enter__.return_value.readlines.return_value = scenario_content
            
            # Mock matcher
            mock_matcher = Mock()
            mock_matcher.find_best_match.return_value = Mock(
                path="header.issueDate",
                score=0.8,
                rationale="Good match"
            )
            
            self.generator.matcher = mock_matcher
            
            # Test
            mandatory_fields = self.generator._process_scenario_lines("/test/scenario.txt", schema_info)
        
        # Assertions
        assert len(mandatory_fields) > 0
        mock_matcher.find_best_match.assert_called()
    
    def test_create_test_case(self):
        """Test case oluşturma testi"""
        # Mock data
        template = {"header": {"id": "TEST-001"}}
        variables = {"header.id": "{{test_id}}"}
        mandatory_fields = {
            "header.issueDate": {
                "type": "date",
                "max_length": None,
                "constraints": Constraints(
                    name_hints=["tarih"],
                    field_type="date",
                    required=True,
                    max_len=None,
                    pattern=None,
                    enum=None,
                    locale=None
                ),
                "match_score": 0.8,
                "rationale": "Good match"
            }
        }
        
        with patch('app.generators.bsc.bsc_generator.generate_value') as mock_generate:
            mock_generate.return_value = "2024-01-01"
            
            # Test
            test_case = self.generator._create_test_case(template, variables, mandatory_fields, "test_bsc")
        
        # Assertions
        assert test_case is not None
        assert "test_data" in test_case
        assert "scenario_type" in test_case
        assert test_case["scenario_type"] == "BSC"
        assert "mandatory_fields_count" in test_case
        assert test_case["mandatory_fields_count"] == 1
        assert "variables_count" in test_case
        assert test_case["variables_count"] == 1
    
    def test_apply_dynamic_params(self):
        """Dinamik parametre uygulama testi"""
        test_case = {"scenario_type": "BSC", "test_data": {}}
        dynamic_params = {"use_rl": True, "max_iterations": 100}
        
        # Test
        result = self.generator._apply_dynamic_params(test_case, dynamic_params)
        
        # Assertions
        assert result["dynamic_params"] == dynamic_params
        assert result["is_dynamic"] is True
