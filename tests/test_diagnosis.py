import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from backend.mcp.affected_area_tool import estimate_affected_area
from backend.agents.diagnosis_agent import DiagnosisAgent

class TestDiagnosisDay2(unittest.TestCase):
    
    def setUp(self):
        # Create a synthetic test image directory inside the project
        self.test_img_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests")
        os.makedirs(self.test_img_dir, exist_ok=True)
        self.synthetic_img_path = os.path.join(self.test_img_dir, "temp_synthetic_leaf.jpg")

    def tearDown(self):
        # Clean up synthetic image if it exists
        if os.path.exists(self.synthetic_img_path):
            os.remove(self.synthetic_img_path)

    def test_affected_area_segmentation(self):
        """
        Verify that estimate_affected_area correctly segments a synthetic leaf
        containing healthy green and diseased brown regions.
        """
        # Create a 200x200 BGR image
        # Outer part (3/4 of pixels): healthy green (BGR: 0, 150, 0)
        # Inner 100x100 square (1/4 of pixels, 25%): diseased brown (BGR: 0, 50, 100)
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[:, :] = [0, 150, 0]  # Green leaf tissue
        img[50:150, 50:150] = [0, 50, 100]  # Brown diseased tissue (25% of the area)
        
        cv2.imwrite(self.synthetic_img_path, img)
        
        # Estimate affected area percentage
        percent = estimate_affected_area(self.synthetic_img_path)
        
        # Expected is around 25.0%
        self.assertAlmostEqual(percent, 25.0, delta=2.0)

    def test_affected_area_empty_image(self):
        """
        Verify that an image with no leaf pixels (e.g. plain black background) returns 0%.
        """
        # Plain black background (no saturation/value)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(self.synthetic_img_path, img)
        
        percent = estimate_affected_area(self.synthetic_img_path)
        self.assertEqual(percent, 0.0)

    @patch("backend.agents.diagnosis_agent.DiseaseDetector")
    @patch("backend.agents.diagnosis_agent.estimate_affected_area")
    def test_diagnosis_agent_flow(self, mock_estimate_area, mock_detector_class):
        """
        Verify that the DiagnosisAgent combines classification and affected area estimation
        into the correct JSON structure.
        """
        # Mock detector and predict output
        mock_detector_instance = MagicMock()
        mock_detector_instance.predict.return_value = {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 98.4
        }
        mock_detector_class.return_value = mock_detector_instance
        
        # Mock affected area tool output
        mock_estimate_area.return_value = 18.5
        
        agent = DiagnosisAgent(model_path="mock_model.pth")
        
        with patch("os.path.exists", return_value=True):
            result = agent.diagnose("dummy_leaf.jpg")
            
            # Assert contract structure
            self.assertEqual(result["crop"], "Tomato")
            self.assertEqual(result["disease"], "Early Blight")
            self.assertEqual(result["confidence"], 98.4)
            self.assertEqual(result["affected_area_percent"], 18.5)
            
            # Verify calls
            mock_detector_instance.predict.assert_called_once_with("dummy_leaf.jpg")
            mock_estimate_area.assert_called_once_with("dummy_leaf.jpg")

if __name__ == "__main__":
    unittest.main()
