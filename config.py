"""Application configuration and data-library loading for AstroCare."""

from __future__ import annotations

from pathlib import Path

from engine import load_indicators


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
INDICATORS_PATH = DATA_DIR / "indicators.json"
SAMPLE_HISTORY_PATH = DATA_DIR / "sample_mission.csv"
ASTRONAUT_DATA_PATH = DATA_DIR / "astronauts.json"
THEME_PATH = ROOT / "styles" / "theme.css"

APP_TITLE = "AstroCare · Crew Health Command"
APP_ICON = "✦"
SECTION_ORDER = [
    "Health Monitoring",
    "Physical Wellness",
    "Mental Wellness",
    "Space Environment",
    "Mission Support",
]

SECTION_SUBTITLES = {
    "Health Monitoring": "A fast, explainable view of physiology and readiness during the mission.",
    "Physical Wellness": "Track countermeasures, recovery, and the physical effects of altered gravity.",
    "Mental Wellness": "A private, human-centered check on mood, stress, sleep, and cognition.",
    "Space Environment": "Watch the habitat signals that shape crew health and performance.",
    "Mission Support": "Find the next approved action, escalation path, and ground-support link.",
}

# The JSON library remains the source of truth for indicator definitions and thresholds.
INDICATORS = load_indicators(INDICATORS_PATH)

