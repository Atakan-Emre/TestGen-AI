from collections import Counter  # Counter'ı import et
from TurkishStemmer import TurkishStemmer  # Büyük harfle başlayan modül adı

class PatternLearner:
    def __init__(self):
        self.patterns = {}
        self.json_paths = []  # JSON yollarını sakla
        
    def learn_patterns(self, field_names, json_paths, examples):
        """Alan adları ve JSON yolları arasındaki kalıpları öğren"""
        self.json_paths = json_paths  # JSON yollarını kaydet
        
        for field in field_names:
            patterns = []
            
            # Kelime kalıpları
            field_words = field.lower().split()
            
            # Her JSON yolu için
            for path in json_paths:
                path_words = path.lower().split('.')
                
                # Ortak kalıpları bul
                common_patterns = self._find_common_patterns(field_words, path_words)
                if common_patterns:
                    patterns.extend(common_patterns)
                    
            # En sık kullanılan kalıpları sakla
            if patterns:
                self.patterns[field] = Counter(patterns).most_common(3)
                
    def _find_common_patterns(self, field_words, path_words):
        """İki kelime listesi arasındaki ortak kalıpları bul"""
        patterns = []
        
        # Prefix/suffix kalıpları
        if field_words[0] in path_words:
            patterns.append(f"PREFIX_{field_words[0]}")
        if field_words[-1] in path_words:
            patterns.append(f"SUFFIX_{field_words[-1]}")
            
        # Kelime dönüşüm kalıpları
        for fw in field_words:
            for pw in path_words:
                if self._is_transform(fw, pw):
                    patterns.append(f"TRANSFORM_{fw}->{pw}")
                    
        return patterns 

    def _is_transform(self, word1, word2):
        """İki kelime arasında dönüşüm var mı kontrol et"""
        # Basit benzerlik kontrolü
        if len(word1) < 3 or len(word2) < 3:
            return False
        
        # Prefix kontrolü
        if word1.startswith(word2) or word2.startswith(word1):
            return True
        
        # Suffix kontrolü
        if word1.endswith(word2) or word2.endswith(word1):
            return True
        
        # Levenshtein mesafesi
        distance = self._levenshtein_distance(word1, word2)
        max_len = max(len(word1), len(word2))
        
        return distance / max_len < 0.3  # Benzerlik eşiği

    def _levenshtein_distance(self, s1, s2):
        """İki string arasındaki edit mesafesini hesapla"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def find_matches(self, field_name):
        """Pattern'lere göre eşleşmeleri bul"""
        matches = []
        
        if field_name in self.patterns:
            for pattern, count in self.patterns[field_name]:
                if pattern.startswith("PREFIX_"):
                    prefix = pattern.split("_")[1]
                    matches.extend([
                        (p, 0.8) 
                        for p in self.json_paths 
                        if p.lower().startswith(prefix)
                    ])
                elif pattern.startswith("SUFFIX_"):
                    suffix = pattern.split("_")[1]
                    matches.extend([
                        (p, 0.7) 
                        for p in self.json_paths 
                        if p.lower().endswith(suffix)
                    ])
                elif pattern.startswith("TRANSFORM_"):
                    transform = pattern.split("_")[1]
                    source, target = transform.split("->")
                    matches.extend([
                        (p, 0.6) 
                        for p in self.json_paths 
                        if target in p.lower()
                    ])
                    
        # Eğer hiç pattern eşleşmesi yoksa, kelime benzerliği kontrolü yap
        if not matches and field_name:
            field_words = set(field_name.lower().split())
            for path in self.json_paths:
                path_words = set(path.lower().split('.'))
                common_words = len(field_words.intersection(path_words))
                if common_words > 0:
                    similarity = common_words / len(field_words.union(path_words))
                    if similarity > 0.3:  # Minimum benzerlik eşiği
                        matches.append((path, similarity))
                
        return matches

    def _find_nested_patterns(self, field_name, json_path):
        """Nested yapılar için pattern'leri bul"""
        patterns = []
        
        # Path'i parçalara ayır
        path_parts = json_path.split('.')
        field_parts = field_name.split()
        
        # Her seviye için pattern kontrolü
        current_path = ""
        for i, part in enumerate(path_parts):
            current_path = f"{current_path}.{part}" if current_path else part
            
            # Array indeks kontrolü
            if '[' in part:
                base_part = part.split('[')[0]
                patterns.append(f"ARRAY_{base_part}")
                
            # Her kelime için benzerlik kontrolü
            for field_word in field_parts:
                if self._is_similar(field_word, part):
                    patterns.append(f"PART_MATCH_{current_path}")
                    
            # Özel yapılar için pattern'ler
            if part.endswith('Id'):
                patterns.append("ID_FIELD")
            elif part.startswith('additional'):
                patterns.append("DYNAMIC_FIELD")
                
        return patterns

    def _is_similar(self, word1, word2):
        """İki kelime benzer mi kontrol et"""
        # Levenshtein mesafesi
        distance = self._levenshtein_distance(word1.lower(), word2.lower())
        max_len = max(len(word1), len(word2))
        
        # Kök benzerliği
        stemmer = TurkishStemmer()
        root1 = stemmer.stem(word1.lower())
        root2 = stemmer.stem(word2.lower())
        
        return (
            distance / max_len < 0.3 or  # Benzerlik eşiği
            root1 == root2 or  # Aynı kök
            word1.lower() in word2.lower() or  # Alt string
            word2.lower() in word1.lower()
        )