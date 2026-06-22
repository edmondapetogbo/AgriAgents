import os
import json
import argparse
from typing import Dict
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
from sklearn.metrics import precision_recall_fscore_support

from model.config import (
    BATCH_SIZE,
    LEARNING_RATE,
    NUM_EPOCHS,
    MODEL_PATH,
    CLASS_MAPPING_PATH,
    TARGET_CLASSES
)
from model.dataset import prepare_datasets
from model.model import get_efficientnet_model

def get_device() -> torch.device:
    """
    Returns the appropriate acceleration device (MPS, CUDA, or CPU).
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

def save_class_mapping(idx_to_class: Dict[int, str]) -> None:
    """
    Saves the class mapping dictionary to a JSON file.
    """
    # Create the mapping mapping idx -> name and crop/disease detail
    mapping = {}
    for idx, class_name in idx_to_class.items():
        class_info = TARGET_CLASSES.get(class_name, {"crop": "Unknown", "disease": "Unknown"})
        mapping[str(idx)] = {
            "class_name": class_name,
            "crop": class_info["crop"],
            "disease": class_info["disease"]
        }
        
    os.makedirs(os.path.dirname(CLASS_MAPPING_PATH), exist_ok=True)
    with open(CLASS_MAPPING_PATH, "w") as f:
        json.dump(mapping, f, indent=4)
    print(f"Saved class mapping to {CLASS_MAPPING_PATH}")

def train_one_epoch(
    model: nn.Module, 
    dataloader: DataLoader, 
    criterion: nn.Module, 
    optimizer: optim.Optimizer, 
    device: torch.device
) -> tuple[float, float]:
    """
    Trains the model for one epoch.
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    progress_bar = tqdm(dataloader, desc="Training")
    for images, labels in progress_bar:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        progress_bar.set_postfix({
            "loss": f"{loss.item():.4f}", 
            "accuracy": f"{100.0 * correct / total:.2f}%"
        })
        
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

@torch.no_grad()
def validate(
    model: nn.Module, 
    dataloader: DataLoader, 
    criterion: nn.Module, 
    device: torch.device
) -> tuple[float, float, float, float]:
    """
    Validates the model and computes validation metrics.
    """
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    all_preds = []
    all_labels = []
    
    for images, labels in tqdm(dataloader, desc="Validating"):
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        
    val_loss = running_loss / total
    val_acc = correct / total
    
    # Compute precision and recall using sklearn
    precision, recall, _, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='weighted', zero_division=0
    )
    
    return val_loss, val_acc, float(precision), float(recall)

def main():
    parser = argparse.ArgumentParser(description="Train EfficientNet-B0 on PlantVillage dataset subset")
    parser.add_argument("--quick-run", action="store_true", help="Run a fast demo/debug execution on small subset of data")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Input batch size")
    parser.add_argument("--lr", type=float, default=LEARNING_RATE, help="Learning rate")
    args = parser.parse_args()
    
    device = get_device()
    print(f"Using device: {device}")
    
    # Load and split datasets
    train_dataset, val_dataset, idx_to_class = prepare_datasets(quick_run=args.quick_run)
    save_class_mapping(idx_to_class)
    
    # Dataloaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=args.batch_size, 
        shuffle=True, 
        num_workers=0 if device.type == "mps" or args.quick_run else 2,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=args.batch_size, 
        shuffle=False, 
        num_workers=0 if device.type == "mps" or args.quick_run else 2,
        pin_memory=True
    )
    
    # Model configuration
    num_classes = len(idx_to_class)
    model = get_efficientnet_model(num_classes=num_classes, pretrained=not args.quick_run)
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=2, factor=0.1)
    
    best_val_loss = float("inf")
    
    epochs = 1 if args.quick_run else args.epochs
    print(f"Starting training for {epochs} epochs...")
    
    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")
        
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, precision, recall = validate(model, val_loader, criterion, device)
        
        scheduler.step(val_loss)
        
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}%")
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc*100:.2f}% | Precision: {precision*100:.2f}% | Recall: {recall*100:.2f}%")
        
        # Save checkpoint if validation loss improves
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            torch.save(model.state_dict(), MODEL_PATH)
            print(f"Saved best model checkpoint to {MODEL_PATH}")
            
    print("\nTraining completed successfully!")

if __name__ == "__main__":
    main()
