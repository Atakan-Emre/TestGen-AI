"""
BSC Generator - Facade sınıfı (sadece orkestrasyon)
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Shared modüller
from app.shared.logging import get_logger
from app.shared.io_loader import load_template, load_variables
from app.shared.json_structure import analyze_structure, set_nested_value, JsonSchemaInfo
from app.shared.value_factory import generate_value, create_null_payload
from app.shared.types import Constraints, MatchResult, BSCException
from app.shared.settings import INPUT_DIR
from app.shared.binding_runtime import apply_binding_profile, filter_bound_fields
from app.services.scenario_intelligence import load_scenario_profiles
from app.services.domain_tuning import (
    build_valid_value,
    normalize_text,
    resolve_preferred_field_type,
    resolve_target_leaf_path,
)

# BSC modüller
from .scenario_parser import parse_line
from .matcher import DefaultMatcher
from .writer import save_test_case, create_test_case_metadata, add_file_path_to_test_case
from . import rl_models


class BSCGenerator:
    """
    BSC Test Generator - Facade Pattern
    
    Public API korunarak sadece orkestrasyon yapar.
    Tüm iş mantığı alt modüllere delege edilir.
    """
    
    def __init__(self, logger=None, matcher=None, rl_bundle=None):
        """
        BSC Generator'ı başlat
        
        Args:
            logger: Logger instance (opsiyonel)
            matcher: Matcher instance (opsiyonel)
            rl_bundle: RL model paketi (opsiyonel)
        """
        self.logger = logger or get_logger(__name__)
        self.matcher = matcher or DefaultMatcher()
        self.rl_bundle = rl_bundle or rl_models.load_models()
        
        self.logger.info("BSCGenerator başlatıldı (Facade Pattern)")
    
    def generate_bsc_test(
        self,
        scenario_path: str,
        test_name: str,
        json_file_id: int,
        binding_profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        BSC test senaryosu oluştur
        
        Args:
            scenario_path: Senaryo dosyası yolu
            test_name: Test adı
            json_file_id: JSON dosya ID'si
            
        Returns:
            Oluşturulan test case
            
        Raises:
            BSCException: Test oluşturma hatası
        """
        try:
            self.logger.info(f"BSC test oluşturuluyor: {test_name}")
            
            # 1) Template yükle
            template = load_template(json_file_id)
            
            # 2) Variables yükle
            variables = load_variables()
            variables, ignored_fields, _mutation_blocked, _binding_payload = apply_binding_profile(
                binding_profile,
                variables,
                template,
                "bsc",
            )
            
            # 3) Şema analizi
            schema_info = analyze_structure(template)
            
            # 4) Senaryo satırlarını işle
            mandatory_fields = self._process_scenario_lines(scenario_path, schema_info)
            mandatory_fields = filter_bound_fields(mandatory_fields, ignored_fields)
            
            # 5) Test case oluştur
            test_case = self._create_test_case(template, variables, mandatory_fields, test_name)
            
            # 6) Test case'i kaydet
            if test_case:
                output_path = save_test_case(test_name, test_case)
                test_case = add_file_path_to_test_case(test_case, output_path)
            
            self.logger.info(f"BSC test başarıyla oluşturuldu: {test_name}")
            return test_case
            
        except Exception as e:
            error_msg = f"BSC test oluşturma hatası: {e}"
            self.logger.error(error_msg)
            raise BSCException(error_msg)
    
    def generate_bsc_test_with_variables(
        self,
        scenario_path: str,
        test_name: str,
        json_file_id: int,
        selected_variables: Optional[List[str]] = None,
        binding_profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Seçilen variables ile BSC test senaryosu oluştur
        
        Args:
            scenario_path: Senaryo dosyası yolu
            test_name: Test adı
            json_file_id: JSON dosya ID'si
            selected_variables: Seçilen değişken listesi (opsiyonel)
            
        Returns:
            Oluşturulan test case
            
        Raises:
            BSCException: Test oluşturma hatası
        """
        try:
            self.logger.info(f"BSC test oluşturuluyor (seçili variables): {test_name}")
            
            # 1) Template yükle
            template = load_template(json_file_id)
            
            # 2) Variables yükle (seçili dosyalardan)
            variables = {}
            if selected_variables:
                for var_file in selected_variables:
                    if var_file.startswith('variables_file:'):
                        file_name = var_file.replace('variables_file:', '')
                        file_path = INPUT_DIR / "Variables" / file_name
                        if file_path.exists():
                            file_variables = load_variables(file_path)
                            variables.update(file_variables)
                            self.logger.info(f"Variables dosyası yüklendi: {file_name} ({len(file_variables)} değişken)")
                        else:
                            self.logger.warning(f"Variables dosyası bulunamadı: {file_name}")
                self.logger.info(f"Toplam {len(variables)} değişken yüklendi")
            else:
                # Varsayılan variables dosyasını yükle
                variables = load_variables()
                self.logger.info(f"Varsayılan variables yüklendi: {len(variables)} değişken")
            
            variables, ignored_fields, _mutation_blocked, _binding_payload = apply_binding_profile(
                binding_profile,
                variables,
                template,
                "bsc",
            )

            # 3) Şema analizi
            schema_info = analyze_structure(template)
            self.logger.info(f"🔍 JSON şeması analiz edildi: {len(schema_info.paths)} alan bulundu")
            
            # 4) Senaryo satırlarını işle
            self.logger.info(f"📖 Senaryo dosyası okunuyor: {scenario_path}")
            mandatory_fields = self._process_scenario_lines(scenario_path, schema_info)
            mandatory_fields = filter_bound_fields(mandatory_fields, ignored_fields)
            self.logger.info(f"📊 Toplam {len(mandatory_fields)} zorunlu alan tespit edildi")
            
            # 5) Test case oluştur
            test_case = self._create_test_case(template, variables, mandatory_fields, test_name)
            
            # 6) Test case'i kaydet
            if test_case:
                output_path = save_test_case(test_name, test_case)
                test_case = add_file_path_to_test_case(test_case, output_path)
            
            self.logger.info(f"BSC test başarıyla oluşturuldu (seçili variables): {test_name}")
            return test_case
            
        except Exception as e:
            error_msg = f"BSC test oluşturma hatası (seçili variables): {e}"
            self.logger.error(error_msg)
            raise BSCException(error_msg)
    
    def generate_dynamic_bsc_test(self, scenario_path: str, test_name: str, json_file_id: int,
                                selected_variables: Optional[List[str]] = None,
                                dynamic_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Dinamik BSC test senaryosu oluştur
        
        Args:
            scenario_path: Senaryo dosyası yolu
            test_name: Test adı
            json_file_id: JSON dosya ID'si
            selected_variables: Seçilen değişken listesi (opsiyonel)
            dynamic_params: Dinamik parametreler (opsiyonel)
            
        Returns:
            Oluşturulan test case
            
        Raises:
            BSCException: Test oluşturma hatası
        """
        try:
            self.logger.info(f"Dinamik BSC test oluşturuluyor: {test_name}")
            
            # Normal BSC test oluştur
            test_case = self.generate_bsc_test_with_variables(
                scenario_path, test_name, json_file_id, selected_variables
            )
            
            # Dinamik parametreleri uygula
            if dynamic_params and test_case:
                test_case = self._apply_dynamic_params(test_case, dynamic_params)
            
            self.logger.info(f"Dinamik BSC test başarıyla oluşturuldu: {test_name}")
            return test_case
            
        except Exception as e:
            error_msg = f"Dinamik BSC test oluşturma hatası: {e}"
            self.logger.error(error_msg)
            raise BSCException(error_msg)
    
    def _process_scenario_lines(self, scenario_path: str, schema_info: JsonSchemaInfo) -> Dict[str, Dict[str, Any]]:
        """
        Senaryo satırlarını işle ve zorunlu alanları belirle
        
        Args:
            scenario_path: Senaryo dosyası yolu
            schema_info: JSON şema bilgisi
            
        Returns:
            Zorunlu alanlar mapping'i
        """
        try:
            scenario_file = Path(scenario_path)
            if not scenario_file.exists():
                raise BSCException(f"Senaryo dosyası bulunamadı: {scenario_path}")
            
            self.logger.info(f"Senaryo dosyası işleniyor: {scenario_path}")
            
            mandatory_fields = {}

            profiles = load_scenario_profiles(str(scenario_file))
            if profiles:
                self.logger.info(f"Yapilandirilmis scenario metadata bulundu: {len(profiles)} alan")
                iterable_constraints = [profile.to_constraints() for profile in profiles if profile.required]
            else:
                with open(scenario_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                self.logger.info(f"Toplam {len(lines)} satır okundu")
                iterable_constraints = []
                for line in lines:
                    parsed = parse_line(line.strip())
                    if parsed and parsed.required:
                        iterable_constraints.append(parsed)

            for line_num, constraints in enumerate(iterable_constraints, 1):
                try:
                    match_result = self.matcher.find_best_match(constraints, schema_info)

                    if match_result and match_result.score > 0.1:
                        field_context = self._build_field_context(match_result.path, constraints, schema_info)
                        target_path = resolve_target_leaf_path(
                            match_result.path,
                            schema_info.paths,
                            schema_info.types,
                            field_context,
                            )
                        if target_path != match_result.path:
                            self.logger.info(
                                "Object path leaf'e indirildi: %s -> %s",
                                match_result.path,
                                target_path,
                            )
                        if self._should_skip_id_like_match(target_path, constraints.source_field_tr, constraints.source_field_en):
                            self.logger.info(
                                "Id-benzeri yanlis eslesme atlandi: %s -> %s",
                                constraints.source_field_tr or constraints.source_field_en or f"satir_{line_num}",
                                target_path,
                            )
                            continue
                        minimum_score = self._minimum_match_score(
                            constraints.field_type,
                            schema_info.types.get(target_path),
                        )
                        if match_result.score < minimum_score:
                            self.logger.info(
                                "Dusuk guvenli eslesme atlandi: %s -> %s (%.3f < %.3f)",
                                constraints.source_field_tr or constraints.source_field_en or f"satir_{line_num}",
                                target_path,
                                match_result.score,
                                minimum_score,
                            )
                            continue
                        mandatory_fields[target_path] = {
                            'type': resolve_preferred_field_type(
                                constraints.field_type,
                                schema_info.types.get(target_path),
                            ),
                            'json_field': target_path,
                            'schema_type': schema_info.types.get(target_path),
                            'max_length': constraints.max_len,
                            'constraints': constraints,
                            'match_score': match_result.score,
                            'rationale': match_result.rationale
                        }

                        self.logger.info(
                            f"Zorunlu alan belirlendi: {match_result.path} (skor: {match_result.score:.3f})"
                        )
                    else:
                        self.logger.warning(f"Satır {line_num}: Uygun alan bulunamadı")

                except Exception as e:
                    self.logger.warning(f"Satır {line_num} işleme hatası: {e}")
                    continue
            
            self.logger.info(f"Toplam {len(mandatory_fields)} zorunlu alan belirlendi")
            return mandatory_fields
            
        except Exception as e:
            error_msg = f"Senaryo satırları işleme hatası: {e}"
            self.logger.error(error_msg)
            raise BSCException(error_msg)

    def _minimum_match_score(self, explicit_type: Optional[str], schema_type: Optional[str]) -> float:
        normalized_type = resolve_preferred_field_type(explicit_type, schema_type)
        if normalized_type in {"bool", "date"}:
            return 0.4
        return 0.45

    def _should_skip_id_like_match(
        self,
        target_path: str,
        source_field_tr: Optional[str],
        source_field_en: Optional[str],
    ) -> bool:
        normalized_source = normalize_text(f"{source_field_tr or ''} {source_field_en or ''}")
        if not normalized_source or not target_path.endswith(".id"):
            return False

        if any(token in normalized_source for token in ["type", "turu", "tipi", "status", "durum"]):
            return True

        if any(token in normalized_source for token in ["adi", "name", "description", "aciklama", "city", "il"]):
            protected_tokens = [
                "seri",
                "serial",
                "belge no",
                "doc nr",
                "document number",
                "kod",
                "code",
                "currency",
                "para birimi",
                "user",
                "kullanici",
                "card",
                "kart",
                "branch",
                "sube",
                "depo",
                "warehouse",
                "check no",
                "cek no",
            ]
            return not any(token in normalized_source for token in protected_tokens)

        return False
    
    def _create_test_case(self, template: Dict[str, Any], variables: Dict[str, str],
                         mandatory_fields: Dict[str, Dict[str, Any]], test_name: str) -> Dict[str, Any]:
        """
        Test case oluştur
        
        Args:
            template: JSON template
            variables: Değişken mapping'i
            mandatory_fields: Zorunlu alanlar
            test_name: Test adı
            
        Returns:
            Oluşturulan test case
        """
        try:
            self.logger.info("Test case oluşturuluyor...")
            
            # Null payload oluştur (eski generator'daki gibi)
            test_data = self._create_null_data(template)
            schema_info = analyze_structure(template)
            
            # Variables'ları ata (eski generator'daki gibi)
            for var_path, var_value in variables.items():
                parts = var_path.split('.')
                current = test_data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = var_value
            
            # VARIABLES ÖNCELİĞİ: Önce variables'da olan alanları işle
            self.logger.info(f"Variables önceliği ile {len(mandatory_fields)} zorunlu alan işleniyor...")
            
            # Variables'da olan alanları önce işle
            for field_path, field_info in mandatory_fields.items():
                if field_path in variables:
                    # Variables'da varsa, o değeri kullan (matcher'a gitme)
                    variables_value = variables[field_path]
                    self._set_nested_value(test_data, field_path, variables_value)
                    self.logger.info(f"📝 VARIABLES: '{field_path}' = {variables_value}")
                else:
                    # Variables'da yoksa matcher kullan
                    try:
                        constraints_obj = field_info.get('constraints') if isinstance(field_info, dict) else None
                        target_path = field_info.get('json_field', field_path)
                        schema_type = field_info.get('schema_type') or schema_info.types.get(target_path)
                        if constraints_obj is not None:
                            generated_value = generate_value(
                                field_info.get('type') or constraints_obj.field_type or 'string',
                                constraints_obj,
                                variables,
                                field_path=target_path,
                                schema_type=schema_type,
                            )
                            if generated_value is not None:
                                self._set_nested_value(test_data, target_path, generated_value)
                                self.logger.info(f"✅ Değer atandı: {target_path} = {generated_value}")
                        else:
                            # Fallback: eski yöntem
                            generated_value = self._generate_value_by_type(field_info, schema_type=schema_type)
                            if generated_value is not None:
                                self._set_nested_value(test_data, target_path, generated_value)
                                self.logger.debug(f"Fallback değer üretildi: {target_path} = {generated_value}")
                    except Exception as e:
                        self.logger.warning(f"Matcher hatası ({field_path}): {e}")
                        # Fallback: eski yöntem
                        generated_value = self._generate_value_by_type(
                            field_info,
                            schema_type=field_info.get('schema_type') if isinstance(field_info, dict) else None,
                        )
                        if generated_value is not None:
                            self._set_nested_value(test_data, field_path, generated_value)
                            self.logger.debug(f"Fallback değer üretildi: {field_path} = {generated_value}")
            
            # Özel alanlar için sabit değerler KALDIRILDI - sadece variables kullanılacak
            
            # Metadata oluştur
            metadata = create_test_case_metadata(
                test_name, 
                "BSC", 
                f"BSC test senaryosu - {test_name} ({len(mandatory_fields)} zorunlu alan)"
            )
            
            test_case = {
                **metadata,
                "test_data": test_data,
                "mandatory_fields_count": len(mandatory_fields),
                "variables_count": len(variables),
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Test case oluşturuldu: {len(mandatory_fields)} zorunlu alan")
            return test_case
            
        except Exception as e:
            error_msg = f"Test case oluşturma hatası: {e}"
            self.logger.error(error_msg)
            raise BSCException(error_msg)
    
    def _create_null_data(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Template'den null data oluştur (eski generator'dan)"""
        if isinstance(template, dict):
            return {k: self._create_null_data(v) if isinstance(v, (dict, list)) else None 
                   for k, v in template.items()}
        elif isinstance(template, list):
            if template:
                return [self._create_null_data(template[0])]
            return []
        return None

    def _build_field_context(
        self,
        field_path: str,
        constraints: Optional[Constraints] = None,
        schema_info: Optional[JsonSchemaInfo] = None,
        field_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        constraints = constraints or (field_info or {}).get("constraints")
        field_info = field_info or {}
        field_name_tr = constraints.source_field_tr if constraints else field_path.split(".")[-1]
        field_name_en = constraints.source_field_en if constraints else field_path.split(".")[-1]
        return {
            "json_field": field_path,
            "field_name_tr": field_name_tr,
            "field_name_en": field_name_en,
            "field_type": resolve_preferred_field_type(
                field_info.get("type") if field_info else None,
                schema_info.types.get(field_path) if schema_info else field_info.get("schema_type"),
            ),
            "schema_type": schema_info.types.get(field_path) if schema_info else field_info.get("schema_type"),
            "semantic_tags": (
                constraints.semantic_tags if constraints and constraints.semantic_tags else constraints.name_hints if constraints else []
            ),
            "pattern": constraints.pattern if constraints else field_info.get("pattern"),
            "enum_values": constraints.enum if constraints else field_info.get("enum_values"),
            "max_length": constraints.max_len if constraints else field_info.get("max_length"),
        }

    def _generate_value_by_type(self, field_info: Dict[str, Any], schema_type: Optional[str] = None) -> Any:
        """Tip bazlı değer üret (eski generator'dan)"""
        field_path = str(field_info.get('json_field', ''))
        field_type = resolve_preferred_field_type(field_info.get('type'), schema_type)
        
        try:
            if field_type == 'variable':
                return field_info.get('sample')
            field_context = self._build_field_context(
                field_path,
                field_info=field_info,
                schema_info=JsonSchemaInfo(paths=[], types={field_path: schema_type}, mandatory=set()),
            )
            return build_valid_value(field_context)
            
        except Exception as e:
            self.logger.warning(f"Değer üretme hatası ({field_path}): {str(e)}")
            return "test_value"

    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any) -> None:
        """Nested değer ata (genelleştirilmiş ve güvenli)"""
        try:
            parts = field_path.split('.')
            current: Any = data
            
            for i, raw_part in enumerate(parts):
                is_last = i == len(parts) - 1
                
                if '[' in raw_part and ']' in raw_part:
                    # Liste erişimi: name[index]
                    list_name = raw_part.split('[')[0]
                    index_str = raw_part.split('[')[1].split(']')[0]
                    index = int(index_str)

                    # Mevcut düğümü dict'e zorla
                    if not isinstance(current, dict):
                        raise TypeError(f"Ara düğüm dict değil: {type(current).__name__}")

                    if list_name not in current or not isinstance(current[list_name], list):
                        current[list_name] = []
                    while len(current[list_name]) <= index:
                        current[list_name].append({})
                    
                    if is_last:
                        # Son parça: değeri ata
                        current[list_name][index] = value
                    else:
                        # Son değilse içeri doğru ilerle
                        if not isinstance(current[list_name][index], dict):
                            current[list_name][index] = {}
                        current = current[list_name][index]
                else:
                    # Sıradan alan erişimi
                    if not is_last:
                        # Ara düğüm: dict oluştur ve içeri gir
                        if raw_part not in current:
                            current[raw_part] = {}
                        elif not isinstance(current[raw_part], dict):
                            # Eğer string/number ise, dict'e dönüştür
                            current[raw_part] = {}
                        current = current[raw_part]
                    else:
                        # Son alan: değeri ata
                        if isinstance(current, dict):
                            current[raw_part] = value
                        else:
                            raise TypeError(f"Ara düğüm dict değil: {type(current).__name__}")

        except Exception as e:
            self.logger.warning(f"Değer atama hatası ({field_path}): {str(e)}")

    def _apply_dynamic_params(self, test_case: Dict[str, Any], dynamic_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dinamik parametreleri uygula
        
        Args:
            test_case: Test case verisi
            dynamic_params: Dinamik parametreler
            
        Returns:
            Güncellenmiş test case
        """
        try:
            self.logger.info(f"Dinamik parametreler uygulanıyor: {list(dynamic_params.keys())}")
            
            # Test case'e dinamik parametreleri ekle
            test_case["dynamic_params"] = dynamic_params
            test_case["is_dynamic"] = True
            
            # Özel dinamik işlemler burada yapılabilir
            # Örnek: RL model kullanımı, özel değer üretimi vb.
            
            if self.rl_bundle and self.rl_bundle.field_matcher:
                self.logger.info("RL model kullanılarak dinamik işlemler yapılıyor")
                # RL model kullanımı burada implement edilebilir
            
            return test_case
            
        except Exception as e:
            self.logger.warning(f"Dinamik parametre uygulama hatası: {e}")
            return test_case
