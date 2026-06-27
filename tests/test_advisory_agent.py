"""
tests/test_advisory_agent.py

Unit tests for backend/agents/advisory_agent.py
-------------------------------------------------
Coverage:
  1. Healthy crop          → priority == "Preventive Care", no error
  2. Low risk              → priority == "Preventive Care"
  3. Medium risk           → priority == "Monitor Closely"
  4. High risk             → priority == "Immediate Action"
  5. Unknown disease       → KeyError raised (KB returns disease_not_found)
  6. Missing diagnosis key → ValueError raised at validation
  7. Missing forecast key  → ValueError raised at validation

All tests bypass disk I/O by pre-loading the module-level KB cache
(same pattern used in test_knowledge_base_tool.py).
"""

import unittest

import backend.mcp.knowledge_base_tool as kb_module
from backend.agents.advisory_agent import (
    AdvisoryAgent,
    PRIORITY_IMMEDIATE,
    PRIORITY_MONITOR,
    PRIORITY_PREVENTIVE,
)


# ---------------------------------------------------------------------------
# Shared in-memory fixture that mirrors diseases.json
# ---------------------------------------------------------------------------
SAMPLE_KB: dict = {
    "Tomato": {
        "Healthy": {
            "description": "The tomato plant shows no visible disease symptoms.",
            "recommendations": [
                "Continue normal monitoring.",
                "Maintain proper irrigation.",
                "Inspect plants weekly.",
            ],
            "prevention": [
                "Maintain field hygiene.",
                "Rotate crops regularly.",
            ],
        },
        "Early Blight": {
            "description": "A fungal disease causing brown concentric spots on older leaves.",
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
        },
        "Late Blight": {
            "description": "An aggressive disease that spreads rapidly in humid conditions.",
            "recommendations": [
                "Apply fungicide immediately.",
                "Monitor nearby plants.",
                "Remove severely infected plants.",
            ],
            "prevention": [
                "Avoid excessive moisture.",
                "Ensure good spacing.",
                "Inspect plants frequently.",
            ],
        },
    },
    "Potato": {
        "Healthy": {
            "description": "Healthy potato foliage.",
            "recommendations": ["Continue monitoring."],
            "prevention": ["Practice crop rotation."],
        },
    },
    "Corn": {
        "Healthy": {
            "description": "Healthy maize plant.",
            "recommendations": ["Continue monitoring."],
            "prevention": ["Maintain proper nutrition."],
        },
        "Common Rust": {
            "description": "Fungal disease producing reddish pustules.",
            "recommendations": ["Apply fungicide if necessary."],
            "prevention": ["Use resistant hybrids."],
        },
    },
}


