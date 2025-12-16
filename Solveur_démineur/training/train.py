"""
Script d'entraînement du modèle CNN pour le démineur.

Optimisé pour RTX 3060 avec support CUDA et mixed precision training.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.cuda.amp import GradScaler, autocast
import numpy as np
import pickle
import os
import sys

# Ajouter le dossier racine au path pour permettre les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Tuple
from tqdm import tqdm
import matplotlib.pyplot as plt
from training.model import create_model, count_parameters


class MinesweeperDataset(Dataset):
    """Dataset PyTorch pour l'entraînement."""
    
    def __init__(self, examples: List[Dict], height: int, width: int):
        """
        Initialise le dataset.
        
        Args:
            examples: Liste d'exemples {state, move, probabilities}
            height: Hauteur de la grille
            width: Largeur de la grille
        """
        self.examples = examples
        self.height = height
        self.width = width
    
    def __len__(self) -> int:
        return len(self.examples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Récupère un exemple.
        
        Returns:
            Tuple (state, target_move, valid_mask)
        """
        example = self.examples[idx]
        
        # État (4, H, W)
        state = torch.from_numpy(example['state']).float()
        
        # Coup cible (position linéarisée)
        move = example['move']
        target = move[0] * self.width + move[1]
        target = torch.tensor(target, dtype=torch.long)
        
        # Masque des coups valides (H, W)
        # Cases cachées = valides
        valid_mask = (state[1, :, :] == 0).float()  # Channel 1 = masque révélé
        
        return state, target, valid_mask


def load_datasets(data_dir: str = "training/data") -> Dict[str, List[Dict]]:
    """
    Charge tous les datasets.
    
    Args:
        data_dir: Dossier des données
        
    Returns:
        Dictionnaire {difficulty: examples}
    """
    datasets = {}
    
    files = {
        'easy': 'dataset_easy.pkl',
        'medium': 'dataset_medium.pkl',
        'hard': 'dataset_hard.pkl'
    }
    
    for difficulty, filename in files.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            datasets[difficulty] = data
            print(f"📂 {difficulty}: {len(data)} exemples")
        else:
            print(f"⚠️  {filepath} non trouvé")
    
    return datasets


def create_dataloaders(
    examples: List[Dict],
    height: int,
    width: int,
    batch_size: int = 64,
    train_split: float = 0.8
) -> Tuple[DataLoader, DataLoader]:
    """
    Crée les dataloaders train/val.
    
    Args:
        examples: Liste d'exemples
        height: Hauteur grille
        width: Largeur grille
        batch_size: Taille des batchs
        train_split: Proportion du train
        
    Returns:
        Tuple (train_loader, val_loader)
    """
    # Mélanger et diviser
    np.random.shuffle(examples)
    split_idx = int(len(examples) * train_split)
    
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]
    
    # Créer datasets
    train_dataset = MinesweeperDataset(train_examples, height, width)
    val_dataset = MinesweeperDataset(val_examples, height, width)
    
    # Créer dataloaders avec pin_memory pour GPU
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,  # Paralléliser le chargement
        pin_memory=True  # Optimisation pour GPU
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    
    return train_loader, val_loader


class Trainer:
    """Entraîneur pour le modèle CNN."""
    
    def __init__(
        self,
        model: nn.Module,
        device: torch.device,
        learning_rate: float = 0.001,
        use_amp: bool = True
    ):
        """
        Initialise l'entraîneur.
        
        Args:
            model: Modèle à entraîner
            device: Device (cuda/cpu)
            learning_rate: Taux d'apprentissage
            use_amp: Utiliser mixed precision (pour GPU)
        """
        self.model = model.to(device)
        self.device = device
        self.use_amp = use_amp and device.type == 'cuda'
        
        # Optimizer Adam avec weight decay
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4
        )
        
        # Scheduler pour réduire le LR
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=3
        )
        
        # Loss function: CrossEntropy pour classification
        self.criterion = nn.CrossEntropyLoss()
        
        # GradScaler pour mixed precision
        self.scaler = GradScaler() if self.use_amp else None
        
        # Historique
        self.train_losses = []
        self.val_losses = []
        self.val_accuracies = []
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """
        Entraîne pour une epoch.
        
        Args:
            train_loader: DataLoader d'entraînement
            
        Returns:
            Loss moyenne
        """
        self.model.train()
        total_loss = 0
        
        pbar = tqdm(train_loader, desc="Training")
        for states, targets, masks in pbar:
            # Déplacer sur GPU
            states = states.to(self.device)
            targets = targets.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Forward avec mixed precision si disponible
            if self.use_amp:
                with autocast():
                    outputs = self.model(states)
                    loss = self.criterion(outputs, targets)
                
                # Backward avec scaler
                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(states)
                loss = self.criterion(outputs, targets)
                loss.backward()
                self.optimizer.step()
            
            total_loss += loss.item()
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        return total_loss / len(train_loader)
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """
        Valide le modèle.
        
        Args:
            val_loader: DataLoader de validation
            
        Returns:
            Tuple (loss, accuracy)
        """
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for states, targets, masks in tqdm(val_loader, desc="Validation"):
                states = states.to(self.device)
                targets = targets.to(self.device)
                masks = masks.to(self.device)
                
                outputs = self.model(states)
                loss = self.criterion(outputs, targets)
                
                total_loss += loss.item()
                
                # Calculer accuracy
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()
        
        avg_loss = total_loss / len(val_loader)
        accuracy = 100.0 * correct / total
        
        return avg_loss, accuracy
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 50,
        save_path: str = "training/models"
    ):
        """
        Boucle d'entraînement complète.
        
        Args:
            train_loader: DataLoader d'entraînement
            val_loader: DataLoader de validation
            num_epochs: Nombre d'époques
            save_path: Dossier de sauvegarde
        """
        os.makedirs(save_path, exist_ok=True)
        best_val_loss = float('inf')
        
        print(f"\n🚀 Début de l'entraînement ({num_epochs} époques)")
        print(f"Device: {self.device}")
        print(f"Mixed Precision: {self.use_amp}")
        print(f"Paramètres: {count_parameters(self.model):,}\n")
        
        for epoch in range(num_epochs):
            print(f"\n{'='*60}")
            print(f"Epoch {epoch+1}/{num_epochs}")
            print(f"{'='*60}")
            
            # Entraînement
            train_loss = self.train_epoch(train_loader)
            self.train_losses.append(train_loss)
            
            # Validation
            val_loss, val_acc = self.validate(val_loader)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)
            
            # Scheduler
            self.scheduler.step(val_loss)
            
            # Affichage
            print(f"\n📊 Résultats:")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss:   {val_loss:.4f}")
            print(f"  Val Acc:    {val_acc:.2f}%")
            
            # Sauvegarder le meilleur modèle
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                model_path = os.path.join(save_path, 'best_model.pth')
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_loss,
                    'val_acc': val_acc
                }, model_path)
                print(f"  ✅ Meilleur modèle sauvegardé!")
        
        print(f"\n{'='*60}")
        print(f"✅ Entraînement terminé!")
        print(f"Meilleure Val Loss: {best_val_loss:.4f}")
        print(f"{'='*60}\n")
        
        # Sauvegarder les courbes
        self.plot_training_curves(save_path)
    
    def plot_training_curves(self, save_path: str):
        """
        Trace et sauvegarde les courbes d'apprentissage.
        
        Args:
            save_path: Dossier de sauvegarde
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss
        ax1.plot(self.train_losses, label='Train')
        ax1.plot(self.val_losses, label='Validation')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Accuracy
        ax2.plot(self.val_accuracies, label='Validation', color='green')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.set_title('Validation Accuracy')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(save_path, 'training_curves.png'), dpi=150)
        print(f"📈 Courbes sauvegardées: {save_path}/training_curves.png")


