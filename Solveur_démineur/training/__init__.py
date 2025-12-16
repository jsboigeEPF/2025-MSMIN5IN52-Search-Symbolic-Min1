"""
Module d'entraînement pour le solveur supervisé.

Ce module contient:
- generate_dataset.py: Génération de datasets d'apprentissage
- model.py: Architectures CNN pour prédire les coups
- train.py: Pipeline d'entraînement optimisé GPU
"""

from .model import MinesweeperCNN, MinesweeperResNet, create_model
from .generate_dataset import DatasetGenerator

__all__ = [
    'MinesweeperCNN',
    'MinesweeperResNet',
    'create_model',
    'DatasetGenerator'
]
