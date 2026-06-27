"""
backend/mcp/knowledge_base_tool.py

MCP Tool: Knowledge Base Loader
--------------------------------
Loads knowledge_base/diseases.json exactly once and caches it for the
lifetime of the process.  Provides get_disease_info() which is consumed
by the Advisory Agent to retrieve crop-disease information.

JSON structure expected in diseases.json:
{
    "<Crop>": {
        "<Disease>": {
            "description": "...",
            "recommendations": [...],
            "prevention": [...]
        }
    }
}
"""

import json
import os
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Module-level cache
# The JSON file is loaded once and stored here so subsequent calls are O(1).
# ---------------------------------------------------------------------------
_KNOWLEDGE_BASE_CACHE: Optional[Dict[str, Any]] = None

# Resolve path relative to this file so the tool works regardless of the
# current working directory at runtime.
_KB_FILE_PATH: str = os.path.join(
    os.path.dirname(__file__),   # backend/mcp/
    "..",                        # backend/
    "..",                        # project root
    "knowledge_base",
    "diseases.json",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_knowledge_base(kb_path: str = _KB_FILE_PATH) -> Dict[str, Any]:
    """
    Load and return the knowledge base from *kb_path*.

    The result is stored in the module-level ``_KNOWLEDGE_BASE_CACHE`` so
    that the file is only read from disk once per process lifetime.

    Args:
        kb_path: Absolute or relative path to diseases.json.
                 Defaults to the standard project location.

    Returns:
        Dict containing the full knowledge base.

    Raises:
        FileNotFoundError: If the JSON file does not exist at *kb_path*.
        ValueError: If the JSON file is malformed or cannot be parsed.
    """
    global _KNOWLEDGE_BASE_CACHE

    # Return the cached version if it is already populated.
    if _KNOWLEDGE_BASE_CACHE is not None:
        return _KNOWLEDGE_BASE_CACHE

    # Resolve to an absolute path for a clear error message.
    resolved_path = os.path.abspath(kb_path)

    if not os.path.exists(resolved_path):
        raise FileNotFoundError(
            f"Knowledge base file not found at: {resolved_path}"
        )

    try:
        with open(resolved_path, "r", encoding="utf-8") as fh:
            _KNOWLEDGE_BASE_CACHE = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Knowledge base file is malformed JSON: {exc}"
        ) from exc

    return _KNOWLEDGE_BASE_CACHE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class KnowledgeBaseTool:
    """
    MCP tool that provides structured crop-disease information by querying
    the knowledge_base/diseases.json file.

    The JSON is loaded once on the first call and cached in-process, so
    repeated calls incur no I/O overhead.

    Usage (Advisory Agent)::

        kb = KnowledgeBaseTool()
        info = kb.get_disease_info(crop="Tomato", disease="Early Blight")
    """

    def __init__(self, kb_path: str = _KB_FILE_PATH) -> None:
        """
        Initialise the tool and eagerly load the knowledge base.

        Args:
            kb_path: Path to diseases.json.  Defaults to the standard
                     project location derived from this file's position.

        Raises:
            FileNotFoundError: If diseases.json does not exist.
            ValueError: If diseases.json is malformed.
        """
        # Trigger the load now so any I/O errors surface at construction time
        # rather than silently failing on the first query.
        self._kb: Dict[str, Any] = _load_knowledge_base(kb_path)

    # ------------------------------------------------------------------
    # Core query method
    # ------------------------------------------------------------------

    def get_disease_info(
        self,
        crop: str,
        disease: str,
    ) -> Dict[str, Any]:
        """
        Return disease information for the given *crop* / *disease* pair.

        The Advisory Agent uses this to obtain recommendations and
        prevention strategies before building the final advisory report.

        Args:
            crop:    Crop name (case-sensitive), e.g. ``"Tomato"``.
            disease: Disease name (case-sensitive), e.g. ``"Early Blight"``.
                     Use ``"Healthy"`` for crops showing no disease symptoms.

        Returns:
            A dict with exactly three keys::

                {
                    "description":     str,
                    "recommendations": list[str],
                    "prevention":      list[str],
                }

        Raises:
            KeyError: If *crop* is not present in the knowledge base, wrapped
                      in a structured ``dict`` for agent-friendly handling.
            KeyError: If *disease* is not present under *crop*, wrapped
                      in a structured ``dict``.

        Note:
            The method never raises an uncaught exception; it always returns
            either a valid result dict or a structured error dict so that the
            calling agent can handle failures gracefully.
        """
        # --- Validate crop -----------------------------------------------
        if crop not in self._kb:
            available_crops = list(self._kb.keys())
            return {
                "error": "crop_not_found",
                "message": (
                    f"Crop '{crop}' was not found in the knowledge base. "
                    f"Available crops: {available_crops}"
                ),
                "crop": crop,
                "disease": disease,
            }

        crop_data: Dict[str, Any] = self._kb[crop]

        # --- Validate disease ---------------------------------------------
        if disease not in crop_data:
            available_diseases = list(crop_data.keys())
            return {
                "error": "disease_not_found",
                "message": (
                    f"Disease '{disease}' was not found for crop '{crop}'. "
                    f"Available diseases: {available_diseases}"
                ),
                "crop": crop,
                "disease": disease,
            }

        disease_data: Dict[str, Any] = crop_data[disease]

        # --- Return structured result -------------------------------------
        return {
            "description":     disease_data.get("description", ""),
            "recommendations": disease_data.get("recommendations", []),
            "prevention":      disease_data.get("prevention", []),
        }


# ---------------------------------------------------------------------------
# Module-level convenience alias (matches architecture contract)
# ---------------------------------------------------------------------------

def get_disease_info(crop: str, disease: str) -> Dict[str, Any]:
    """
    Module-level wrapper around ``KnowledgeBaseTool.get_disease_info``.

    Provided so the MCP layer can call ``get_disease_info(crop, disease)``
    without needing to instantiate the class directly.

    Args:
        crop:    Crop name, e.g. ``"Tomato"``.
        disease: Disease name, e.g. ``"Early Blight"``.

    Returns:
        Same dict as ``KnowledgeBaseTool.get_disease_info``.
    """
    tool = KnowledgeBaseTool()
    return tool.get_disease_info(crop=crop, disease=disease)
