import os
from typing import Dict, Any

# Path settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXTRACT_DIR = os.path.join(DATA_DIR, "extracted")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model.pth")
CLASS_MAPPING_PATH = os.path.join(MODEL_DIR, "class_mapping.json")

# Training hyperparameters
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
NUM_EPOCHS = 10
IMAGE_SIZE = 224

# Target PlantVillage folders and their mapping to standard outputs
TARGET_CLASSES: Dict[str, Dict[str, str]] = {
    "Tomato___healthy": {"crop": "Tomato", "disease": "Healthy"},
    "Tomato___Early_blight": {"crop": "Tomato", "disease": "Early Blight"},
    "Tomato___Late_blight": {"crop": "Tomato", "disease": "Late Blight"},
    "Tomato___Leaf_Mold": {"crop": "Tomato", "disease": "Leaf Mold"},
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {"crop": "Tomato", "disease": "Yellow Leaf Curl Virus"},
    "Potato___healthy": {"crop": "Potato", "disease": "Healthy"},
    "Potato___Early_blight": {"crop": "Potato", "disease": "Early Blight"},
    "Potato___Late_blight": {"crop": "Potato", "disease": "Late Blight"},
    "Corn_(maize)___healthy": {"crop": "Corn", "disease": "Healthy"},
    "Corn_(maize)___Common_rust_": {"crop": "Corn", "disease": "Common Rust"},
    "Corn_(maize)___Northern_Leaf_Blight": {"crop": "Corn", "disease": "Northern Leaf Blight"},
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {"crop": "Corn", "disease": "Gray Leaf Spot"},
}

# Mapping patterns to match ZIP folders dynamically in case of slight naming variations
FOLDER_PATTERNS = {
    "tomato___healthy": "Tomato___healthy",
    "tomato___early_blight": "Tomato___Early_blight",
    "tomato___late_blight": "Tomato___Late_blight",
    "tomato___leaf_mold": "Tomato___Leaf_Mold",
    "tomato_yellow_leaf_curl": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "yellow_leaf_curl_virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "potato___healthy": "Potato___healthy",
    "potato___early_blight": "Potato___Early_blight",
    "potato___late_blight": "Potato___Late_blight",
    "corn___healthy": "Corn_(maize)___healthy",
    "corn_(maize)___healthy": "Corn_(maize)___healthy",
    "common_rust": "Corn_(maize)___Common_rust_",
    "northern_leaf_blight": "Corn_(maize)___Northern_Leaf_Blight",
    "gray_leaf_spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "cercospora": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
}
