"""
Alan eşleştirme - embedding + rule-based ensemble
"""
import numpy as np
from functools import lru_cache
from typing import List, Dict, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from app.shared.json_structure import JsonSchemaInfo, split_camel_case, normalize_name
from app.shared.types import Constraints, MatchResult, MatchingError
from app.shared.logging import get_logger
from app.shared.settings import EMB_MODEL_NAME, MATCH_WEIGHTS


logger = get_logger(__name__)

GENERIC_PATH_TOKENS = {"id", "code", "name", "type", "status", "value"}
ID_LIKE_HINT_TOKENS = {
    "id",
    "code",
    "uuid",
    "serial",
    "seri",
    "reference",
    "referans",
    "number",
    "numara",
    "no",
    "iban",
    "hesap",
    "account",
    "card",
    "kart",
    "user",
    "kullanici",
    "currency",
    "branch",
    "sube",
}


class DefaultMatcher:
    """
    Varsayılan alan eşleştirici - semantic + rule-based ensemble
    """
    
    _model_instance = None
    _model_name = None
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Matcher'ı başlat
        
        Args:
            model_name: Embedding model adı (opsiyonel)
        """
        self.model_name = model_name or EMB_MODEL_NAME
        self._field_embeddings_cache = {}
        
        logger.info(f"DefaultMatcher başlatılıyor: {self.model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading ile model'i al (singleton pattern)"""
        if DefaultMatcher._model_instance is None or DefaultMatcher._model_name != self.model_name:
            try:
                logger.info(f"Embedding model yükleniyor: {self.model_name}")
                DefaultMatcher._model_instance = SentenceTransformer(self.model_name)
                DefaultMatcher._model_name = self.model_name
                logger.info("Embedding model başarıyla yüklendi")
            except Exception as e:
                logger.error(f"Model yükleme hatası: {e}")
                raise MatchingError(f"Embedding model yüklenemedi: {e}")
        return DefaultMatcher._model_instance
    
    @lru_cache(maxsize=512)
    def get_field_embeddings(self, paths: tuple) -> np.ndarray:
        """
        Alan path'leri için embedding'leri al (cache'li)
        
        Args:
            paths: Alan path'lerinin tuple'ı
            
        Returns:
            Embedding matrisi
        """
        try:
            # Path'leri normalize et ve birleştir
            normalized_paths = []
            for path in paths:
                # CamelCase'i kelimelere ayır
                words = split_camel_case(path)
                # Normalize et ve birleştir
                normalized = " ".join(words)
                normalized_paths.append(normalized)
            
            # Embedding'leri hesapla
            embeddings = self.model.encode(normalized_paths, convert_to_numpy=True)
            
            logger.debug(f"Embedding'ler hesaplandı: {len(paths)} path")
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding hesaplama hatası: {e}")
            raise MatchingError(f"Embedding hesaplanamadı: {e}")
    
    def score_by_rules(self, constraints: Constraints, path_name_tokens: List[str], 
                      schema_type: str) -> float:
        """
        Rule-based skorlama
        
        Args:
            constraints: Kısıtlamalar
            path_name_tokens: Path adı token'ları
            schema_type: Şema tipi
            
        Returns:
            Rule-based skor (0-1)
        """
        try:
            score = 0.0
            total_checks = 0
            
            # Tip uyumu kontrolü
            if constraints.field_type and schema_type:
                type_match = self._check_type_match(constraints.field_type, schema_type)
                score += type_match * 0.3
                total_checks += 1
            
            # İsim benzerliği kontrolü
            name_score = self._check_name_similarity(constraints.name_hints, path_name_tokens)
            score += name_score * 0.4
            total_checks += 1
            
            # Zorunlu alan kontrolü
            if constraints.required:
                # Zorunlu alanlar genellikle önemli alanlardır
                mandatory_score = self._check_mandatory_field(path_name_tokens)
                score += mandatory_score * 0.2
                total_checks += 1
            
            # Türkçe/İngilizce sözlük kontrolü
            dictionary_score = self._check_dictionary_similarity(constraints.name_hints, path_name_tokens)
            score += dictionary_score * 0.1
            total_checks += 1
            
            logger.debug(f"Rule-based skor: {score:.3f} (path: {path_name_tokens})")
            return min(score, 1.0)
            
        except Exception as e:
            logger.warning(f"Rule-based skorlama hatası: {e}")
            return 0.0
    
    def _check_type_match(self, constraint_type: str, schema_type: str) -> float:
        """Tip uyumu kontrolü"""
        # Tip mapping'leri
        type_mappings = {
            "string": ["string", "text"],
            "id": ["id", "code", "uuid"],
            "enum": ["enum"],
            "number": ["number", "amount", "quantity", "rate"],
            "date": ["date", "datetime"],
            "bool": ["boolean", "bool"]
        }
        
        constraint_lower = constraint_type.lower()
        schema_lower = schema_type.lower()
        
        # Direkt eşleşme
        if constraint_lower == schema_lower:
            return 1.0
        
        # Mapping'lerde eşleşme
        for category, types in type_mappings.items():
            if constraint_lower in types and schema_lower in types:
                return 0.8
        
        # Kısmi eşleşme
        if constraint_lower in schema_lower or schema_lower in constraint_lower:
            return 0.5
        
        return 0.0
    
    def _check_name_similarity(self, name_hints: List[str], path_tokens: List[str]) -> float:
        """İsim benzerliği kontrolü"""
        if not name_hints or not path_tokens:
            return 0.0
        
        max_score = 0.0
        
        for hint in name_hints:
            hint_tokens = hint.lower().split()
            
            for hint_token in hint_tokens:
                for path_token in path_tokens:
                    path_token_lower = path_token.lower()
                    
                    # Tam eşleşme
                    if hint_token == path_token_lower:
                        max_score = max(max_score, 1.0)
                    # Kısmi eşleşme
                    elif hint_token in path_token_lower or path_token_lower in hint_token:
                        max_score = max(max_score, 0.6)
                    # Edit distance benzerliği (basit)
                    elif self._simple_similarity(hint_token, path_token_lower) > 0.7:
                        max_score = max(max_score, 0.4)
        
        return max_score
    
    def _check_mandatory_field(self, path_tokens: List[str]) -> float:
        """Zorunlu alan kontrolü"""
        # Önemli alan anahtar kelimeleri
        important_keywords = ["id", "code", "name", "title", "type", "status"]
        
        for token in path_tokens:
            token_lower = token.lower()
            if any(keyword in token_lower for keyword in important_keywords):
                return 1.0
        
        return 0.5  # Varsayılan skor
    
    def _check_dictionary_similarity(self, name_hints: List[str], path_tokens: List[str]) -> float:
        """Sözlük benzerliği kontrolü"""
        # Türkçe-İngilizce sözlük
        dictionary = {
            "tarih": ["date", "time"],
            "vergi": ["tax", "vat"],
            "tutar": ["amount", "price", "total"],
            "kod": ["code", "number"],
            "ad": ["name", "title"],
            "açıklama": ["description", "detail"],
            "kullanıcı": ["user", "username"],
            "stok": ["stock", "product"],
            "birim": ["unit", "currency"]
        }
        
        max_score = 0.0
        
        for hint in name_hints:
            hint_lower = hint.lower()
            
            for path_token in path_tokens:
                path_token_lower = path_token.lower()
                
                # Sözlükten eşleşme ara
                for tr_word, en_words in dictionary.items():
                    if hint_lower == tr_word:
                        if any(en_word in path_token_lower for en_word in en_words):
                            max_score = max(max_score, 1.0)
                    elif any(en_word in hint_lower for en_word in en_words):
                        if tr_word in path_token_lower:
                            max_score = max(max_score, 1.0)
        
        return max_score
    
    def _simple_similarity(self, s1: str, s2: str) -> float:
        """Basit string benzerliği (Levenshtein distance tabanlı)"""
        if not s1 or not s2:
            return 0.0
        
        # Basit Jaccard benzerliği
        set1 = set(s1)
        set2 = set(s2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_best_match(self, constraints: Constraints, info: JsonSchemaInfo) -> MatchResult:
        """
        En iyi alan eşleşmesini bul (optimize edilmiş)
        
        Args:
            constraints: Kısıtlamalar
            info: JSON şema bilgisi
            
        Returns:
            En iyi eşleşme sonucu
            
        Raises:
            MatchingError: Eşleştirme hatası
        """
        try:
            logger.debug(f"En iyi eşleşme aranıyor: {constraints.name_hints}")
            
            if not info.paths:
                raise MatchingError("Eşleştirilecek alan bulunamadı")
            
            best_match = None
            best_score = -1.0
            semantic_weight = MATCH_WEIGHTS.get("semantic", 0.7)
            rules_weight = MATCH_WEIGHTS.get("rules", 0.3)
            constraint_embedding = None
            path_embeddings = None
            constraint_text = self._build_constraint_text(constraints)

            if constraint_text:
                try:
                    constraint_embedding = self.model.encode([constraint_text], convert_to_numpy=True)[0]
                    path_embeddings = self.get_field_embeddings(tuple(info.paths))
                except Exception as exc:
                    logger.warning(f"Semantic hazirlik hatasi: {exc}")
                    constraint_embedding = None
                    path_embeddings = None
            
            for index, path in enumerate(info.paths):
                try:
                    path_tokens = split_camel_case(path)
                    schema_type = info.types.get(path, "unknown")
                    rule_score = self.score_by_rules(constraints, path_tokens, schema_type)

                    semantic_score = 0.0
                    if constraint_embedding is not None and path_embeddings is not None:
                        semantic_score = self._cosine_similarity(constraint_embedding, path_embeddings[index])

                    ensemble_score = (semantic_score * semantic_weight) + (rule_score * rules_weight)
                    ensemble_score *= self._generic_path_penalty(
                        constraints,
                        path_tokens,
                        schema_type,
                        rule_score,
                    )
                    
                    logger.debug(
                        f"Path: {path}, Semantic: {semantic_score:.3f}, Rule: {rule_score:.3f}, Score: {ensemble_score:.3f}"
                    )
                    
                    if ensemble_score > best_score:
                        best_score = ensemble_score
                        best_match = MatchResult(
                            path=path,
                            score=ensemble_score,
                            rationale=f"Semantic: {semantic_score:.3f}, Rule-based: {rule_score:.3f}"
                        )
                        
                except Exception as e:
                    logger.warning(f"Path {path} değerlendirme hatası: {e}")
                    continue
            
            if best_match is None:
                raise MatchingError("Hiçbir eşleşme bulunamadı")
            
            logger.info(f"En iyi eşleşme: {best_match.path} (skor: {best_match.score:.3f})")
            return best_match
            
        except Exception as e:
            error_msg = f"Alan eşleştirme hatası: {e}"
            logger.error(error_msg)
            raise MatchingError(error_msg)
    
    def _calculate_semantic_score(self, constraints: Constraints, path: str) -> float:
        """Semantic benzerlik skoru hesapla"""
        try:
            # Constraints'ten metin oluştur
            constraint_text = " ".join(constraints.name_hints)
            if not constraint_text:
                return 0.0
            
            # Path'i normalize et
            path_words = split_camel_case(path)
            path_text = " ".join(path_words)
            
            # Embedding'leri hesapla
            constraint_emb = self.model.encode([constraint_text], convert_to_numpy=True)[0]
            path_emb = self.model.encode([path_text], convert_to_numpy=True)[0]
            
            # Kosinüs benzerliği
            similarity = np.dot(constraint_emb, path_emb) / (
                np.linalg.norm(constraint_emb) * np.linalg.norm(path_emb)
            )
            
            return max(0.0, similarity)  # Negatif değerleri 0 yap
            
        except Exception as e:
            logger.warning(f"Semantic skor hesaplama hatası: {e}")
            return 0.0

    def _build_constraint_text(self, constraints: Constraints) -> str:
        parts = list(constraints.name_hints or [])
        if constraints.source_field_tr:
            parts.append(constraints.source_field_tr)
        if constraints.source_field_en:
            parts.append(constraints.source_field_en)
        if constraints.semantic_tags:
            parts.extend(constraints.semantic_tags)
        if constraints.enum:
            parts.extend(constraints.enum[:3])
        return " ".join(part for part in parts if part)

    def _generic_path_penalty(
        self,
        constraints: Constraints,
        path_tokens: List[str],
        schema_type: str,
        rule_score: float,
    ) -> float:
        if not path_tokens:
            return 1.0

        lowered_tokens = [token.lower() for token in path_tokens if token]
        last_token = lowered_tokens[-1]
        id_like_path = last_token == "id" or last_token.endswith(".id")
        constraint_text = self._build_constraint_text(constraints).lower()
        constraint_type = (constraints.field_type or "").lower()

        if len(lowered_tokens) == 1 and last_token in GENERIC_PATH_TOKENS and rule_score < 0.2:
            return 0.15

        if id_like_path:
            if any(token in constraint_text for token in [" type", "type", "turu", "tipi", "status", "durum"]):
                return 0.15
            has_id_like_hint = any(token in constraint_text for token in ID_LIKE_HINT_TOKENS)
            if constraint_type not in {"id", "code", "uuid"} and not has_id_like_hint:
                return 0.15

        if constraint_type in {"bool", "boolean"} and schema_type not in {"bool", "boolean"}:
            return 0.15

        if last_token in {"type", "status"} and constraint_type in {"bool", "date", "number", "id"}:
            return 0.25

        if schema_type == "unknown" and rule_score < 0.15:
            return 0.35

        return 1.0

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        left_norm = np.linalg.norm(left)
        right_norm = np.linalg.norm(right)
        if left_norm == 0 or right_norm == 0:
            return 0.0
        similarity = float(np.dot(left, right) / (left_norm * right_norm))
        return max(0.0, similarity)
