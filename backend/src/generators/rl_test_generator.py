import numpy as np
from stable_baselines3 import PPO
from gymnasium import spaces

class TestCaseEnvironment:
    def __init__(self, json_structure, historical_cases):
        self.json_structure = json_structure
        self.historical_cases = historical_cases
        # Aksiyon uzayı: Her alan için olası değer tipleri
        self.action_space = spaces.Dict({
            'field_selection': spaces.Discrete(len(json_structure)),
            'value_type': spaces.Discrete(5)  # null, string, number, boolean, object
        })
        # Gözlem uzayı: Mevcut test case durumu
        self.observation_space = spaces.Dict({
            'coverage': spaces.Box(low=0, high=1, shape=(1,)),
            'success_rate': spaces.Box(low=0, high=1, shape=(1,)),
            'field_states': spaces.MultiBinary(len(json_structure))
        })
        
    def reset(self):
        self.current_test_case = {}
        self.field_states = np.zeros(len(self.json_structure))
        return self._get_observation()
        
    def step(self, action):
        # Aksiyonu uygula
        field_idx = action['field_selection']
        value_type = action['value_type']
        
        # Test case'i güncelle
        field_name = list(self.json_structure.keys())[field_idx]
        self.current_test_case[field_name] = self._generate_value(value_type)
        
        # Ödül hesapla
        reward = self._calculate_reward()
        
        # Durumu güncelle
        self.field_states[field_idx] = 1
        
        return self._get_observation(), reward, self._is_done(), {}
        
    def _calculate_reward(self):
        coverage = np.mean(self.field_states)
        success_rate = self._validate_test_case()
        return coverage * 0.5 + success_rate * 0.5 
        
    def _validate_test_case(self):
        # Test case'in geçerliliğini kontrol et
        structure_score = self._check_structure()
        consistency_score = self._check_consistency()
        coverage_score = self._check_coverage()
        
        return (
            structure_score * 0.4 + 
            consistency_score * 0.3 + 
            coverage_score * 0.3
        )
        
    def _check_consistency(self):
        # Alanlar arası tutarlılığı kontrol et
        inconsistencies = []
        for rule in self.business_rules:
            if not rule.validate(self.current_test_case):
                inconsistencies.append(rule)
        return 1.0 - (len(inconsistencies) / len(self.business_rules))