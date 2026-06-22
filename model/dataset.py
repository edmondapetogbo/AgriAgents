import os
import zipfile
import urllib.request
from typing import List, Tuple, Dict
from PIL import Image
from tqdm import tqdm
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from sklearn.model_selection import train_test_split

from model.config import (
    DATA_DIR,
    EXTRACT_DIR,
    TARGET_CLASSES,
    FOLDER_PATTERNS,
    IMAGE_SIZE
)

def get_target_class_from_path(zip_path: str) -> str:
    """
    Checks if a file in the zip belongs to one of our target classes based on patterns.
    """
    lower_path = zip_path.lower()
    if "raw/color/" not in lower_path:
        return None
        
    # Extract directory name after raw/color/
    parts = zip_path.split("raw/color/")
    if len(parts) < 2:
        return None
        
    sub_path = parts[1]
    folder_name = sub_path.split("/")[0]
    folder_name_lower = folder_name.lower()
    
    # Try to match the folder name against our patterns
    for pattern, target in FOLDER_PATTERNS.items():
        if pattern in folder_name_lower:
            return target
            
    return None

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_and_extract_dataset() -> None:
    """
    Downloads the PlantVillage dataset zip and extracts only target classes.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Check if target classes directories already exist and contain images
    all_exist = True
    for cls in TARGET_CLASSES.keys():
        cls_dir = os.path.join(EXTRACT_DIR, cls)
        if not os.path.exists(cls_dir) or len(os.listdir(cls_dir)) == 0:
            all_exist = False
            break
            
    if all_exist:
        print("Dataset already downloaded and extracted.")
        return

    zip_url = "https://github.com/spMohanty/PlantVillage-Dataset/archive/refs/heads/master.zip"
    zip_path = os.path.join(DATA_DIR, "plantvillage.zip")
    
    print(f"Downloading PlantVillage dataset from {zip_url}...")
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=zip_url.split('/')[-1]) as t:
        urllib.request.urlretrieve(zip_url, filename=zip_path, reporthook=t.update_to)
        
    print("Extracting target classes from ZIP archive...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    # Create class subdirectories
    for cls in TARGET_CLASSES.keys():
        os.makedirs(os.path.join(EXTRACT_DIR, cls), exist_ok=True)
        
    extracted_counts = {cls: 0 for cls in TARGET_CLASSES.keys()}
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Loop through all files in the zip and extract only matching ones
        for member in tqdm(zip_ref.infolist(), desc="Filtering & Extracting"):
            # Skip directories
            if member.is_dir():
                continue
                
            target_class = get_target_class_from_path(member.filename)
            if target_class:
                # Extract file contents
                filename = os.path.basename(member.filename)
                if not filename:
                    continue
                    
                target_filepath = os.path.join(EXTRACT_DIR, target_class, filename)
                
                # Write file content directly
                with zip_ref.open(member) as source, open(target_filepath, "wb") as target:
                    target.write(source.read())
                    
                extracted_counts[target_class] += 1
                
    print("\nExtraction summary:")
    for cls, count in extracted_counts.items():
        print(f"  {cls}: {count} images extracted")
        
    # Remove ZIP file to save disk space
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print("Cleaned up downloaded ZIP archive.")


class PlantVillageDataset(Dataset):
    def __init__(self, file_paths: List[str], labels: List[int], transform=None):
        self.file_paths = file_paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path = self.file_paths[idx]
        # Open in RGB format
        image = Image.open(img_path).convert("RGB")
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
            
        return image, label


def get_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    """
    Returns train and val/test transforms for EfficientNet-B0.
    """
    # ImageNet normalization statistics
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])
    
    return train_transform, val_transform


def prepare_datasets(quick_run: bool = False) -> Tuple[Dataset, Dataset, Dict[int, str]]:
    """
    Prepares train and validation datasets.
    
    Args:
        quick_run: If True, returns a tiny dataset (e.g. 5 images per class) for rapid testing.
        
    Returns:
        Tuple of (train_dataset, val_dataset, class_mapping_idx_to_name)
    """
    # Ensure dataset is downloaded and extracted
    if not quick_run:
        download_and_extract_dataset()
    else:
        # For quick run, we just check if data exists; if not, we try to download a minimal amount
        # but to keep it simple, we run full extraction if nothing exists.
        download_and_extract_dataset()
        
    # Gather file paths and labels
    file_paths = []
    labels = []
    
    # Class names list to keep target index ordering consistent
    class_names = sorted(list(TARGET_CLASSES.keys()))
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    idx_to_class = {idx: name for idx, name in enumerate(class_names)}
    
    for class_name in class_names:
        class_dir = os.path.join(EXTRACT_DIR, class_name)
        if not os.path.exists(class_dir):
            continue
            
        class_files = [
            os.path.join(class_dir, f) for f in os.listdir(class_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        
        if quick_run:
            # Subsample to a maximum of 10 images per class
            class_files = class_files[:10]
            
        file_paths.extend(class_files)
        labels.extend([class_to_idx[class_name]] * len(class_files))
        
    if not file_paths:
        raise ValueError("No images found! Verify dataset extraction directory.")
        
    # Train / Val Split (80/20)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        file_paths, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    train_transform, val_transform = get_transforms()
    
    train_dataset = PlantVillageDataset(train_paths, train_labels, train_transform)
    val_dataset = PlantVillageDataset(val_paths, val_labels, val_transform)
    
    print(f"Dataset summary:")
    print(f"  Training samples: {len(train_dataset)}")
    print(f"  Validation samples: {len(val_dataset)}")
    print(f"  Number of classes: {len(class_names)}")
    
    return train_dataset, val_dataset, idx_to_class
