"""
frontend/app.py

AgriAgents – Streamlit Frontend
---------------------------------
One-page interface that orchestrates the full multi-agent pipeline:

    DiagnosisAgent → ForecastAgent → AdvisoryAgent → ReportAgent

User Inputs
-----------
  • Leaf image  (required – jpg / jpeg / png, max 10 MB)
  • Crop name   (optional)
  • Location    (optional – used by ForecastAgent for weather data)

Display Sections
----------------
  1. Diagnosis   – crop, disease, confidence, affected area %
  2. Forecast    – spread risk, risk score, weather summary
  3. Advisory    – priority, recommendations, prevention
  4. Report      – summary sentence + full consolidated report

Constraints (from PROJECT_RULES.md / AGRIAGENTS_ARCHITECTURE.md)
-----------------------------------------------------------------
  • No LLM calls in the frontend.
  • No database.
  • No authentication.
  • File types: jpg, jpeg, png  |  Max size: 10 MB
  • All API keys live in .env (handled by the backend agents, not here).
"""

import os
import sys
import tempfile
from typing import Any, Dict, List, Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so all backend imports resolve
# correctly when Streamlit is launched from any working directory.
# ---------------------------------------------------------------------------
_PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import agents after the path is patched
from backend.agents.diagnosis_agent import DiagnosisAgent
from backend.agents.forecast_agent import ForecastAgent
from backend.agents.advisory_agent import AdvisoryAgent
from backend.agents.report_agent import ReportAgent


# ---------------------------------------------------------------------------
# Constants (match AGRIAGENTS_ARCHITECTURE.md security requirements)
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS: tuple = ("jpg", "jpeg", "png")
MAX_FILE_SIZE_MB: int = 10
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024


