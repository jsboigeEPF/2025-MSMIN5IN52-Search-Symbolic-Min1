"""
Modèle CNN pour l'apprentissage supervisé du démineur.

Architecture optimisée pour RTX 3060 avec support CUDA.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class MinesweeperCNN(nn.Module):
    """
    CNN pour prédire les meilleurs coups au démineur.
    
    Architecture:
    - Input: (batch, 4, H, W) - 4 channels (valeurs, masque, drapeaux, frontière)
    - Plusieurs couches convolutives pour extraire patterns locaux
    - Couches fully-connected pour décision globale
    - Output: (batch, H*W) - probabilité que chaque case soit le meilleur coup
    """
    
    def __init__(self, height: int = 16, width: int = 16):
        """
        Initialise le réseau.
        
        Args:
            height: Hauteur de la grille
            width: Largeur de la grille
        """
        super(MinesweeperCNN, self).__init__()
        
        self.height = height
        self.width = width
        
        # Bloc 1: Extraction features de bas niveau
        self.conv1 = nn.Conv2d(4, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        
        # Bloc 2: Features intermédiaires
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        
        # Bloc 3: Features de plus haut niveau
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        # Bloc 4: Raffiner les patterns
        self.conv4 = nn.Conv2d(128, 64, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(64)
        
        # Bloc 5: Prédiction finale par case
        self.conv5 = nn.Conv2d(64, 32, kernel_size=1)
        self.bn5 = nn.BatchNorm2d(32)
        
        # Sortie: 1 canal = score par case
        self.output = nn.Conv2d(32, 1, kernel_size=1)
        
        # Dropout pour régularisation
        self.dropout = nn.Dropout2d(p=0.2)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Tensor (batch, 4, H, W)
            
        Returns:
            Tensor (batch, H*W) avec scores pour chaque case
        """
        # Bloc 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        
        # Bloc 2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Bloc 3
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        
        # Bloc 4
        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Bloc 5
        x = self.conv5(x)
        x = self.bn5(x)
        x = F.relu(x)
        
        # Output
        x = self.output(x)  # (batch, 1, H, W)
        
        # Flatten spatial dimensions
        batch_size = x.size(0)
        x = x.view(batch_size, -1)  # (batch, H*W)
        
        return x
    
    def predict_move(self, state: torch.Tensor, valid_moves: torch.Tensor = None) -> Tuple[int, int]:
        """
        Prédit le meilleur coup pour un état donné.
        
        Args:
            state: Tensor (4, H, W) - état de la grille
            valid_moves: Tensor (H, W) optionnel - masque des coups valides
            
        Returns:
            Tuple (row, col) du meilleur coup
        """
        self.eval()
        with torch.no_grad():
            # Ajouter dimension batch
            if state.dim() == 3:
                state = state.unsqueeze(0)  # (1, 4, H, W)
            
            # Forward
            scores = self.forward(state)  # (1, H*W)
            scores = scores.squeeze(0)  # (H*W,)
            
            # Appliquer masque si fourni
            if valid_moves is not None:
                valid_mask = valid_moves.view(-1)  # (H*W,)
                scores = scores * valid_mask + (1 - valid_mask) * (-1e9)
            
            # Trouver le meilleur coup
            best_idx = scores.argmax().item()
            row = best_idx // self.width
            col = best_idx % self.width
            
            return (row, col)


class MinesweeperResNet(nn.Module):
    """
    Variante avec blocs résiduels pour captures de patterns plus complexes.
    Plus lourd mais potentiellement plus performant.
    """
    
    def __init__(self, height: int = 16, width: int = 16):
        """
        Initialise le ResNet.
        
        Args:
            height: Hauteur de la grille
            width: Largeur de la grille
        """
        super(MinesweeperResNet, self).__init__()
        
        self.height = height
        self.width = width
        
        # Première couche
        self.conv1 = nn.Conv2d(4, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        
        # Blocs résiduels
        self.res_block1 = ResidualBlock(64, 64)
        self.res_block2 = ResidualBlock(64, 128, stride=1)
        self.res_block3 = ResidualBlock(128, 128)
        self.res_block4 = ResidualBlock(128, 64, stride=1)
        
        # Sortie
        self.output = nn.Conv2d(64, 1, kernel_size=1)
        
        self.dropout = nn.Dropout2d(p=0.3)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        
        x = self.res_block1(x)
        x = self.dropout(x)
        
        x = self.res_block2(x)
        x = self.res_block3(x)
        x = self.dropout(x)
        
        x = self.res_block4(x)
        
        x = self.output(x)
        
        batch_size = x.size(0)
        x = x.view(batch_size, -1)
        
        return x
    
    def predict_move(self, state: torch.Tensor, valid_moves: torch.Tensor = None) -> Tuple[int, int]:
        """Prédit le meilleur coup."""
        self.eval()
        with torch.no_grad():
            if state.dim() == 3:
                state = state.unsqueeze(0)
            
            scores = self.forward(state).squeeze(0)
            
            if valid_moves is not None:
                valid_mask = valid_moves.view(-1)
                scores = scores * valid_mask + (1 - valid_mask) * (-1e9)
            
            best_idx = scores.argmax().item()
            row = best_idx // self.width
            col = best_idx % self.width
            
            return (row, col)


class ResidualBlock(nn.Module):
    """Bloc résiduel pour le ResNet."""
    
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        """
        Initialise le bloc résiduel.
        
        Args:
            in_channels: Canaux d'entrée
            out_channels: Canaux de sortie
            stride: Stride pour la convolution
        """
        super(ResidualBlock, self).__init__()
        
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, 
                               stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3,
                               stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        # Shortcut connection
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, 
                         stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass du bloc résiduel."""
        identity = x
        
        out = self.conv1(x)
        out = self.bn1(out)
        out = F.relu(out)
        
        out = self.conv2(out)
        out = self.bn2(out)
        
        out += self.shortcut(identity)
        out = F.relu(out)
        
        return out


def create_model(model_type: str = 'cnn', height: int = 16, width: int = 16) -> nn.Module:
    """
    Factory pour créer un modèle.
    
    Args:
        model_type: 'cnn' ou 'resnet'
        height: Hauteur de la grille
        width: Largeur de la grille
        
    Returns:
        Modèle PyTorch
    """
    if model_type == 'resnet':
        return MinesweeperResNet(height, width)
    else:
        return MinesweeperCNN(height, width)


def count_parameters(model: nn.Module) -> int:
    """
    Compte le nombre de paramètres entraînables.
    
    Args:
        model: Modèle PyTorch
        
    Returns:
        Nombre de paramètres
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test du modèle
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  Device: {device}")
    
    # Modèle CNN
    model_cnn = create_model('cnn', 16, 16).to(device)
    print(f"\n📊 CNN - Paramètres: {count_parameters(model_cnn):,}")
    
    # Test forward
    dummy_input = torch.randn(8, 4, 16, 16).to(device)
    output = model_cnn(dummy_input)
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    
    # Modèle ResNet
    model_resnet = create_model('resnet', 16, 16).to(device)
    print(f"\n📊 ResNet - Paramètres: {count_parameters(model_resnet):,}")
    
    output_resnet = model_resnet(dummy_input)
    print(f"Output shape: {output_resnet.shape}")
