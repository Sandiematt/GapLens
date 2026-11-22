"""Every constant used across GapLens lives here."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "gaplens.db"

# --- Grading components -----------------------------------------------------
# Component key -> maximum score of that component.
COMPONENTS = {"CIA-1": 25, "CIA-2": 50, "CIA-3": 25, "ESE": 100}
CIA_COMPONENTS = ("CIA-1", "CIA-2", "CIA-3")
CIA_TOTAL_MAX = sum(COMPONENTS[c] for c in CIA_COMPONENTS)  # 100
DEFAULT_CIA_WEIGHT = 0.5
ESE_PASS_MARK = 40

# --- Detection thresholds ---------------------------------------------------
GAP_POINTS = 25  # concept gap: student share this many points below class avg
SILLY_CLASS_FRACTION = 0.70  # >= 70% of the class ...
SILLY_CLASS_SHARE = 0.60  # ... scored >= 60% of the question's marks
SILLY_STUDENT_SHARE = 0.40  # while the student scored under 40%
TIME_PRESSURE_DROP = 20  # last third this many points below the rest
TIME_PRESSURE_EXCESS = 15  # and this much bigger than the class's drop
TIME_PRESSURE_MIN_QUESTIONS = 3

# --- Goals, warnings and weak topics ----------------------------------------
STRETCH_MARGIN = 15
EARLY_WARNING_CIA_PCT = 40
TOP_WEAK_TOPICS = 3
BIG_GAP_PCT = 50

# --- Demo data ----------------------------------------------------------------
DEMO_FACULTY_NAME = "Dr. Demo Faculty"
DEMO_CLASS = "MCA-A"
DEMO_STUDENT_ROLL = "25MCA007"
DEMO_STUDENT_NAME = "Demo Student"
DEMO_STUDENT_COUNT = 40
DEMO_ROLL_PREFIX = "25MCA"
TARGET_CHOICES = tuple(range(60, 95, 5))  # 60, 65, ... 90
TARGET_MIN, TARGET_MAX = 0, 100

ROLES = ("Student", "Faculty")
APP_NAME = "GapLens"
APP_TAGLINE = "CHRIST Smart Marks Coach"

# --- Gemini (optional, free-tier key) ------------------------------------------
GEMINI_DEFAULT_MODEL = "gemini-flash-latest"  # tried first when no model is configured
GEMINI_MAX_CANDIDATES = 3  # models tried at most, moving on only on "not found"
GEMINI_TIMEOUT_S = 60
GEMINI_TEMPERATURE = 0.2
GEMINI_SCRIPT_WARN_MB = 15  # inline uploads near Gemini's ~20 MB request limit may fail
