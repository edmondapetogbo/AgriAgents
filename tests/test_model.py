import os
import unittest
from unittest.mock import MagicMock, patch
import torch
import torch.nn as nn
from PIL import Image

from model.config import TARGET_CLASSES
from model.model import get_efficientnet_model
from model.dataset import get_target_class_from_path, get_transforms, PlantVillageDataset

class TestDiseaseModel(unittest.TestCase):
    
    def test_model_architecture(self):
        """
        Verify that the custom EfficientNet-B0 model instantiates correctly
        and produces the expected output shape [batch_size, num_classes].
        """
        num_classes = 12
        model = get_efficientnet_model(num_classes=num_classes, pretrained=False)
        self.assertIsInstance(model, nn.Module)
        
        # Test input shape
        test_input = torch.randn(2, 3, 224, 224)
        output = model(test_input)
        
        self.assertEqual(output.shape, (2, num_classes))

    def test_class_matching(self):
        """
        Verify that path names are matched correctly to canonical target classes.
        """
        test_cases = {
            "PlantVillage-Dataset-master/raw/color/Tomato___healthy/0001.JPG": "Tomato___healthy",
            "raw/color/Potato___Early_blight/img_12.png": "Potato___Early_blight",
            "PlantVillage/raw/color/Corn_(maize)___Common_rust_/rust_1.jpg": "Corn_(maize)___Common_rust_",
            "raw/color/Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot/spot.jpeg": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
            # Invalid paths
            "raw/grayscale/Tomato___healthy/0001.JPG": None,
            "other_folder/Tomato___healthy/0001.JPG": None,
        }
        
        for path, expected in test_cases.items():
            result = get_target_class_from_path(path)
            self.assertEqual(result, expected, f"Failed matching for path: {path}")

    def test_dataset_transforms(self):
        """
        Verify that transforms reshape images to the target size.
        """
        train_transform, val_transform = get_transforms()
        
        # Create a mock PIL image
        mock_img = Image.new("RGB", (300, 300), color="green")
        
        train_tensor = train_transform(mock_img)
        val_tensor = val_transform(mock_img)
        
        self.assertEqual(train_tensor.shape, (3, 224, 224))
        self.assertEqual(val_tensor.shape, (3, 224, 224))
        self.assertIsInstance(train_tensor, torch.Tensor)
        self.assertIsInstance(val_tensor, torch.Tensor)

    def test_dataset_len_and_getitem(self):
        """
        Verify that the custom PlantVillageDataset functions correctly.
        """
        file_paths = ["fake_img1.jpg", "fake_img2.jpg"]
        labels = [0, 1]
        
        # Mock PIL.Image.open to avoid loading files from disk
        mock_image = Image.new("RGB", (100, 100))
        
        with patch("PIL.Image.open", return_value=mock_image) as mock_open:
            dataset = PlantVillageDataset(file_paths, labels, transform=None)
            self.assertEqual(len(dataset), 2)
            
            img, label = dataset[0]
            mock_open.assert_called_once_with("fake_img1.jpg")
            self.assertEqual(label, 0)
            self.assertIsInstance(img, Image.Image)

    @patch("model.inference.load_class_mapping")
    @patch("model.inference.get_efficientnet_model")
    @patch("model.inference.os.path.exists")
    @patch("torch.load")
    def test_inference_detector_contract(self, mock_torch_load, mock_exists, mock_get_model, mock_load_mapping):
        """
        Verify that the inference class DiseaseDetector correctly initializes
        and outputs matches conforming to the Diagnosis Agent output contract.
        """
        # Mock class mapping
        mock_load_mapping.return_value = {
            "0": {"class_name": "Tomato___Early_blight", "crop": "Tomato", "disease": "Early Blight"}
        }
        # Mock exist checks for mapping and model paths
        mock_exists.return_value = True
        
        # Mock model and output
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Make model output a mock prediction of class index 0 with high logit
        mock_output = torch.zeros(1, 1)
        mock_output[0, 0] = 10.0 # High value for class 0
        mock_model.return_value = mock_output
        
        from model.inference import DiseaseDetector
        
        detector = DiseaseDetector(model_path="fake_path.pth")
        
        # Mock image loading
        mock_image = Image.new("RGB", (100, 100))
        with patch("PIL.Image.open", return_value=mock_image):
            result = detector.predict("fake_image.jpg")
            
            # Check contract structure
            self.assertIn("crop", result)
            self.assertIn("disease", result)
            self.assertIn("confidence", result)
            
            self.assertEqual(result["crop"], "Tomato")
            self.assertEqual(result["disease"], "Early Blight")
            self.assertIsInstance(result["confidence"], float)
            self.assertGreaterEqual(result["confidence"], 0.0)
            self.assertLessEqual(result["confidence"], 100.0)

if __name__ == "__main__":
    unittest.main()
