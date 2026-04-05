from functools import lru_cache

from sentence_transformers import SentenceTransformer
from transformers import pipeline

from app.shared.settings import EMB_MODEL_NAME


@lru_cache(maxsize=1)
def get_sentence_model() -> SentenceTransformer:
    return SentenceTransformer(EMB_MODEL_NAME)


@lru_cache(maxsize=1)
def get_ner_pipeline():
    return pipeline(
        "ner",
        model="dbmdz/bert-large-cased-finetuned-conll03-english",
        aggregation_strategy="simple",
    )
