"""
backend/agents/report_agent.py

Agent 4: Report Agent
---------------------
Pure aggregation agent.  Combines the outputs of all three upstream agents:

  1. DiagnosisAgent  – crop, disease, confidence, affected_area_percent
  2. ForecastAgent   – spread_risk, risk_score, weather_summary, reason
  3. AdvisoryAgent   – priority, recommendations, prevention

No LLM, no external API calls, no I/O beyond receiving the three dicts.

Output contract (matches docs/api_contracts.md Report Agent section):
  {
      "summary":              str,          # auto-generated plain-English sentence
      "crop":                 str,
      "disease":              str,
      "confidence":           float,
      "affected_area_percent":float,
      "spread_risk":          str,
      "risk_score":           int,
      "priority":             str,
      "recommendations":      list[str],
      "prevention":           list[str],
      "weather_summary":      dict          # forwarded from ForecastAgent as-is
  }
"""

import json
import argparse
from typing import Any, Dict, List


class ReportAgent:
    """
    Report Agent that aggregates diagnosis, forecast, and advisory outputs
    into a single flat farmer-facing report dict.

    No external dependencies – all data comes from the upstream agents.

    Usage::

        agent = ReportAgent()
        report = agent.generate(
            diagnosis=diagnosis_output,
            forecast=forecast_output,
            advisory=advisory_output,
        )
    """

    # ------------------------------------------------------------------
    # Required keys for each upstream input
    # Used by the validation helpers to produce clear error messages.
    # ------------------------------------------------------------------
    _REQUIRED_DIAGNOSIS_KEYS: tuple = (
        "crop",
        "disease",
        "confidence",
        "affected_area_percent",
    )
    _REQUIRED_FORECAST_KEYS: tuple = (
        "spread_risk",
        "risk_score",
    )
    _REQUIRED_ADVISORY_KEYS: tuple = (
        "priority",
        "recommendations",
        "prevention",
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        diagnosis: Dict[str, Any],
        forecast: Dict[str, Any],
        advisory: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build and return the final farmer report.

        Args:
            diagnosis: Output of DiagnosisAgent.diagnose().
                       Required keys: crop, disease, confidence,
                       affected_area_percent.
            forecast:  Output of ForecastAgent.forecast_risk().
                       Required keys: spread_risk, risk_score.
                       Optional keys: weather_summary, reason.
            advisory:  Output of AdvisoryAgent.advise().
                       Required keys: priority, recommendations, prevention.

        Returns:
            Flat report dict matching the Report Agent output contract.

        Raises:
            ValueError: If any required key is missing from *diagnosis*,
                        *forecast*, or *advisory*.
            TypeError:  If any of the three inputs is not a dict.
        """
        # --- 1. Type-guard each upstream payload -------------------------
        self._assert_dict(diagnosis, "diagnosis")
        self._assert_dict(forecast,  "forecast")
        self._assert_dict(advisory,  "advisory")

        # --- 2. Validate required keys -----------------------------------
        self._validate_keys(diagnosis, self._REQUIRED_DIAGNOSIS_KEYS, "diagnosis")
        self._validate_keys(forecast,  self._REQUIRED_FORECAST_KEYS,  "forecast")
        self._validate_keys(advisory,  self._REQUIRED_ADVISORY_KEYS,  "advisory")

        # --- 3. Extract fields from each upstream payload ----------------

        # Diagnosis fields
        crop: str                  = diagnosis["crop"]
        disease: str               = diagnosis["disease"]
        confidence: float          = float(diagnosis["confidence"])
        affected_area: float       = float(diagnosis["affected_area_percent"])

        # Forecast fields
        spread_risk: str           = forecast["spread_risk"]
        risk_score: int            = int(forecast["risk_score"])
        # weather_summary may be a nested dict or a plain string depending on
        # whether the ForecastAgent ran in live mode or was mocked; preserve
        # whatever shape was returned.
        weather_summary: Any       = forecast.get("weather_summary", {})

        # Advisory fields
        priority: str              = advisory["priority"]
        recommendations: List[str] = list(advisory.get("recommendations", []))
        prevention: List[str]      = list(advisory.get("prevention", []))

        # --- 4. Generate a human-readable summary sentence ---------------
        # Deterministic template; no LLM required.
        summary: str = self._build_summary(
            crop=crop,
            disease=disease,
            confidence=confidence,
            affected_area=affected_area,
            spread_risk=spread_risk,
            priority=priority,
        )

        # --- 5. Assemble and return the flat report dict -----------------
        return {
            "summary":               summary,
            "crop":                  crop,
            "disease":               disease,
            "confidence":            confidence,
            "affected_area_percent": affected_area,
            "spread_risk":           spread_risk,
            "risk_score":            risk_score,
            "priority":              priority,
            "recommendations":       recommendations,
            "prevention":            prevention,
            "weather_summary":       weather_summary,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_dict(value: Any, label: str) -> None:
        """
        Raise a TypeError if *value* is not a dict.

        Args:
            value: The object to check.
            label: Human-readable name used in the error message.

        Raises:
            TypeError: If *value* is not a dict.
        """
        if not isinstance(value, dict):
            raise TypeError(
                f"'{label}' must be a dict, got {type(value).__name__!r}."
            )

    @staticmethod
    def _validate_keys(
        data: Dict[str, Any],
        required: tuple,
        label: str,
    ) -> None:
        """
        Check that every key in *required* is present in *data*.

        Args:
            data:     The dict to inspect.
            required: Tuple of key names that must be present.
            label:    Human-readable name for the dict (used in errors).

        Raises:
            ValueError: If any required key is absent.
        """
        for key in required:
            if key not in data:
                raise ValueError(
                    f"Missing required '{label}' key: '{key}'. "
                    f"'{label}' must contain: {list(required)}"
                )

    @staticmethod
    def _build_summary(
        crop: str,
        disease: str,
        confidence: float,
        affected_area: float,
        spread_risk: str,
        priority: str,
    ) -> str:
        """
        Compose a concise plain-English summary sentence for the farmer.

        The sentence is fully deterministic — no LLM or template engine is
        used.  The format is kept short so it can be displayed as a headline
        in a PDF or dashboard widget.

        Args:
            crop:          Detected crop name.
            disease:       Detected disease name.
            confidence:    Model confidence percentage.
            affected_area: Affected leaf area percentage.
            spread_risk:   Forecast spread risk level.
            priority:      Advisory priority label.

        Returns:
            Single-sentence summary string.
        """
        # Healthy crops get a shorter, positive message.
        if disease.lower() == "healthy":
            return (
                f"{crop} plant appears healthy (confidence: {confidence:.1f}%). "
                f"No immediate action required."
            )

        return (
            f"{crop} plant diagnosed with {disease} "
            f"(confidence: {confidence:.1f}%, "
            f"affected area: {affected_area:.1f}%). "
            f"Spread risk is {spread_risk}. "
            f"Recommended action: {priority}."
        )


# ---------------------------------------------------------------------------
# CLI entry point – mirrors the pattern used across all other agents
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Report Agent to aggregate agent outputs into a farmer report."
    )
    parser.add_argument(
        "--diagnosis",
        type=str,
        required=True,
        help="Diagnosis JSON string from DiagnosisAgent.",
    )
    parser.add_argument(
        "--forecast",
        type=str,
        required=True,
        help="Forecast JSON string from ForecastAgent.",
    )
    parser.add_argument(
        "--advisory",
        type=str,
        required=True,
        help="Advisory JSON string from AdvisoryAgent.",
    )
    args = parser.parse_args()

    try:
        diagnosis: Dict[str, Any] = json.loads(args.diagnosis)
        forecast: Dict[str, Any]  = json.loads(args.forecast)
        advisory: Dict[str, Any]  = json.loads(args.advisory)

        agent = ReportAgent()
        result = agent.generate(
            diagnosis=diagnosis,
            forecast=forecast,
            advisory=advisory,
        )
        print(json.dumps(result, indent=2))

    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2))


if __name__ == "__main__":
    main()
