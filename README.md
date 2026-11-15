# AstroCare

AstroCare is a Streamlit prototype for astronaut self-assessment during a long-duration space mission. It combines physiological, physical, mental, and environmental signals into an explainable workflow:

```text
measurement → configured thresholds → normal / watch / escalate → human review
```

AstroCare is a design and decision-support prototype. It is not a medical device, diagnostic system, or replacement for mission procedures, crew medical officers, behavioral-health support, operations control, or flight-surgeon judgment. All current readings are simulated and all ranges in `data/indicators.json` are illustrative.

## Quick start

Run these commands from the project root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Astronauts create a profile or sign in before opening the dashboard. Profiles and each astronaut's check-ins are stored locally in `data/astronauts.json`; passwords are stored as salted PBKDF2 hashes. This is a lightweight prototype store, so use synthetic data and do not deploy it for real medical records. New profiles start with an empty personal history. The local `.venv` can also be reused when it already exists:

```bash
source .venv/bin/activate
streamlit run app.py
```

## How the application works

### Startup flow

1. `app.py` configures the Streamlit page and loads `styles/theme.css`.
2. `app.py` shows sign-in or profile creation and then loads only that astronaut's saved check-ins.
3. `engine.evaluate_measurements()` evaluates available values against the configured indicator thresholds.
4. The shared sidebar and section navigation are rendered.
5. The selected section module is called through its public `render()` function.
6. The section reads the shared results and composes its page from reusable components.

### Data flow

```text
data/sample_mission.csv
          │
          ▼
      state.py ───────► st.session_state["history"]
          │             st.session_state["measurement_values"]
          ▼
      engine.py ──────► st.session_state["last_results"]
          │
          ▼
      sections/*.py ──► components/*.py ──► Streamlit UI
```

The backend remains data-driven. Sections do not calculate clinical status themselves; they display the results produced by `engine.py`.

## Project structure

```text
app.py                         # Streamlit entry point and section router
config.py                      # Paths, page configuration, indicator loading
state.py                       # Shared Streamlit session-state lifecycle

sections/
  __init__.py
  mission_overview.py       # Signed-in landing dashboard and quick navigation
  health_monitoring.py         # Readiness, body map, check-in, priority signals
  physical_wellness.py         # Exercise, strength, recovery, countermeasures
  mental_wellness.py           # Mood, stress, sleep, cognition, privacy messaging
  space_environment.py         # Cabin CO₂, radiation, telemetry coverage
  mission_support.py           # Alerts, guidance, equipment, mission support

components/
  __init__.py
  sidebar.py                   # Shared mission profile sidebar
  header.py                    # Section title and status header
  metric_cards.py              # Summary and indicator cards
  status_indicators.py         # Alerts, status labels, priority rows
  charts.py                    # Reusable Plotly history charts
  body_map.py                  # Interactive body-system selector

styles/
  theme.css                    # Global colors, typography, spacing, components

engine.py                      # Indicator evaluation, readiness, trends, history
gamification.py                # Streak, points, and badge helpers
data/indicators.json           # Indicator definitions and illustrative thresholds
data/sample_mission.csv        # Simulated 14-day mission history
requirements.txt               # Python dependencies
```

## Team ownership model

The frontend is intentionally split so team members can work in parallel.

| Area | Primary file(s) | Responsibility |
|---|---|---|
| Health Monitoring | `sections/health_monitoring.py` | Physiological dashboard, anatomy interaction, daily check-in |
| Physical Wellness | `sections/physical_wellness.py` | Exercise, strength, recovery, countermeasure views |
| Mental Wellness | `sections/mental_wellness.py` | Private mood/stress/sleep/cognition workflow |
| Space Environment | `sections/space_environment.py` | Habitat telemetry and environmental risk context |
| Mission Support | `sections/mission_support.py` | Alerts, guidance, equipment readiness, escalation context |
| Shared UI | `components/` and `styles/theme.css` | Components used by multiple sections |
| Data/evaluation | `engine.py`, `state.py`, `config.py`, `data/` | State, thresholds, history, and calculations |

Each section exposes the same interface:

```python
def render() -> None:
    """Render this dashboard section."""
```

`app.py` should remain a router and application shell. A section should not import `app.py`; this prevents circular imports and keeps section ownership clear.

## Adding or changing a section

1. Open the relevant file under `sections/`.
2. Keep data access through `st.session_state` and `config.INDICATORS`.
3. Reuse shared components before creating section-specific markup.
4. Add section-specific CSS only when the visual behavior cannot be shared. Prefer adding reusable styles to `styles/theme.css`.
5. Keep the public function as `render()` so `app.py` does not need section-specific logic.
6. Test the section through the navigation and with incomplete data if the section depends on optional indicators.

