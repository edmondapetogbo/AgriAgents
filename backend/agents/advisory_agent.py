"""
backend/agents/advisory_agent.py

Agent 3: Advisory Agent
-----------------------
Generates crop-disease recommendations, prevention strategies, and a
priority label by combining:

  1. Diagnosis output   – crop, disease, confidence, affected_area_percent
  2. Forecast output    – spread_risk, risk_score
  3. Knowledge Base     – diseases.json via KnowledgeBaseTool

No LLM is used.  All logic is deterministic and rule-based.

Priority rules (applied in descending severity order):
  • spread_risk == "High" AND affected_area_percent > 40  → "Immediate Action"
  • spread_risk == "High"                                 → "Immediate Action"
  • spread_risk == "Medium"                               → "Monitor Closely"
  • spread_risk == "Low"  (or "Healthy" disease)          → "Preventive Care"

Output contract (matches docs/api_contracts.md Advisory Agent section):
  {
      "crop":            str,
      "disease":         str,
      "spread_risk":     str,
      "recommendations": list[str],
      "prevention":      list[str],
      "priority":        str
  }
"""

import json
import argparse
from typing import Any, Dict, List

from backend.mcp.knowledge_base_tool import KnowledgeBaseTool


# ---------------------------------------------------------------------------
# Priority constants – single source of truth for the rule engine
# ---------------------------------------------------------------------------
PRIORITY_IMMEDIATE = "Immediate Action"
PRIORITY_MONITOR   = "Monitor Closely"
PRIORITY_PREVENTIVE = "Preventive Care"

# Threshold used in the High-risk + large-area rule
HIGH_RISK_AREA_THRESHOLD: float = 40.0


