"""
tests/test_knowledge_base_tool.py

Unit tests for backend/mcp/knowledge_base_tool.py
---------------------------------------------------
Coverage:
  1. Valid crop + valid disease         → returns description, recommendations, prevention
  2. Healthy crop                       → "Healthy" treated as a normal disease entry
  3. Unknown crop                       → structured error dict (error: crop_not_found)
  4. Unknown disease on a known crop    → structured error dict (error: disease_not_found)
  5. Malformed JSON                     → ValueError raised during construction (mocked)

All file I/O is performed through module-level _load_knowledge_base, which
is patched or bypassed in the relevant tests so no real disk access is needed.
"""

import json
import os
import unittest
from unittest.mock import mock_open, patch

# Module under test
from backend.mcp.knowledge_base_tool import KnowledgeBaseTool, get_disease_info
import backend.mcp.knowledge_base_tool as kb_module


# ---------------------------------------------------------------------------
# Shared fixture: a minimal in-memory knowledge base that mirrors diseases.json
# ---------------------------------------------------------------------------
SAMPLE_KB: dict = {
    "Tomato": {
        "Healthy": {
            "description": "The tomato plant shows no visible disease symptoms.",
            "recommendations": [
                "Continue normal monitoring.",
                "Maintain proper irrigation.",
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
            ],
            "prevention": [
                "Avoid overhead irrigation.",
                "Rotate crops.",
            ],
        },
    },
    "Potato": {
        "Healthy": {
            "description": "Healthy potato foliage.",
            "recommendations": ["Continue monitoring."],
            "prevention": ["Practice crop rotation."],
        },
        "Late Blight": {
            "description": "Highly destructive disease favored by wet weather.",
            "recommendations": ["Treat immediately.", "Monitor surrounding crops."],
            "prevention": ["Avoid prolonged leaf wetness.", "Inspect crops regularly."],
        },
    },
}


class TestKnowledgeBaseTool(unittest.TestCase):
    """Tests for KnowledgeBaseTool using an in-memory knowledge base fixture."""

    def setUp(self) -> None:
        """
        Reset the module-level cache before every test so each test starts
        with a clean slate regardless of execution order.
        """
        kb_module._KNOWLEDGE_BASE_CACHE = None

    # ------------------------------------------------------------------
    # Helper: return a KnowledgeBaseTool backed by the sample fixture
    # ------------------------------------------------------------------
    def _make_tool(self) -> KnowledgeBaseTool:
        """
        Construct a KnowledgeBaseTool whose internal _kb is pre-loaded
        with SAMPLE_KB, bypassing all disk I/O.
        """
        tool = KnowledgeBaseTool.__new__(KnowledgeBaseTool)
        tool._kb = SAMPLE_KB
        return tool

    # ===================================================================
    # Test 1 – Valid crop and valid disease
    # ===================================================================
    def test_valid_crop_and_disease(self) -> None:
        """
        Querying a known crop + disease should return the three expected keys
        with non-empty, correct values.
        """
        tool = self._make_tool()
        result = tool.get_disease_info(crop="Tomato", disease="Early Blight")

        # All three keys must be present
        self.assertIn("description", result)
        self.assertIn("recommendations", result)
        self.assertIn("prevention", result)

        # Values must match the fixture data
        self.assertEqual(
            result["description"],
            "A fungal disease causing brown concentric spots on older leaves.",
        )
        self.assertIsInstance(result["recommendations"], list)
        self.assertGreater(len(result["recommendations"]), 0)

        self.assertIsInstance(result["prevention"], list)
        self.assertGreater(len(result["prevention"]), 0)

        # No error key when the query succeeds
        self.assertNotIn("error", result)

    # ===================================================================
    # Test 2 – Healthy crop
    # ===================================================================
    def test_healthy_crop(self) -> None:
        """
        'Healthy' is a valid disease entry in the knowledge base.
        The tool must return the Healthy description without errors.
        """
        tool = self._make_tool()
        result = tool.get_disease_info(crop="Tomato", disease="Healthy")

        self.assertNotIn("error", result)
        self.assertIn("description", result)
        self.assertEqual(
            result["description"],
            "The tomato plant shows no visible disease symptoms.",
        )
        self.assertIsInstance(result["recommendations"], list)
        self.assertIsInstance(result["prevention"], list)

    # ===================================================================
    # Test 3 – Unknown crop
    # ===================================================================
    def test_unknown_crop(self) -> None:
        """
        Querying a crop that is not in the knowledge base must return a
        structured error dict with error == 'crop_not_found'.
        It must NOT raise an exception.
        """
        tool = self._make_tool()
        result = tool.get_disease_info(crop="Wheat", disease="Rust")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "crop_not_found")
        self.assertIn("message", result)
        self.assertIn("Wheat", result["message"])

        # The original query params must be echoed for traceability
        self.assertEqual(result["crop"], "Wheat")
        self.assertEqual(result["disease"], "Rust")

    # ===================================================================
    # Test 4 – Unknown disease (crop exists, disease does not)
    # ===================================================================
    def test_unknown_disease(self) -> None:
        """
        Querying a valid crop with a disease that is not recorded must
        return a structured error dict with error == 'disease_not_found'.
        """
        tool = self._make_tool()
        result = tool.get_disease_info(crop="Tomato", disease="Yellow Rust")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "disease_not_found")
        self.assertIn("message", result)
        self.assertIn("Yellow Rust", result["message"])
        self.assertIn("Tomato", result["message"])

        # The original query params must be echoed
        self.assertEqual(result["crop"], "Tomato")
        self.assertEqual(result["disease"], "Yellow Rust")

    # ===================================================================
    # Test 5 – Malformed JSON (simulated via mock_open)
    # ===================================================================
    def test_malformed_json_raises_value_error(self) -> None:
        """
        If diseases.json contains invalid JSON, constructing KnowledgeBaseTool
        must raise a ValueError with a descriptive message.
        The module cache is reset before the test and the open() call is
        replaced with a mock that returns corrupt bytes.
        """
        # Reset cache so _load_knowledge_base tries to open the file again
        kb_module._KNOWLEDGE_BASE_CACHE = None

        corrupt_content = "{ this is NOT valid JSON !!!"

        # Patch os.path.exists so the file appears to exist,
        # and builtins.open so the read returns corrupt JSON.
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=corrupt_content)):

            with self.assertRaises(ValueError) as ctx:
                KnowledgeBaseTool()

            self.assertIn("malformed JSON", str(ctx.exception))

    # ===================================================================
    # Additional: module-level convenience function
    # ===================================================================
    def test_module_level_get_disease_info(self) -> None:
        """
        The module-level get_disease_info() wrapper must delegate to
        KnowledgeBaseTool and return the same result structure.
        """
        # Pre-load the cache with the fixture so no disk I/O is needed
        kb_module._KNOWLEDGE_BASE_CACHE = SAMPLE_KB

        result = get_disease_info(crop="Potato", disease="Late Blight")

        self.assertNotIn("error", result)
        self.assertIn("description", result)
        self.assertIn("recommendations", result)
        self.assertIn("prevention", result)
        self.assertEqual(
            result["description"],
            "Highly destructive disease favored by wet weather.",
        )


if __name__ == "__main__":
    unittest.main()
