from typing import Callable, Optional

from app.services.scenario_intelligence import ScenarioIntelligenceService


class BertNerGenerator:
    """
    Geriye donuk isim korunur.
    Uretim artik gercek NLP hibrit katmani uzerinden yapilir:
    - CSV alan semantigi
    - embedding tabanli tip/tag cikarma
    - opsiyonel BERT NER entity extraction
    - yapilandirilmis scenario bundle sidecar kaydi
    """

    def __init__(self, progress_callback: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None):
        self.service = ScenarioIntelligenceService(progress_callback=progress_callback)
        self.last_bundle = None
        self.last_scenario_path = None

    def generate_scenarios(
        self,
        input_file,
        scenario_name=None,
        generator_type="nlp_hybrid",
        progress_callback: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None,
    ):
        bundle, scenario_path = self.service.generate_bundle(
            input_file=input_file,
            scenario_name=scenario_name,
            generator_type=generator_type,
            progress_callback=progress_callback,
        )
        self.last_bundle = bundle
        self.last_scenario_path = scenario_path
        generated_lines = []
        for field in bundle.fields:
            generated_lines.extend(field.scenario_lines)
        return generated_lines