Do not copy the evaluation logic into a section. Use the already evaluated result objects:

```python
results = st.session_state["last_results"]
history = st.session_state["history"]
```

## Adding an indicator

Add a complete indicator object to `data/indicators.json`. The current schema expects:

- `id`, `label`, `short_label`, `category`, and `system`
- `unit`, `min`, `max`, `step`, and `default`
- `thresholds.normal`, `thresholds.attention`, and `thresholds.critical`
- `measure_in_space`, `why_exam`, `hazards`
- `actions` and `status_messages`

If the indicator is a history-backed measurement, add a matching column to `data/sample_mission.csv`. Then add its ID to the relevant section’s indicator list. The engine will evaluate it automatically after `config.py` reloads the indicator library.

Do not add a value merely to make a card look complete. If telemetry is not available, show an explicit unavailable state instead of fabricating a measurement.

## Session state and check-ins

The shared state keys are:

| Key | Meaning |
|---|---|
| `history` | In-memory DataFrame containing mission history |
| `measurement_values` | Latest evaluated measurement mapping |
| `last_results` | List of engine-generated result dictionaries |
| `selected_system` | Current body-map selection |
| `checkins` | Number of check-ins in the current session |
| `sleep_quality` | Mental-wellness session-only rating |

`state.save_check_in()` merges a partial update, re-evaluates available indicators, appends to the in-memory history, and saves that check-in under the signed-in astronaut in `data/astronauts.json`. The sample CSV remains demo data and is not used for signed-in astronaut dashboards.

Use bracket notation for session-state keys. For example:

```python
st.session_state["measurement_values"]
```

Avoid `st.session_state.values`: `values` is also a mapping method and can produce `TypeError: argument of type 'method' is not iterable`.

## Design system

The global visual system lives in `styles/theme.css`.

| Token | Value | Use |
|---|---|---|
| Deep Space | `#071321` | App background |
| Panel Navy | `#0D1B2A` | Main panels |
| Elevated Surface | `#14283B` | Cards and raised surfaces |
| Electric Cyan | `#42D9E8` | Primary interaction and telemetry accent |
| Mint Green | `#55E6B5` | Normal/healthy state |
| Warning Amber | `#F4BC62` | Watch state |
| Critical Red | `#F16B78` | Escalation state |
| Primary Text | `#EAF2FA` | Main readable text |

Interface text uses Inter/Manrope. Telemetry, measurements, timestamps, labels, and status values use JetBrains Mono. Glow is intentionally restrained: selected or hovered body systems, active indicators, and important alerts may receive emphasis; normal cards should remain quiet.

## Testing and verification

Compile the application modules:

```bash
./.venv/bin/python -m py_compile \
  app.py config.py state.py engine.py gamification.py \
  sections/*.py components/*.py
```

Run the Streamlit AppTest smoke check for all five routes:

```bash
./.venv/bin/python - <<'PY'
from streamlit.testing.v1 import AppTest

sections = [
    "Mission Overview",
    "Health Monitoring",
    "Physical Wellness",
    "Mental Wellness",
    "Space Environment",
]

app = AppTest.from_file("app.py", default_timeout=20).run()
assert not app.exception, app.exception
for section in sections:
    app.radio[0].set_value(section).run()
    assert not app.exception, f"{section}: {app.exception}"
print("All five sections render successfully.")
PY
```

When testing a UI change, also verify the relevant interaction: health check-in submission, body-system selection, mental-wellness input, or mission-support controls.

## Medical and data boundaries

The current demo data contains:

- Heart rate
- Systolic blood pressure
- Oxygen saturation
- Body temperature
- Sleep duration
- Hydration confidence
- Exercise minutes
- Grip strength versus personal baseline
- Mood
- Perceived stress
- Reaction time
- Cabin CO₂
- Radiation dose

Cabin temperature, humidity, pressure, oxygen, microgravity exposure, bone health, fatigue, and social-isolation telemetry are not present in the supplied data. The UI labels these as unavailable rather than inventing measurements.

Thresholds are configurable examples, not universal spaceflight clinical limits. Any operational version must use validated devices, approved mission rules, provenance and quality flags, access control, audit logging, and an approved escalation tree.

## Reference material

- [NASA: Five hazards of human spaceflight](https://www.nasa.gov/hrp/hazards/)
- [NASA: Risks of human spaceflight](https://www.nasa.gov/hrp/risks/)
- [NASA: Health and medical care](https://www.nasa.gov/reference/3-0-health-and-medical-care/)
- [NASA Human Research Roadmap: risk portfolio](https://humanresearchroadmap.nasa.gov/Risks/default.aspx)
- [NASA: Human Health and Performance on a Mission to Mars](https://www.nasa.gov/wp-content/uploads/2024/01/human-health-and-performance.pdf)
