"""
tests/test_report_agent.py

Unit tests for backend/agents/report_agent.py
----------------------------------------------
Coverage:
  1. Valid report           → all 11 output keys present with correct values
  2. Missing diagnosis key  → ValueError raised, message names the missing key
  3. Missing forecast key   → ValueError raised, message names the missing key
  4. Missing advisory key   → ValueError raised, message names the missing key

Additional tests:
  5. Healthy crop summary   → summary uses the short healthy-plant sentence
  6. Output contract keys   → report always has exactly the 11 expected keys
  7. Wrong input type       → TypeError raised when a non-dict is passed
"""

import unittest
from typing import Any, Dict

from backend.agents.report_agent import ReportAgent


# ---------------------------------------------------------------------------
# Shared fixtures – realistic outputs from the upstream agents
# ---------------------------------------------------------------------------

VALID_DIAGNOSIS: Dict[str, Any] = {
    "crop": "Tomato",
    "disease": "Early Blight",
    "confidence": 97.2,
    "affected_area_percent": 23.7,
}

VALID_FORECAST: Dict[str, Any] = {
    "spread_risk": "Medium",
    "risk_score": 62,
    "weather_summary": {
        "temperature": 29,
        "humidity": 82,
        "rain_probability": 67,
    },
    "reason": "High humidity increases fungal disease spread.",
}

VALID_ADVISORY: Dict[str, Any] = {
    "crop": "Tomato",
    "disease": "Early Blight",
    "spread_risk": "Medium",
    "priority": "Monitor Closely",
    "recommendations": [
        "Apply a suitable fungicide.",
        "Remove severely infected leaves.",
        "Improve air circulation.",
    ],
    "prevention": [
        "Avoid overhead irrigation.",
        "Rotate crops.",
        "Use disease-free seeds.",
    ],
}

# All 11 keys the Report Agent must always return
EXPECTED_OUTPUT_KEYS = {
    "summary",
    "crop",
    "disease",
    "confidence",
    "affected_area_percent",
    "spread_risk",
    "risk_score",
    "priority",
    "recommendations",
    "prevention",
    "weather_summary",
}


