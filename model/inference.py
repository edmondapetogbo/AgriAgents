import os
import json
import argparse
from typing import Dict, Any
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from model.config import (
    MODEL_PATH,
    CLASS_MAPPING_PATH,
    IMAGE_SIZE
)
from model.model import get_efficientnet_model

def load_class_mapping() -> Dict[str, Dict[str, str]]:
    """
    Loads the index-to-class mapping from JSON.
    """
    if not os.path.exists(CLASS_MAPPING_PATH):
        raise FileNotFoundError(
            f"Class mapping file not found at {CLASS_MAPPING_PATH}. "
            "Please train the model first to generate it."
        )
    with open(CLASS_MAPPING_PATH, "r") as f:
        return json.load(f)

def get_inference_transform() -> transforms.Compose:
    """
    Returns the required ImageNet normalization transforms for evaluation.
    """
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])

class DiseaseDetector:
    def __init__(self, model_path: str = MODEL_PATH):
        """
        Initializes the detector by loading class mapping and the trained model.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
        
        # Load mapping
        self.class_mapping = load_class_mapping()
        self.num_classes = len(self.class_mapping)
        
        # Initialize model architecture
        self.model = get_efficientnet_model(num_classes=self.num_classes, pretrained=False)
        
        # Load weights
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Trained model checkpoint not found at {model_path}. "
                "Please run training first."
            )
            
        # Load state dict (handle potential CPU/GPU/MPS cross-loading)
        state_dict = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        
        self.transform = get_inference_transform()

    @torch.no_grad()
    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Predicts crop and disease for a given image.
        
        Args:
            image_path: Path to the input image file.
            
        Returns:
            Dict conforming to the detect_crop_disease tool contract.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")
            
        # Load and preprocess image
        image = Image.open(image_path).convert("RGB")
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Forward pass
        outputs = self.model(img_tensor)
        probabilities = F.softmax(outputs, dim=1)[0]
        
        # Get top prediction
        confidence_val, pred_class_idx = torch.max(probabilities, dim=0)
        
        idx_str = str(pred_class_idx.item())
        class_info = self.class_mapping.get(idx_str, {"crop": "Unknown", "disease": "Unknown"})
        
        # Convert confidence to percentage scale (0-100) rounded to 1 decimal place
        confidence_percent = round(float(confidence_val.item()) * 100, 1)
        
        return {
            "crop": class_info["crop"],
            "disease": class_info["disease"],
            "confidence": confidence_percent
        }

def main():
    parser = argparse.ArgumentParser(description="Run disease detection inference on an image")
    parser.add_argument("--image_path", type=str, required=True, help="Path to input crop image")
    parser.add_argument("--model_path", type=str, default=MODEL_PATH, help="Path to model weights file")
    args = parser.parse_args()
    
    try:
        detector = DiseaseDetector(model_path=args.model_path)
        result = detector.predict(args.image_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()
