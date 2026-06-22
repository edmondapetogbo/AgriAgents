import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

def get_efficientnet_model(num_classes: int = 12, pretrained: bool = True) -> nn.Module:
    """
    Initializes an EfficientNet-B0 model with a custom classifier head.
    
    Args:
        num_classes: The number of output classes.
        pretrained: If True, loads ImageNet-pretrained weights.
        
    Returns:
        nn.Module: The configured PyTorch model.
    """
    # Load pretrained weights or uninitialized model
    weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = efficientnet_b0(weights=weights)
    
    # EfficientNet-B0's classifier is:
    # (classifier): Sequential(
    #   (0): Dropout(p=0.2, inplace=True)
    #   (1): Linear(in_features=1280, out_features=1000, bias=True)
    # )
    in_features = model.classifier[1].in_features
    
    # Replace the linear layer with our custom output size
    model.classifier[1] = nn.Linear(in_features, num_classes)
    
    return model

if __name__ == "__main__":
    # Test model shape instantiation
    test_model = get_efficientnet_model(num_classes=12, pretrained=False)
    test_input = torch.randn(1, 3, 224, 224)
    test_output = test_model(test_input)
    print(f"Model successfully created. Input shape: {test_input.shape}, Output shape: {test_output.shape}")