class TestAdvisoryAgent(unittest.TestCase):
    """Tests for AdvisoryAgent using an in-memory knowledge base."""

    def setUp(self) -> None:
        """
        Reset the KB module cache and inject the in-memory fixture before
        every test, so each test starts from a known, deterministic state.
        """
        # Inject our fixture into the module-level cache so no disk I/O occurs.
        kb_module._KNOWLEDGE_BASE_CACHE = SAMPLE_KB
        # Now construct the agent (KnowledgeBaseTool will use the cached dict).
        self.agent = AdvisoryAgent()

    def tearDown(self) -> None:
        """Reset the module-level cache after each test."""
        kb_module._KNOWLEDGE_BASE_CACHE = None

    # ===================================================================
    # Helper: build standard input dicts
    # ===================================================================
    @staticmethod
    def _make_diagnosis(
        crop: str = "Tomato",
        disease: str = "Early Blight",
        confidence: float = 97.2,
        affected_area: float = 23.7,
    ) -> dict:
        return {
            "crop": crop,
            "disease": disease,
            "confidence": confidence,
            "affected_area_percent": affected_area,
        }

    @staticmethod
    def _make_forecast(
        spread_risk: str = "Medium",
        risk_score: int = 62,
    ) -> dict:
        return {
            "spread_risk": spread_risk,
            "risk_score": risk_score,
        }

    # ===================================================================
    # Test 1 – Healthy crop
    # ===================================================================
    def test_healthy_crop(self) -> None:
        """
        A healthy crop should always yield 'Preventive Care' regardless of
        the forecast spread_risk level, and must return valid KB data.
        """
        diagnosis = self._make_diagnosis(disease="Healthy", affected_area=2.0)
        forecast  = self._make_forecast(spread_risk="Low", risk_score=10)

        result = self.agent.advise(diagnosis=diagnosis, forecast=forecast)

        # Priority must be Preventive Care for a healthy crop
        self.assertEqual(result["priority"], PRIORITY_PREVENTIVE)

        # Standard keys must be present
        self.assertEqual(result["crop"], "Tomato")
        self.assertEqual(result["disease"], "Healthy")
        self.assertIsInstance(result["recommendations"], list)
        self.assertIsInstance(result["prevention"], list)
        self.assertGreater(len(result["recommendations"]), 0)

        # No error key
        self.assertNotIn("error", result)

    # ===================================================================
    # Test 2 – Low risk
    # ===================================================================
    def test_low_risk(self) -> None:
        """
        A detected disease with Low spread risk must yield 'Preventive Care'.
        """
        diagnosis = self._make_diagnosis(
            disease="Early Blight", affected_area=15.0
        )
        forecast = self._make_forecast(spread_risk="Low", risk_score=25)

        result = self.agent.advise(diagnosis=diagnosis, forecast=forecast)

        self.assertEqual(result["priority"], PRIORITY_PREVENTIVE)
        self.assertEqual(result["spread_risk"], "Low")
        self.assertIn("recommendations", result)
        self.assertIn("prevention", result)
        self.assertNotIn("error", result)

    # ===================================================================
    # Test 3 – Medium risk
    # ===================================================================
    def test_medium_risk(self) -> None:
        """
        A detected disease with Medium spread risk must yield 'Monitor Closely'.
        The augmentation logic should also append a monitoring reminder.
        """
        diagnosis = self._make_diagnosis(
            disease="Early Blight", affected_area=23.7
        )
        forecast = self._make_forecast(spread_risk="Medium", risk_score=62)

        result = self.agent.advise(diagnosis=diagnosis, forecast=forecast)

        self.assertEqual(result["priority"], PRIORITY_MONITOR)
        self.assertEqual(result["spread_risk"], "Medium")

        # Augmented recommendation should mention monitoring
        combined_recs = " ".join(result["recommendations"]).lower()
        self.assertIn("monitor", combined_recs)

    # ===================================================================
    # Test 4 – High risk
    # ===================================================================
    def test_high_risk(self) -> None:
        """
        High spread risk must always yield 'Immediate Action', even when
        affected_area is below the 40 % threshold.
        When affected_area > 40 %, an agronomist referral should also appear.
        """
        # 4a – High risk, area below threshold
        diagnosis_low_area = self._make_diagnosis(
            disease="Late Blight", affected_area=25.0
        )
        forecast_high = self._make_forecast(spread_risk="High", risk_score=85)

        result_low = self.agent.advise(
            diagnosis=diagnosis_low_area, forecast=forecast_high
        )
        self.assertEqual(result_low["priority"], PRIORITY_IMMEDIATE)

        # 4b – High risk AND area > 40 % → agronomist referral appended
        diagnosis_high_area = self._make_diagnosis(
            disease="Late Blight", affected_area=55.0
        )
        result_high = self.agent.advise(
            diagnosis=diagnosis_high_area, forecast=forecast_high
        )
        self.assertEqual(result_high["priority"], PRIORITY_IMMEDIATE)

        combined_recs = " ".join(result_high["recommendations"]).lower()
        self.assertIn("agronomist", combined_recs)

    # ===================================================================
    # Test 5 – Unknown disease (crop exists, disease does not)
    # ===================================================================
    def test_unknown_disease(self) -> None:
        """
        Querying a disease not present in the knowledge base must raise
        a KeyError with a descriptive message.  The agent must NOT silently
        return empty lists.
        """
        diagnosis = self._make_diagnosis(
            crop="Tomato", disease="Powdery Mildew", affected_area=30.0
        )
        forecast = self._make_forecast(spread_risk="Medium", risk_score=50)

        with self.assertRaises(KeyError) as ctx:
            self.agent.advise(diagnosis=diagnosis, forecast=forecast)

        # Error message should mention the unrecognised disease
        self.assertIn("Powdery Mildew", str(ctx.exception))

    # ===================================================================
    # Test 6 – Missing diagnosis key
    # ===================================================================
    def test_missing_diagnosis_key(self) -> None:
        """
        Omitting 'affected_area_percent' from diagnosis must raise a
        ValueError before any KB lookup occurs.
        """
        bad_diagnosis = {
            "crop": "Tomato",
            "disease": "Early Blight",
            # 'affected_area_percent' intentionally omitted
            "confidence": 92.0,
        }
        forecast = self._make_forecast()

        with self.assertRaises(ValueError) as ctx:
            self.agent.advise(diagnosis=bad_diagnosis, forecast=forecast)

        self.assertIn("affected_area_percent", str(ctx.exception))

    # ===================================================================
    # Test 7 – Missing forecast key
    # ===================================================================
    def test_missing_forecast_key(self) -> None:
        """
        Omitting 'spread_risk' from forecast must raise a ValueError
        before any KB lookup occurs.
        """
        diagnosis = self._make_diagnosis()
        bad_forecast = {
            # 'spread_risk' intentionally omitted
            "risk_score": 62,
        }

        with self.assertRaises(ValueError) as ctx:
            self.agent.advise(diagnosis=diagnosis, forecast=bad_forecast)

        self.assertIn("spread_risk", str(ctx.exception))

    # ===================================================================
    # Additional: output contract structure
    # ===================================================================
    def test_output_contract_keys(self) -> None:
        """
        The advisory output must always contain exactly the six keys
        defined in docs/api_contracts.md, regardless of input.
        """
        diagnosis = self._make_diagnosis()
        forecast  = self._make_forecast()

        result = self.agent.advise(diagnosis=diagnosis, forecast=forecast)

        expected_keys = {"crop", "disease", "spread_risk",
                         "recommendations", "prevention", "priority"}
        self.assertEqual(set(result.keys()), expected_keys)

    def test_corn_common_rust_medium_risk(self) -> None:
        """
        Cross-crop test: Corn + Common Rust + Medium risk should return
        KB data for Corn and yield 'Monitor Closely'.
        """
        diagnosis = self._make_diagnosis(
            crop="Corn", disease="Common Rust", affected_area=18.0
        )
        forecast  = self._make_forecast(spread_risk="Medium", risk_score=55)

        result = self.agent.advise(diagnosis=diagnosis, forecast=forecast)

        self.assertEqual(result["crop"], "Corn")
        self.assertEqual(result["disease"], "Common Rust")
        self.assertEqual(result["priority"], PRIORITY_MONITOR)
        self.assertIsInstance(result["recommendations"], list)
        self.assertIsInstance(result["prevention"], list)


if __name__ == "__main__":
    unittest.main()
