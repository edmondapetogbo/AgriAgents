import os
import json
import argparse
from typing import Dict, Any

from model.inference import DiseaseDetector
from backend.mcp.affected_area_tool import estimate_affected_area

class DiagnosisAgent:
    def __init__(self, model_path: str = None):
        """
        Initializes the Diagnosis Agent by loading the disease detector model.
        
        Args:
            model_path: Optional custom path to the model weights.
        """
        # If model_path is not specified, let DiseaseDetector use its default
        if model_path:
            self.detector = DiseaseDetector(model_path=model_path)
        else:
            self.detector = DiseaseDetector()

    def diagnose(self, image_path: str) -> Dict[str, Any]:
        """
        Performs diagnosis by combining crop/disease classification and affected leaf area estimation.
        
        Args:
            image_path: Path to the input image file.
            
        Returns:
            Dict conforming to the Diagnosis Agent contract:
            {
                "crop": "...",
                "disease": "...",
                "confidence": 97.2,
                "affected_area_percent": 23.7
            }
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")
            
        # 1. Run disease detection model
        disease_results = self.detector.predict(image_path)
        
        # 2. Run OpenCV affected-area estimation tool
        affected_area_percent = estimate_affected_area(image_path)
        
        # 3. Combine results
        diagnosis = {
            "crop": disease_results["crop"],
            "disease": disease_results["disease"],
            "confidence": disease_results["confidence"],
            "affected_area_percent": affected_area_percent
        }
        
        return diagnosis

def main():
    parser = argparse.ArgumentParser(description="Run Diagnosis Agent for crop disease and affected area")
    parser.add_argument("--image_path", type=str, required=True, help="Path to input crop image")
    parser.add_argument("--model_path", type=str, default=None, help="Optional custom path to model weights")
    args = parser.parse_args()
    
    try:
        agent = DiagnosisAgent(model_path=args.model_path)
        result = agent.diagnose(args.image_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()
