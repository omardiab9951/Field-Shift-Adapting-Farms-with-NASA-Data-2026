from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data" / "processed"
MANIFEST_PATH = BACKEND_DIR / "data" / "manifest.json"

HOST = "127.0.0.1"
PORT = 8000
ALLOWED_ORIGINS = (
    "null",  # Browser origin when index.html is opened directly from Finder.
    "http://127.0.0.1:8080",
    "http://localhost:8080",
)

SCORING_METHOD = (
    "Weighted arithmetic mean of the notebook's published normalized components: "
    "(land_weight*s_land + water_weight*s_water + practice_weight*s_practice) "
    "/ (land_weight + water_weight + practice_weight). Water is not renormalized "
    "per cell. Default notebook analysis uses equal weights; its water alternative "
    "uses land and water weights 1,1,0."
)

LIMITATIONS = [
    "Rice net irrigation excludes additional seepage losses.",
    "Sugarbeet uses the notebook's special suitability treatment: the summer crop "
    "determines land suitability for sugarbeet rotations.",
    "Some source suitability and irrigation values were median-filled and are flagged.",
    "Local practice reflects area-level 2020 crop statistics, not a farmer's current rotation.",
    "Scores are comparative, not probabilities or guaranteed yields.",
    "The method does not check detailed calendar feasibility, profit, or agronomic rotation rules.",
    "Spatial detail follows the coarser source layers; results are not field-level measurements.",
]