# ---------------------------------------------------------------------------
# Page configuration – must be the first Streamlit call in the script
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AgriAgents – Crop Disease Analyzer",
    page_icon="🌱",
    layout="centered",
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _validate_image(uploaded_file: Any) -> Optional[str]:
    """
    Validate the uploaded file for type and size.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        An error message string if invalid, or None if the file is acceptable.
    """
    # Check file extension (case-insensitive)
    extension: str = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return (
            f"Unsupported file type: **.{extension}**. "
            f"Please upload a JPG, JPEG, or PNG image."
        )

    # Check file size
    file_bytes: bytes = uploaded_file.getvalue()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb: float = len(file_bytes) / (1024 * 1024)
        return (
            f"File is too large ({size_mb:.1f} MB). "
            f"Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    return None  # File is valid


def _save_uploaded_file(uploaded_file: Any) -> str:
    """
    Write the uploaded file to a temporary path on disk.

    The file is saved to the system temp directory with its original
    extension preserved so that OpenCV and PIL can infer the format.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Absolute path to the saved temporary file.
    """
    extension: str = uploaded_file.name.rsplit(".", 1)[-1].lower()
    # NamedTemporaryFile with delete=False so the path remains accessible
    # after the context manager closes.
    with tempfile.NamedTemporaryFile(
        suffix=f".{extension}", delete=False
    ) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def _risk_color(spread_risk: str) -> str:
    """
    Map a spread risk label to a Streamlit status emoji prefix for display.

    Args:
        spread_risk: One of "Low", "Medium", "High".

    Returns:
        Emoji string prefix.
    """
    mapping: Dict[str, str] = {
        "Low":    "🟢",
        "Medium": "🟡",
        "High":   "🔴",
    }
    return mapping.get(spread_risk, "⚪")


def _priority_icon(priority: str) -> str:
    """
    Map an advisory priority label to an emoji for display.

    Args:
        priority: One of "Immediate Action", "Monitor Closely", "Preventive Care".

    Returns:
        Emoji string prefix.
    """
    mapping: Dict[str, str] = {
        "Immediate Action": "🚨",
        "Monitor Closely":  "⚠️",
        "Preventive Care":  "✅",
    }
    return mapping.get(priority, "ℹ️")


def _display_bullet_list(items: List[str], empty_message: str = "None listed.") -> None:
    """
    Render a list of strings as Streamlit bullet points.

    Args:
        items:         List of text items to display.
        empty_message: Fallback text when the list is empty.
    """
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.markdown(f"_{empty_message}_")


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _load_diagnosis_agent() -> DiagnosisAgent:
    """
    Load DiagnosisAgent once per Streamlit session (cached by st.cache_resource).

    Caching prevents the EfficientNet model weights from being loaded on
    every button click, which would make each analysis take 10+ seconds.

    Returns:
        Initialised DiagnosisAgent instance.
    """
    return DiagnosisAgent()


def run_pipeline(
    image_path: str,
    location: str,
) -> Dict[str, Any]:
    """
    Execute the full AgriAgents multi-agent pipeline in sequence.

    Steps:
      1. DiagnosisAgent.diagnose()
      2. ForecastAgent.forecast_risk()
      3. AdvisoryAgent.advise()
      4. ReportAgent.generate()

    Args:
        image_path: Absolute path to the saved leaf image on disk.
        location:   City name string for weather lookup (may be empty).

    Returns:
        Report dict from ReportAgent.generate().

    Raises:
        Exception: Propagates any agent-level exception so the caller can
                   display a user-friendly error message.
    """
    # --- Step 1: Diagnosis ------------------------------------------------
    diagnosis_agent: DiagnosisAgent = _load_diagnosis_agent()
    diagnosis: Dict[str, Any] = diagnosis_agent.diagnose(image_path)

    # --- Step 2: Forecast -------------------------------------------------
    # ForecastAgent requires a 'location' field; fall back to a default
    # city if the user did not provide one so the weather API doesn't fail.
    forecast_input: Dict[str, Any] = {
        **diagnosis,
        "location": location if location.strip() else "New Delhi",
    }
    forecast_agent: ForecastAgent = ForecastAgent()
    forecast: Dict[str, Any] = forecast_agent.forecast_risk(forecast_input)

    # --- Step 3: Advisory -------------------------------------------------
    advisory_agent: AdvisoryAgent = AdvisoryAgent()
    advisory: Dict[str, Any] = advisory_agent.advise(
        diagnosis=diagnosis,
        forecast=forecast,
    )

    # --- Step 4: Report ---------------------------------------------------
    report_agent: ReportAgent = ReportAgent()
    report: Dict[str, Any] = report_agent.generate(
        diagnosis=diagnosis,
        forecast=forecast,
        advisory=advisory,
    )

    return report


# ---------------------------------------------------------------------------
# UI – Header
# ---------------------------------------------------------------------------

st.title("🌱 AgriAgents")
st.markdown(
    "**AI-powered crop disease diagnosis and recommendation system.** "
    "Upload a leaf image to get a complete analysis including disease detection, "
    "spread risk forecast, and actionable recommendations."
)
st.divider()


# ---------------------------------------------------------------------------
# UI – Input Form
# ---------------------------------------------------------------------------

st.subheader("📷 Upload & Settings")

uploaded_file = st.file_uploader(
    label="Leaf Image (required)",
    type=list(ALLOWED_EXTENSIONS),
    help=f"Accepted formats: JPG, JPEG, PNG  |  Maximum size: {MAX_FILE_SIZE_MB} MB",
)

col_crop, col_loc = st.columns(2)

with col_crop:
    # Optional: the crop name field is informational for the farmer;
    # the model determines the actual crop from the image.
    crop_name: str = st.text_input(
        label="Crop Name (optional)",
        placeholder="e.g. Tomato, Potato, Corn",
        help="If provided, used for display only. The model detects the crop automatically.",
    )

with col_loc:
    location: str = st.text_input(
        label="Location (optional)",
        placeholder="e.g. Ahmedabad, Mumbai",
        help="City name used to retrieve live weather data for spread risk forecast. "
             "Defaults to New Delhi if left blank.",
    )

analyze_btn: bool = st.button("🔍 Analyze", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# UI – Analysis pipeline (runs only when the button is clicked)
# ---------------------------------------------------------------------------

if analyze_btn:
    # Guard: require an image to be uploaded
    if uploaded_file is None:
        st.warning("⚠️ Please upload a leaf image before clicking Analyze.")
        st.stop()

    # Validate the uploaded file (type + size)
    validation_error: Optional[str] = _validate_image(uploaded_file)
    if validation_error:
        st.error(f"❌ {validation_error}")
        st.stop()

    # Show the uploaded image in the sidebar for reference
    with st.sidebar:
        st.subheader("Uploaded Image")
        st.image(uploaded_file, use_container_width=True, caption=uploaded_file.name)

    # Save to disk so the agents (which expect a file path) can access it
    tmp_path: str = _save_uploaded_file(uploaded_file)

    try:
        # Run the full 4-agent pipeline with a spinner
        with st.spinner("🌿 Analyzing crop image — this may take a few seconds…"):
            report: Dict[str, Any] = run_pipeline(
                image_path=tmp_path,
                location=location,
            )

    except FileNotFoundError as exc:
        # Temporary file cleanup failure or model weights missing
        st.error(f"❌ File error: {exc}")
        st.stop()
    except ValueError as exc:
        # Invalid input detected by one of the agents
        st.error(f"❌ Input error: {exc}")
        st.stop()
    except Exception as exc:
        # Any other unexpected failure (network error, model error, etc.)
        st.error(
            f"❌ An unexpected error occurred during analysis:\n\n`{exc}`\n\n"
            "Please verify that:\n"
            "- The image is a clear photo of a crop leaf.\n"
            "- The location name is a valid city.\n"
            "- The model weights are present at `model/best_model.pth`."
        )
        st.stop()
    finally:
        # Always clean up the temporary file, whether analysis succeeded or not
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # -----------------------------------------------------------------------
    # Results – Report Summary Banner
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader("📋 Report Summary")
    st.info(report.get("summary", "Analysis complete."))

    # -----------------------------------------------------------------------
    # Results – Three columns: Diagnosis | Forecast | Advisory
    # -----------------------------------------------------------------------
    col_diag, col_fore, col_adv = st.columns(3)

    # --- Diagnosis ----------------------------------------------------------
    with col_diag:
        st.markdown("### 🔬 Diagnosis")

        detected_crop: str = report.get("crop", "—")
        detected_disease: str = report.get("disease", "—")
        confidence: float = report.get("confidence", 0.0)
        affected_area: float = report.get("affected_area_percent", 0.0)

        st.metric(label="Crop",    value=detected_crop)
        st.metric(label="Disease", value=detected_disease)
        st.metric(label="Confidence score",    value=f"{confidence:.0f}%")
        st.metric(label="Estimated Affected Area", value=f"{affected_area:.0f}%")

    # --- Forecast -----------------------------------------------------------
    with col_fore:
        st.markdown("### 🌦️ Forecast")

        spread_risk: str = report.get("spread_risk", "—")
        risk_score: int  = report.get("risk_score", 0)
        weather: Any     = report.get("weather_summary", {})

        risk_icon: str = _risk_color(spread_risk)
        st.metric(label="Spread Risk",  value=f"{risk_icon} {spread_risk}")
        st.metric(label="Risk Score",   value=f"{risk_score} / 100")

        # Weather summary (may be a dict or a string depending on the forecast)
        if isinstance(weather, dict) and weather:
            st.markdown("**Current Weather:**")
            temp: Any = weather.get("temperature", "—")
            hum:  Any = weather.get("humidity", "—")
            rain: Any = weather.get("rain_probability", "—")
            st.markdown(
                f"Temperature: {temp}°C\nHumidity: {hum}%\nRain Chance: {rain}%"
            )
        elif isinstance(weather, str) and weather:
            st.markdown(f"**Weather:** {weather}")

    # --- Advisory -----------------------------------------------------------
    with col_adv:
        st.markdown("### 💡 Advisory")

        priority: str = report.get("priority", "—")
        priority_icon: str = _priority_icon(priority)
        st.metric(label="Priority", value=f"{priority_icon} {priority}")

    # -----------------------------------------------------------------------
    # Results – Recommendations & Prevention (full-width, below the columns)
    # -----------------------------------------------------------------------
    st.divider()

    rec_col, prev_col = st.columns(2)

    with rec_col:
        st.markdown("#### ✅ Recommendations")
        _display_bullet_list(
            report.get("recommendations", []),
            empty_message="No specific recommendations.",
        )

    with prev_col:
        st.markdown("#### 🛡️ Prevention")
        _display_bullet_list(
            report.get("prevention", []),
            empty_message="No specific prevention steps.",
        )

    st.divider()
    st.caption(
        "AgriAgents v1.0"
        "Powered by PyTorch • OpenCV • Streamlit • Open-Meteo"
        "Dataset: PlantVillage"
        "This application provides AI-assisted crop disease diagnosis and decision support. Recommendations should be validated by an agricultural professional before taking critical actions."
    )
