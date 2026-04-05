from TurkishStemmer import TurkishStemmer

class FieldAnalyzer:
    def __init__(self):
        self.ner_model = None
        self.pattern_learner = None
        self.similarity_threshold = 0.7
        self.json_paths = []
        self.stemmer = TurkishStemmer()
        
    def analyze(self, field_name, json_paths, context=None):
        """Alan adı için en uygun JSON yolunu bul"""
        self.json_paths = json_paths
        candidates = []
        
        # NER ile alan tipini belirle
        if context and self.ner_model:
            field_type = self._get_field_type(field_name, context)
        else:
            field_type = None
            
        # Pattern'lerle eşleştir
        if self.pattern_learner:
            pattern_matches = self.pattern_learner.find_matches(field_name)
            if pattern_matches:  # Boş liste kontrolü ekle
                candidates.extend(pattern_matches)
        
        # Benzerlik hesapla
        for path in json_paths:
            score = self._calculate_similarity(field_name, path, field_type)
            if score > self.similarity_threshold:
                candidates.append((path, score))
                
        # En iyi eşleşmeyi döndür
        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        return None

    def _calculate_similarity(self, field_name, json_path, field_type=None):
        """Gelişmiş benzerlik hesaplama"""
        score = 0.0
        
        # Kelime benzerliği (0.4)
        field_words = set(field_name.lower().split())
        path_words = set(json_path.lower().split('.'))
        
        common_words = len(field_words.intersection(path_words))
        word_similarity = common_words / len(field_words.union(path_words))
        score += 0.4 * word_similarity
        
        # Yapısal benzerlik (0.3)
        structure_score = self._calculate_structure_similarity(field_name, json_path)
        score += 0.3 * structure_score
        
        # Semantik benzerlik (0.2)
        semantic_score = self._calculate_semantic_similarity(field_name, json_path)
        score += 0.2 * semantic_score
        
        # Alan tipi bonus (0.1)
        if field_type and field_type.lower() in json_path.lower():
            score += 0.1
            
        return score

    def _calculate_structure_similarity(self, field_name, json_path):
        """Yapısal benzerlik hesapla"""
        # Path derinliği kontrolü
        field_depth = len(field_name.split())
        path_depth = len(json_path.split('.'))
        depth_diff = abs(field_depth - path_depth)
        
        # Array indeks kontrolü
        has_array = '[' in json_path
        is_list_field = 'list' in field_name.lower()
        
        # Özel alan kontrolü
        is_special = any(x in json_path.lower() for x in ['id', 'code', 'type', 'value'])
        
        score = 1.0
        score -= 0.2 * depth_diff  # Derinlik farkı cezası
        score += 0.2 if has_array == is_list_field else 0.0  # Array uyumu bonusu
        score += 0.1 if is_special else 0.0  # Özel alan bonusu
        
        return max(0, min(score, 1.0))  # 0-1 arasında normalize et

    def _calculate_semantic_similarity(self, field_name, json_path):
        """Semantik benzerlik hesapla"""
        # Kök benzerliği
        field_roots = {self.stemmer.stem(w) for w in field_name.lower().split()}
        path_roots = {self.stemmer.stem(w) for w in json_path.lower().split('.')}
        
        # Ortak kökler
        common_roots = len(field_roots.intersection(path_roots))
        root_similarity = common_roots / len(field_roots.union(path_roots))
        
        # Anlamsal gruplar
        semantic_groups = {
            'id': ['kod', 'numara', 'no'],
            'type': ['tür', 'tip', 'çeşit'],
            'value': ['değer', 'tutar', 'miktar'],
            'description': ['açıklama', 'tanım', 'detay']
        }
        
        # Anlamsal grup eşleşmesi
        group_match = False
        for group, alternatives in semantic_groups.items():
            if (group in json_path.lower() and 
                any(alt in field_name.lower() for alt in alternatives)):
                group_match = True
                break
                
        return 0.7 * root_similarity + 0.3 * (1.0 if group_match else 0.0)

    def _get_field_type(self, field_name, context):
        """NER modeli ile alan tipini belirle"""
        if not self.ner_model:
            return None
        
        doc = self.ner_model(context)
        for ent in doc.ents:
            if field_name in ent.text:
                return ent.label_
        
        return None

    def find_matches(self, field_name):
        """Pattern'lere göre eşleşmeleri bul"""
        matches = []
        
        if field_name in self.patterns:
            for pattern, count in self.patterns[field_name]:
                if pattern.startswith("PREFIX_"):
                    prefix = pattern.split("_")[1]
                    matches.extend([(p, 0.8) for p in self.json_paths if p.lower().startswith(prefix)])
                elif pattern.startswith("SUFFIX_"):
                    suffix = pattern.split("_")[1]
                    matches.extend([(p, 0.7) for p in self.json_paths if p.lower().endswith(suffix)])
                elif pattern.startswith("TRANSFORM_"):
                    transform = pattern.split("_")[1]
                    source, target = transform.split("->")
                    matches.extend([(p, 0.6) for p in self.json_paths if target in p.lower()])
                
        return matches