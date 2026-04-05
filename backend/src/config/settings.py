from pathlib import Path

# Ana dizinler
BASE_DIR = Path("/app")
DATA_DIR = BASE_DIR / "data"

# Input/Output dizinleri
INPUT_PATH = DATA_DIR / "input"
OUTPUT_PATH = DATA_DIR / "output"

# Alt dizinler
CSV_DIR = INPUT_PATH / "Csv"
JSON_DIR = INPUT_PATH / "Json"
VARIABLES_DIR = INPUT_PATH / "Variables"
TEST_SCENARIOS_DIR = OUTPUT_PATH / "test_scenarios"

# Dizinleri oluştur
for path in [CSV_DIR, JSON_DIR, VARIABLES_DIR, TEST_SCENARIOS_DIR]:
    path.mkdir(parents=True, exist_ok=True) 