class AdvisoryAgent:
    """
    Advisory Agent that uses deterministic, rule-based logic to produce
    actionable farming recommendations from diagnosis and forecast data.

    Usage::

        agent = AdvisoryAgent()
        advisory = agent.advise(diagnosis=diag_output, forecast=forecast_output)
    """

    def __init__(self) -> None:
        """
        Initialise the Advisory Agent and eagerly load the knowledge base.

        Raises:
            FileNotFoundError: If knowledge_base/diseases.json is missing.
            ValueError:        If diseases.json is malformed JSON.
        """
        # Load the knowledge base once at construction time.
        # KnowledgeBaseTool caches the JSON internally, so repeated
        # AdvisoryAgent instantiations in the same process incur no I/O.
        self._kb = KnowledgeBaseTool()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def advise(
        self,
        diagnosis: Dict[str, Any],
        forecast: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate the advisory report from upstream agent outputs.

        Args:
            diagnosis: Output dict from DiagnosisAgent.diagnose(), must contain:
                       - "crop"                 (str)
                       - "disease"              (str)
                       - "confidence"           (float)
                       - "affected_area_percent" (float)
            forecast:  Output dict from ForecastAgent.forecast_risk(), must contain:
                       - "spread_risk"  (str)  – "Low" | "Medium" | "High"
                       - "risk_score"   (int)

        Returns:
            Dict matching the Advisory Agent output contract::

                {
                    "crop":            str,
                    "disease":         str,
                    "spread_risk":     str,
                    "recommendations": list[str],
                    "prevention":      list[str],
                    "priority":        str
                }

        Raises:
            ValueError: If required keys are absent from *diagnosis* or *forecast*.
            KeyError:   If the knowledge base returns an error for the given crop/disease.
        """
        # --- 1. Validate inputs -------------------------------------------
        self._validate_diagnosis(diagnosis)
        self._validate_forecast(forecast)

        crop: str              = diagnosis["crop"]
        disease: str           = diagnosis["disease"]
        affected_area: float   = float(diagnosis["affected_area_percent"])
        spread_risk: str       = forecast["spread_risk"]

        # --- 2. Query the Knowledge Base for disease information ----------
        kb_result: Dict[str, Any] = self._kb.get_disease_info(
            crop=crop,
            disease=disease,
        )

        # KnowledgeBaseTool returns a structured error dict (not an exception)
        # when crop or disease is unknown.  Propagate this clearly.
        if "error" in kb_result:
            raise KeyError(
                f"Knowledge base lookup failed: {kb_result.get('message', kb_result)}"
            )

        recommendations: List[str] = list(kb_result.get("recommendations", []))
        prevention: List[str]      = list(kb_result.get("prevention", []))

        # --- 3. Determine priority using deterministic rules ---------------
        priority: str = self._determine_priority(
            spread_risk=spread_risk,
            affected_area=affected_area,
            disease=disease,
        )

        # --- 4. Augment recommendations based on risk context --------------
        # Append risk-contextual advice so the farmer gets actionable
        # guidance even when the KB entry is minimal.
        recommendations = self._augment_recommendations(
            base=recommendations,
            spread_risk=spread_risk,
            affected_area=affected_area,
            priority=priority,
        )

        # --- 5. Build and return output dict ------------------------------
        return {
            "crop":            crop,
            "disease":         disease,
            "spread_risk":     spread_risk,
            "recommendations": recommendations,
            "prevention":      prevention,
            "priority":        priority,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_diagnosis(diagnosis: Dict[str, Any]) -> None:
        """
        Check that all mandatory diagnosis keys are present and non-empty.

        Args:
            diagnosis: Dict to validate.

        Raises:
            ValueError: On any missing or empty required key.
        """
        required = ("crop", "disease", "affected_area_percent")
        for key in required:
            if key not in diagnosis:
                raise ValueError(
                    f"Missing required diagnosis key: '{key}'. "
                    f"Diagnosis must contain: {list(required)}"
                )
        # Ensure numeric field is actually a number
        try:
            float(diagnosis["affected_area_percent"])
        except (TypeError, ValueError):
            raise ValueError(
                "'affected_area_percent' must be a numeric value, "
                f"got: {diagnosis['affected_area_percent']!r}"
            )

    @staticmethod
    def _validate_forecast(forecast: Dict[str, Any]) -> None:
        """
        Check that all mandatory forecast keys are present.

        Args:
            forecast: Dict to validate.

        Raises:
            ValueError: On any missing required key.
        """
        required = ("spread_risk", "risk_score")
        for key in required:
            if key not in forecast:
                raise ValueError(
                    f"Missing required forecast key: '{key}'. "
                    f"Forecast must contain: {list(required)}"
                )

        valid_risks = {"Low", "Medium", "High"}
        if forecast["spread_risk"] not in valid_risks:
            raise ValueError(
                f"'spread_risk' must be one of {valid_risks}, "
                f"got: {forecast['spread_risk']!r}"
            )

    @staticmethod
    def _determine_priority(
        spread_risk: str,
        affected_area: float,
        disease: str,
    ) -> str:
        """
        Apply the priority rule engine and return the appropriate label.

        Rules (evaluated top-to-bottom, first match wins):
          1. disease == "Healthy"                                → Preventive Care
          2. spread_risk == "High" AND affected_area > threshold → Immediate Action
          3. spread_risk == "High"                               → Immediate Action
          4. spread_risk == "Medium"                             → Monitor Closely
          5. spread_risk == "Low"  (default)                     → Preventive Care

        Args:
            spread_risk:   Risk level string from ForecastAgent.
            affected_area: Percentage of affected leaf area.
            disease:       Detected disease name.

        Returns:
            Priority label string.
        """
        # Rule 1 – Healthy crops always get preventive care only
        if disease.lower() == "healthy":
            return PRIORITY_PREVENTIVE

        # Rule 2 & 3 – High spread risk triggers immediate action
        # (area threshold check included for explainability but both
        #  High-risk variants resolve to the same label per spec)
        if spread_risk == "High":
            return PRIORITY_IMMEDIATE

        # Rule 4 – Medium risk requires close monitoring
        if spread_risk == "Medium":
            return PRIORITY_MONITOR

        # Rule 5 – Low risk (default) → preventive measures only
        return PRIORITY_PREVENTIVE

    @staticmethod
    def _augment_recommendations(
        base: List[str],
        spread_risk: str,
        affected_area: float,
        priority: str,
    ) -> List[str]:
        """
        Append context-sensitive recommendations derived from risk rules.

        Only adds advice that is not already present (case-insensitive
        substring check) to avoid duplicates.

        Args:
            base:          Recommendations sourced from the knowledge base.
            spread_risk:   Forecast risk level.
            affected_area: Affected leaf area percentage.
            priority:      Computed priority label.

        Returns:
            Augmented list of recommendation strings.
        """
        augmented = list(base)  # work on a copy, never mutate the KB cache

        def _already_present(hint: str) -> bool:
            """Return True if *hint* text is already captured in the list."""
            hint_lower = hint.lower()
            return any(hint_lower in r.lower() for r in augmented)

        # High risk additions
        if spread_risk == "High":
            if not _already_present("neighboring"):
                augmented.append("Inspect and treat neighboring plants immediately.")
            if not _already_present("isolate"):
                augmented.append("Isolate severely infected plants to prevent spread.")

        # Large affected area additions
        if affected_area > HIGH_RISK_AREA_THRESHOLD:
            if not _already_present("agronomist"):
                augmented.append(
                    "Consult an agronomist — over 40% of the leaf area is affected."
                )

        # Medium risk addition
        if spread_risk == "Medium":
            if not _already_present("monitor"):
                augmented.append(
                    "Monitor disease progression daily and re-evaluate within 48 hours."
                )

        return augmented


# ---------------------------------------------------------------------------
# CLI entry point (mirrors the pattern used in diagnosis_agent.py)
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Advisory Agent with diagnosis and forecast JSON inputs."
    )
    parser.add_argument(
        "--diagnosis",
        type=str,
        required=True,
        help='Diagnosis JSON string, e.g. \'{"crop":"Tomato","disease":"Early Blight",'
             '"confidence":97.2,"affected_area_percent":23.7}\'',
    )
    parser.add_argument(
        "--forecast",
        type=str,
        required=True,
        help='Forecast JSON string, e.g. \'{"spread_risk":"Medium","risk_score":62}\'',
    )
    args = parser.parse_args()

    try:
        diagnosis: Dict[str, Any] = json.loads(args.diagnosis)
        forecast: Dict[str, Any]  = json.loads(args.forecast)

        agent = AdvisoryAgent()
        result = agent.advise(diagnosis=diagnosis, forecast=forecast)
        print(json.dumps(result, indent=2))

    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2))


if __name__ == "__main__":
    main()
