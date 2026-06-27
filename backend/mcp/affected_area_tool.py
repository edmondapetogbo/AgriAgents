import os
import cv2
import numpy as np
import argparse
import json
from typing import Dict, Any

def estimate_affected_area(image_path: str) -> float:
    """
    Estimates the percentage of affected (diseased) leaf area using OpenCV.
    
    This function:
    1. Loads the image.
    2. Converts it to the HSV color space.
    3. Segments the leaf from neutral backgrounds by thresholding Saturation and Value channels.
    4. Identifies healthy green areas using specific HSV ranges.
    5. Calculates the diseased area as leaf pixels that do not fall into the healthy green range.
    6. Returns the percentage of diseased leaf area.
    
    Args:
        image_path: Absolute or relative path to the image.
        
    Returns:
        float: Percentage of affected area (0.0 to 100.0) rounded to 1 decimal place.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
        
    # Read the image in BGR format
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to read image at {image_path}")
        
    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    
    # 1. Segment leaf from background
    # PlantVillage leaf images typically have neutral (gray/black/off-white) backgrounds.
    # Leaf tissue is colorful, meaning it has higher saturation.
    # Threshold Saturation (s > 25) and Value (v > 20) to find leaf pixels.
    _, sat_mask = cv2.threshold(s, 25, 255, cv2.THRESH_BINARY)
    _, val_mask = cv2.threshold(v, 20, 255, cv2.THRESH_BINARY)
    leaf_mask = cv2.bitwise_and(sat_mask, val_mask)
    
    # Apply morphological closing and opening to remove small holes and noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel)
    
    # 2. Segment healthy green areas on the leaf
    # Healthy green hue is generally between 30 and 90 in OpenCV HSV scale.
    lower_green = np.array([30, 35, 30])
    upper_green = np.array([90, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Healthy green leaf pixels
    healthy_mask = cv2.bitwise_and(leaf_mask, green_mask)
    
    # 3. Diseased leaf pixels (leaf pixels that are NOT healthy green)
    diseased_mask = cv2.bitwise_and(leaf_mask, cv2.bitwise_not(healthy_mask))
    
    # 4. Calculate counts and percentage
    leaf_pixels = int(cv2.countNonZero(leaf_mask))
    diseased_pixels = int(cv2.countNonZero(diseased_mask))
    
    if leaf_pixels == 0:
        # Fallback if no leaf pixels are detected: assume 0% affected area
        return 0.0
        
    affected_percent = (diseased_pixels / leaf_pixels) * 100.0
    
    # Clamp between 0.0 and 100.0 and round to 1 decimal place
    affected_percent = max(0.0, min(100.0, affected_percent))
    return round(affected_percent, 1)

def main():
    parser = argparse.ArgumentParser(description="Estimate affected crop leaf area percentage using OpenCV")
    parser.add_argument("--image_path", type=str, required=True, help="Path to input crop leaf image")
    args = parser.parse_args()
    
    try:
        affected_area = estimate_affected_area(args.image_path)
        print(json.dumps({"affected_area_percent": affected_area}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()