class TestReportAgent(unittest.TestCase):
    """Unit tests for ReportAgent.generate()."""

    def setUp(self) -> None:
        """Instantiate a fresh ReportAgent before each test."""
        self.agent = ReportAgent()

    # ===================================================================
    # Test 1 – Valid report
    # ===================================================================
    def test_valid_report(self) -> None:
        """
        Passing valid diagnosis, forecast, and advisory dicts should produce
        a report that:
          - contains all 11 required keys
          - correctly maps values from upstream agents
          - includes a non-empty summary sentence
        """
        report = self.agent.generate(
            diagnosis=VALID_DIAGNOSIS,
            forecast=VALID_FORECAST,
            advisory=VALID_ADVISORY,
        )

        # All expected output keys must be present
        self.assertEqual(set(report.keys()), EXPECTED_OUTPUT_KEYS)

        # Values must be correctly forwarded
        self.assertEqual(report["crop"],                  "Tomato")
        self.assertEqual(report["disease"],               "Early Blight")
        self.assertAlmostEqual(report["confidence"],       97.2, places=1)
        self.assertAlmostEqual(report["affected_area_percent"], 23.7, places=1)
        self.assertEqual(report["spread_risk"],           "Medium")
        self.assertEqual(report["risk_score"],             62)
        self.assertEqual(report["priority"],              "Monitor Closely")

        # Lists must be non-empty and match advisory input
        self.assertIsInstance(report["recommendations"], list)
        self.assertEqual(report["recommendations"], VALID_ADVISORY["recommendations"])

        self.assertIsInstance(report["prevention"], list)
        self.assertEqual(report["prevention"], VALID_ADVISORY["prevention"])

        # weather_summary must be forwarded from forecast unchanged
        self.assertEqual(report["weather_summary"], VALID_FORECAST["weather_summary"])

        # Summary must be a non-empty string mentioning crop and disease
        self.assertIsInstance(report["summary"], str)
        self.assertGreater(len(report["summary"]), 0)
        self.assertIn("Tomato",       report["summary"])
        self.assertIn("Early Blight", report["summary"])

    # ===================================================================
    # Test 2 – Missing diagnosis key
    # ===================================================================
    def test_missing_diagnosis_key(self) -> None:
        """
        Omitting 'confidence' from the diagnosis dict must raise a ValueError
        that explicitly names the missing key.
        """
        bad_diagnosis = {
            "crop": "Tomato",
            "disease": "Early Blight",
            # 'confidence' intentionally omitted
            "affected_area_percent": 23.7,
        }

        with self.assertRaises(ValueError) as ctx:
            self.agent.generate(
                diagnosis=bad_diagnosis,
                forecast=VALID_FORECAST,
                advisory=VALID_ADVISORY,
            )

        self.assertIn("confidence", str(ctx.exception))
        self.assertIn("diagnosis",  str(ctx.exception))

    # ===================================================================
    # Test 3 – Missing forecast key
    # ===================================================================
    def test_missing_forecast_key(self) -> None:
        """
        Omitting 'risk_score' from the forecast dict must raise a ValueError
        that explicitly names the missing key.
        """
        bad_forecast = {
            "spread_risk": "Medium",
            # 'risk_score' intentionally omitted
            "weather_summary": {},
        }

        with self.assertRaises(ValueError) as ctx:
            self.agent.generate(
                diagnosis=VALID_DIAGNOSIS,
                forecast=bad_forecast,
                advisory=VALID_ADVISORY,
            )

        self.assertIn("risk_score", str(ctx.exception))
        self.assertIn("forecast",   str(ctx.exception))

    # ===================================================================
    # Test 4 – Missing advisory key
    # ===================================================================
    def test_missing_advisory_key(self) -> None:
        """
        Omitting 'priority' from the advisory dict must raise a ValueError
        that explicitly names the missing key.
        """
        bad_advisory = {
            # 'priority' intentionally omitted
            "recommendations": [],
            "prevention": [],
        }

        with self.assertRaises(ValueError) as ctx:
            self.agent.generate(
                diagnosis=VALID_DIAGNOSIS,
                forecast=VALID_FORECAST,
                advisory=bad_advisory,
            )

        self.assertIn("priority", str(ctx.exception))
        self.assertIn("advisory", str(ctx.exception))

    # ===================================================================
    # Test 5 – Healthy crop summary
    # ===================================================================
    def test_healthy_crop_summary(self) -> None:
        """
        When disease is 'Healthy', the summary must use the shorter
        positive-health sentence and must NOT mention a priority action.
        """
        healthy_diagnosis = {
            "crop": "Potato",
            "disease": "Healthy",
            "confidence": 99.1,
            "affected_area_percent": 1.5,
        }
        healthy_forecast = {
            "spread_risk": "Low",
            "risk_score": 15,
            "weather_summary": {"temperature": 22, "humidity": 50, "rain_probability": 5},
        }
        healthy_advisory = {
            "priority": "Preventive Care",
            "recommendations": ["Continue normal monitoring."],
            "prevention": ["Maintain field hygiene."],
        }

        report = self.agent.generate(
            diagnosis=healthy_diagnosis,
            forecast=healthy_forecast,
            advisory=healthy_advisory,
        )

        # The summary should confirm the healthy status
        self.assertIn("healthy", report["summary"].lower())
        # It should NOT mention any disease name
        self.assertNotIn("Early Blight", report["summary"])
        self.assertEqual(report["disease"], "Healthy")
        self.assertEqual(report["priority"], "Preventive Care")

    # ===================================================================
    # Test 6 – Output contract keys always present
    # ===================================================================
    def test_output_contract_keys(self) -> None:
        """
        The report must always expose exactly the 11 keys specified in
        docs/api_contracts.md, no more, no less.
        """
        report = self.agent.generate(
            diagnosis=VALID_DIAGNOSIS,
            forecast=VALID_FORECAST,
            advisory=VALID_ADVISORY,
        )

        self.assertEqual(set(report.keys()), EXPECTED_OUTPUT_KEYS)

    # ===================================================================
    # Test 7 – Wrong input type raises TypeError
    # ===================================================================
    def test_wrong_input_type_raises_type_error(self) -> None:
        """
        Passing a non-dict (e.g. None or a string) for any of the three
        inputs must raise a TypeError with the offending argument named.
        """
        # None passed as diagnosis
        with self.assertRaises(TypeError) as ctx_diag:
            self.agent.generate(
                diagnosis=None,           # type: ignore[arg-type]
                forecast=VALID_FORECAST,
                advisory=VALID_ADVISORY,
            )
        self.assertIn("diagnosis", str(ctx_diag.exception))

        # String passed as forecast
        with self.assertRaises(TypeError) as ctx_fore:
            self.agent.generate(
                diagnosis=VALID_DIAGNOSIS,
                forecast="not a dict",    # type: ignore[arg-type]
                advisory=VALID_ADVISORY,
            )
        self.assertIn("forecast", str(ctx_fore.exception))

        # List passed as advisory
        with self.assertRaises(TypeError) as ctx_adv:
            self.agent.generate(
                diagnosis=VALID_DIAGNOSIS,
                forecast=VALID_FORECAST,
                advisory=["not", "a", "dict"],  # type: ignore[arg-type]
            )
        self.assertIn("advisory", str(ctx_adv.exception))

    # ===================================================================
    # Test 8 – Forecast without optional weather_summary
    # ===================================================================
    def test_forecast_without_weather_summary(self) -> None:
        """
        A forecast dict that omits the optional 'weather_summary' field
        should still produce a valid report with weather_summary == {}.
        """
        minimal_forecast = {
            "spread_risk": "Low",
            "risk_score": 20,
            # 'weather_summary' intentionally omitted
        }

        report = self.agent.generate(
            diagnosis=VALID_DIAGNOSIS,
            forecast=minimal_forecast,
            advisory=VALID_ADVISORY,
        )

        # weather_summary must default to an empty dict, not raise
        self.assertEqual(report["weather_summary"], {})
        self.assertEqual(report["spread_risk"], "Low")


if __name__ == "__main__":
    unittest.main()
