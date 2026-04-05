from stable_baselines3 import DQN
import torch.nn as nn

class FieldMatchingEnvironment:
    def __init__(self, json_structure, scenario_texts):
        self.json_structure = json_structure
        self.scenario_texts = scenario_texts
        self.observation_space = spaces.Box(
            low=-1, high=1, 
            shape=(768,)  # BERT embedding size
        )
        
    def _get_observation(self):
        # Senaryo metninin BERT embeddingi
        scenario_embedding = self.sentence_model.encode(
            self.current_scenario,
            normalize_embeddings=True
        )
        return scenario_embedding
        
    def _calculate_match_score(self, field_name):
        # Alan adı ve senaryo metni arasındaki semantic benzerlik
        field_parts = self._split_camel_case(field_name)
        field_context = " ".join(field_parts)
        
        # Türkçe ve İngilizce benzerlik skorlarını hesapla
        tr_score = self.nlp_tr(field_context).similarity(
            self.nlp_tr(self.current_scenario)
        )
        en_score = self.nlp_en(field_context).similarity(
            self.nlp_en(self.current_scenario)
        )
        
        return max(tr_score, en_score)