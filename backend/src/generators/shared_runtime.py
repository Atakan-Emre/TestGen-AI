import os
import warnings
from functools import lru_cache

import spacy
import spacy_transformers
from stable_baselines3 import DQN, PPO
from app.services.nlp_runtime import get_ner_pipeline, get_sentence_model


def _build_nlp():
    nlp = spacy.blank("xx")
    nlp.add_pipe("sentencizer")
    config = {
        "model": {
            "@architectures": "spacy-transformers.TransformerModel.v3",
            "name": "bert-base-multilingual-cased",
            "tokenizer_config": {"use_fast": True},
        }
    }
    nlp.add_pipe("transformer", config=config)
    nlp.add_pipe("ner")
    return nlp


def _load_rl_model(loader, base_path: str):
    zip_path = f"{base_path}.zip"
    if not os.path.exists(zip_path):
        return None
    return loader.load(base_path)


@lru_cache(maxsize=1)
def get_base_runtime():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        return {
            "nlp": _build_nlp(),
            "sentence_model": get_sentence_model(),
            "field_matcher": _load_rl_model(DQN, "models/field_matcher"),
            "value_generator": _load_rl_model(PPO, "models/test_generator"),
        }


@lru_cache(maxsize=1)
def get_legacy_test_runtime():
    runtime = dict(get_base_runtime())
    runtime["ner"] = get_ner_pipeline()
    return runtime
