"""
Construction de contraintes CSP pour le démineur.

Transforme l'état du jeu en un problème de satisfaction de contraintes.
"""

from typing import List, Tuple, Dict, Set
from game.board import Board, CellState


class Constraint:
    """Représente une contrainte de somme sur des variables."""
    
    def __init__(self, variables: List[Tuple[int, int]], total: int):
        """
        Initialise une contrainte.
        
        Args:
            variables: Liste des positions (row, col) des variables
            total: Somme attendue (nombre de mines)
        """
        self.variables = variables
        self.total = total
    
    def __repr__(self):
        return f"Constraint({len(self.variables)} vars, sum={self.total})"


class ConstraintBuilder:
    """Construit les contraintes CSP à partir de la grille."""
    
    def __init__(self, board: Board):
        """
        Initialise le constructeur de contraintes.
        
        Args:
            board: Grille de démineur
        """
        self.board = board
    
    def build_constraints(self) -> Tuple[List[Tuple[int, int]], List[Constraint]]:
        """
        Construit toutes les contraintes à partir de l'état actuel.
        
        Returns:
            Tuple (variables, constraints) où:
            - variables: Liste des cases inconnues (row, col)
            - constraints: Liste des contraintes
        """
        # Variables = cases cachées
        variables = self.board.get_hidden_cells()
        
        if not variables:
            return [], []
        
        # Contraintes à partir des cases révélées
        constraints = []
        
        for row, col in self.board.get_revealed_cells():
            value = self.board.values[row, col]
            
            # Trouver les voisins cachés
            hidden_neighbors = []
            for nr, nc in self.board.get_neighbors(row, col):
                if self.board.cell_states[nr, nc] == CellState.HIDDEN:
                    hidden_neighbors.append((nr, nc))
            
            # Compter les mines déjà marquées (drapeaux)
            flagged_count = 0
            for nr, nc in self.board.get_neighbors(row, col):
                if self.board.cell_states[nr, nc] == CellState.FLAGGED:
                    flagged_count += 1
            
            # Créer la contrainte si nécessaire
            if hidden_neighbors:
                remaining_mines = value - flagged_count
                constraint = Constraint(hidden_neighbors, remaining_mines)
                constraints.append(constraint)
        
        return variables, constraints
    
    def build_global_constraint(self, variables: List[Tuple[int, int]]) -> Constraint:
        """
        Construit la contrainte globale sur le nombre total de mines.
        
        Args:
            variables: Liste des variables (cases inconnues)
            
        Returns:
            Contrainte globale
        """
        # Compter les mines déjà révélées ou marquées
        revealed_mines = 0
        for r in range(self.board.height):
            for c in range(self.board.width):
                if self.board.cell_states[r, c] == CellState.REVEALED and self.board.mines[r, c]:
                    revealed_mines += 1
                elif self.board.cell_states[r, c] == CellState.FLAGGED:
                    revealed_mines += 1
        
        remaining_mines = self.board.num_mines - revealed_mines
        return Constraint(variables, remaining_mines)
    
    def simplify_constraints(self, variables: List[Tuple[int, int]], 
                           constraints: List[Constraint]) -> Tuple[List[Tuple[int, int]], List[Constraint], 
                                                                   Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """
        Simplifie les contraintes et détecte les cases évidentes.
        
        Args:
            variables: Liste des variables
            constraints: Liste des contraintes
            
        Returns:
            Tuple (new_variables, new_constraints, certain_mines, certain_safe):
            - new_variables: Variables restantes après simplification
            - new_constraints: Contraintes restantes
            - certain_mines: Cases qui sont certainement des mines
            - certain_safe: Cases qui sont certainement sûres
        """
        certain_mines = set()
        certain_safe = set()
        
        changed = True
        while changed:
            changed = False
            
            for constraint in constraints[:]:
                # Tous les voisins sont des mines (AFN - All Free Neighbors)
                if constraint.total == len(constraint.variables):
                    for var in constraint.variables:
                        if var not in certain_mines:
                            certain_mines.add(var)
                            changed = True
                
                # Aucun voisin n'est une mine (AMN - All Mines Neighbors)
                elif constraint.total == 0:
                    for var in constraint.variables:
                        if var not in certain_safe:
                            certain_safe.add(var)
                            changed = True
        
        # Retirer les variables certaines
        new_variables = [v for v in variables if v not in certain_mines and v not in certain_safe]
        
        # Mettre à jour les contraintes
        new_constraints = []
        for constraint in constraints:
            new_vars = [v for v in constraint.variables if v not in certain_mines and v not in certain_safe]
            new_total = constraint.total - sum(1 for v in constraint.variables if v in certain_mines)
            
            if new_vars:
                new_constraints.append(Constraint(new_vars, new_total))
        
        return new_variables, new_constraints, certain_mines, certain_safe
