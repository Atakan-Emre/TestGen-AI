import numpy as np

class ValueGenerationEnvironment:
    def __init__(self, field_type, constraints, historical_data):
        self.field_type = field_type
        self.constraints = constraints
        self.historical_data = historical_data
        
    def _generate_value(self, action):
        if self.field_type == "date":
            return self._generate_date_value(action)
        elif self.field_type == "numeric":
            return self._generate_numeric_value(action)
        elif self.field_type == "string":
            return self._generate_string_value(action)
            
    def _calculate_coverage(self, value):
        # Değerin test coverage'ına katkısını hesapla
        similar_values = [
            v for v in self.historical_data 
            if self._is_similar(v, value)
        ]
        return 1.0 - (len(similar_values) / len(self.historical_data))
        
    def step(self, action):
        generated_value = self._generate_value(action)
        validation_score = self._validate_value(generated_value)
        coverage_score = self._calculate_coverage(generated_value)
        
        reward = validation_score * 0.7 + coverage_score * 0.3
        return self._get_observation(), reward, False, {}
        
    def _validate_value(self, value):
        # Değerin kısıtlamalara uygunluğunu kontrol et
        constraint_scores = []
        for constraint in self.constraints:
            score = constraint.validate(value)
            constraint_scores.append(score)
        return np.mean(constraint_scores) 