def train_model(
    difficulty: str = 'medium',
    model_type: str = 'cnn',
    batch_size: int = 64,
    num_epochs: int = 50,
    learning_rate: float = 0.001
):
    """
    Fonction principale d'entraînement.
    
    Args:
        difficulty: 'easy', 'medium', ou 'hard'
        model_type: 'cnn' ou 'resnet'
        batch_size: Taille des batchs
        num_epochs: Nombre d'époques
        learning_rate: Taux d'apprentissage
    """
    # Configuration
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Dimensions selon difficulté
    dimensions = {
        'easy': (9, 9),
        'medium': (16, 16),
        'hard': (30, 16)
    }
    height, width = dimensions[difficulty]
    
    # Charger données
    print(f"\n🎮 Entraînement - Difficulté: {difficulty.upper()}")
    datasets = load_datasets()
    
    if difficulty not in datasets:
        print(f"❌ Dataset {difficulty} non trouvé!")
        return
    
    examples = datasets[difficulty]
    
    # Créer dataloaders
    train_loader, val_loader = create_dataloaders(
        examples, height, width, batch_size
    )
    
    print(f"\n📊 Dataset:")
    print(f"  Train: {len(train_loader.dataset)} exemples")
    print(f"  Val:   {len(val_loader.dataset)} exemples")
    print(f"  Batch size: {batch_size}")
    
    # Créer modèle
    model = create_model(model_type, height, width)
    
    # Entraîner
    trainer = Trainer(model, device, learning_rate, use_amp=True)
    trainer.train(train_loader, val_loader, num_epochs, 
                  save_path=f"training/models/{difficulty}_{model_type}")


if __name__ == "__main__":
    # Entraîner sur niveau intermédiaire
    train_model(
        difficulty='medium',
        model_type='cnn',
        batch_size=64,
        num_epochs=50,
        learning_rate=0.001
    )
