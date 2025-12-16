"""
Classe abstraite pour tous les solveurs de démineur.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict
from game.board import Board


class BaseSolver(ABC):
    """Classe de base pour tous les solveurs."""
    
    def __init__(self, board: Board):
        """
        Initialise le solveur.
        
        Args:
            board: Grille de démineur à résoudre
        """
        self.board = board
        self.num_moves = 0
        self.num_logical_deductions = 0
        self.num_probability_guesses = 0
    
    @abstractmethod
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """
        Calcule le prochain coup à jouer.
        
        Returns:
            Tuple (row, col) de la case à révéler, ou None si aucun coup possible
        """
        pass
    
    @abstractmethod
    def get_probabilities(self) -> Dict[Tuple[int, int], float]:
        """
        Calcule les probabilités pour toutes les cases cachées.
        
        Returns:
            Dictionnaire {(row, col): probability}
        """
        pass
    
    def make_move(self, row: int, col: int) -> bool:
        """
        Effectue un mouvement sur la grille.
        
        Args:
            row: Ligne de la case
            col: Colonne de la case
            
        Returns:
            True si le coup est sûr, False si mine
        """
        self.num_moves += 1
        return self.board.reveal(row, col)
    
    def reset_stats(self):
        """Réinitialise les statistiques."""
        self.num_moves = 0
        self.num_logical_deductions = 0
        self.num_probability_guesses = 0
    
    def get_stats(self) -> Dict[str, int]:
        """
        Retourne les statistiques du solveur.
        
        Returns:
            Dictionnaire des statistiques
        """
        return {
            'num_moves': self.num_moves,
            'num_logical_deductions': self.num_logical_deductions,
            'num_probability_guesses': self.num_probability_guesses
        }
