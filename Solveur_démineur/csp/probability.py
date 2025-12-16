"""
Calcul de probabilités exactes pour le démineur.

Énumère toutes les solutions possibles d'un CSP et calcule
la probabilité qu'une case contienne une mine.
"""

from typing import List, Dict, Tuple, Set
from collections import defaultdict


class ProbabilityCalculator:
    """Calcule les probabilités exactes à partir des solutions d'un CSP."""
    
    @staticmethod
    def calculate_probabilities(variables: List[Tuple[int, int]], 
                               solutions: List[Dict[Tuple[int, int], int]]) -> Dict[Tuple[int, int], float]:
        """
        Calcule la probabilité que chaque variable soit une mine.
        
        Args:
            variables: Liste des variables (positions)
            solutions: Liste des solutions (assignations valides)
            
        Returns:
            Dictionnaire {position: probabilité}
        """
        if not solutions:
            # Aucune solution trouvée, probabilité uniforme
            return {var: 0.5 for var in variables}
        
        # Compter combien de fois chaque variable est une mine
        mine_counts = defaultdict(int)
        
        for solution in solutions:
            for var, value in solution.items():
                if value == 1:  # Mine
                    mine_counts[var] += 1
        
        # Calculer les probabilités
        num_solutions = len(solutions)
        probabilities = {}
        
        for var in variables:
            probabilities[var] = mine_counts[var] / num_solutions
        
        return probabilities
    
    @staticmethod
    def find_best_move(probabilities: Dict[Tuple[int, int], float]) -> Tuple[int, int]:
        """
        Trouve la meilleure case à révéler (probabilité minimale).
        
        Args:
            probabilities: Dictionnaire {position: probabilité}
            
        Returns:
            Position (row, col) de la meilleure case
        """
        if not probabilities:
            return None
        
        # Choisir la case avec la probabilité la plus faible
        best_cell = min(probabilities.items(), key=lambda x: x[1])
        return best_cell[0]
    
    @staticmethod
    def get_certain_cells(probabilities: Dict[Tuple[int, int], float], 
                         threshold: float = 0.0001) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """
        Identifie les cases certaines (probabilité 0 ou 1).
        
        Args:
            probabilities: Dictionnaire {position: probabilité}
            threshold: Seuil pour considérer une probabilité comme 0 ou 1
            
        Returns:
            Tuple (certain_safe, certain_mines)
        """
        certain_safe = set()
        certain_mines = set()
        
        for pos, prob in probabilities.items():
            if prob <= threshold:
                certain_safe.add(pos)
            elif prob >= 1.0 - threshold:
                certain_mines.add(pos)
        
        return certain_safe, certain_mines
