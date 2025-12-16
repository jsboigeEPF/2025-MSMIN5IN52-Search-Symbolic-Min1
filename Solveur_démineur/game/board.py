"""
Classe Board - Logique du jeu de démineur.

Gère la grille, la génération des mines, la révélation des cases,
et la détection de fin de partie.
"""

import numpy as np
from typing import Tuple, Set, List
from enum import Enum


class CellState(Enum):
    """États possibles d'une case."""
    HIDDEN = 0
    REVEALED = 1
    FLAGGED = 2


class GameState(Enum):
    """États possibles du jeu."""
    ONGOING = 0
    WON = 1
    LOST = 2


class Board:
    """Représente une grille de démineur."""
    
    def __init__(self, width: int, height: int, num_mines: int, seed: int = None):
        """
        Initialise une grille de démineur.
        
        Args:
            width: Largeur de la grille
            height: Hauteur de la grille
            num_mines: Nombre de mines
            seed: Seed pour la génération aléatoire (reproductibilité)
        """
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.seed = seed
        
        # Grille des mines (True = mine)
        self.mines = np.zeros((height, width), dtype=bool)
        
        # État des cases (HIDDEN, REVEALED, FLAGGED)
        self.cell_states = np.full((height, width), CellState.HIDDEN)
        
        # Valeurs des cases (nombre de mines adjacentes)
        self.values = np.zeros((height, width), dtype=int)
        
        # État du jeu
        self.game_state = GameState.ONGOING
        
        # Statistiques
        self.num_revealed = 0
        self.first_click = True
        
    def generate_mines(self, safe_row: int, safe_col: int):
        """
        Génère les mines en évitant la case cliquée et ses voisins.
        
        Args:
            safe_row: Ligne de la case sûre
            safe_col: Colonne de la case sûre
        """
        if self.seed is not None:
            np.random.seed(self.seed)
        
        # Cases à éviter (case cliquée + voisins)
        safe_cells = set()
        safe_cells.add((safe_row, safe_col))
        for dr, dc in self._get_neighbor_offsets():
            nr, nc = safe_row + dr, safe_col + dc
            if self._is_valid(nr, nc):
                safe_cells.add((nr, nc))
        
        # Toutes les cases possibles
        all_cells = [(r, c) for r in range(self.height) for c in range(self.width)]
        available_cells = [cell for cell in all_cells if cell not in safe_cells]
        
        # Placer les mines aléatoirement
        mine_positions = np.random.choice(len(available_cells), self.num_mines, replace=False)
        for idx in mine_positions:
            r, c = available_cells[idx]
            self.mines[r, c] = True
        
        # Calculer les valeurs (nombre de mines adjacentes)
        self._calculate_values()
    
    def _calculate_values(self):
        """Calcule le nombre de mines adjacentes pour chaque case."""
        for r in range(self.height):
            for c in range(self.width):
                if not self.mines[r, c]:
                    count = 0
                    for dr, dc in self._get_neighbor_offsets():
                        nr, nc = r + dr, c + dc
                        if self._is_valid(nr, nc) and self.mines[nr, nc]:
                            count += 1
                    self.values[r, c] = count
    
    def reveal(self, row: int, col: int) -> bool:
        """
        Révèle une case.
        
        Args:
            row: Ligne de la case
            col: Colonne de la case
            
        Returns:
            True si la révélation réussit, False si mine
        """
        if not self._is_valid(row, col):
            return False
        
        if self.cell_states[row, col] != CellState.HIDDEN:
            return True  # Déjà révélée ou marquée
        
        # Première case cliquée : générer les mines
        if self.first_click:
            self.generate_mines(row, col)
            self.first_click = False
        
        # Mine touchée
        if self.mines[row, col]:
            self.cell_states[row, col] = CellState.REVEALED
            self.game_state = GameState.LOST
            return False
        
        # Révéler la case
        self._reveal_recursive(row, col)
        
        # Vérifier la victoire
        self._check_win()
        
        return True
    
    def _reveal_recursive(self, row: int, col: int):
        """Révèle récursivement les cases vides (flood fill)."""
        if not self._is_valid(row, col):
            return
        
        if self.cell_states[row, col] != CellState.HIDDEN:
            return
        
        if self.mines[row, col]:
            return
        
        # Révéler cette case
        self.cell_states[row, col] = CellState.REVEALED
        self.num_revealed += 1
        
        # Si case vide (0 mines autour), révéler les voisins
        if self.values[row, col] == 0:
            for dr, dc in self._get_neighbor_offsets():
                self._reveal_recursive(row + dr, col + dc)
    
    def flag(self, row: int, col: int):
        """Marque/démarque une case avec un drapeau."""
        if not self._is_valid(row, col):
            return
        
        if self.cell_states[row, col] == CellState.HIDDEN:
            self.cell_states[row, col] = CellState.FLAGGED
        elif self.cell_states[row, col] == CellState.FLAGGED:
            self.cell_states[row, col] = CellState.HIDDEN
    
    def _check_win(self):
        """Vérifie si le joueur a gagné."""
        # Victoire = toutes les cases non-mines révélées
        total_safe_cells = self.width * self.height - self.num_mines
        if self.num_revealed == total_safe_cells:
            self.game_state = GameState.WON
    
    def get_hidden_cells(self) -> List[Tuple[int, int]]:
        """Retourne la liste des cases cachées."""
        hidden = []
        for r in range(self.height):
            for c in range(self.width):
                if self.cell_states[r, c] == CellState.HIDDEN:
                    hidden.append((r, c))
        return hidden
    
    def get_revealed_cells(self) -> List[Tuple[int, int]]:
        """Retourne la liste des cases révélées."""
        revealed = []
        for r in range(self.height):
            for c in range(self.width):
                if self.cell_states[r, c] == CellState.REVEALED:
                    revealed.append((r, c))
        return revealed
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Retourne les voisins valides d'une case."""
        neighbors = []
        for dr, dc in self._get_neighbor_offsets():
            nr, nc = row + dr, col + dc
            if self._is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors
    
    def _get_neighbor_offsets(self) -> List[Tuple[int, int]]:
        """Retourne les offsets des 8 voisins."""
        return [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
    
    def _is_valid(self, row: int, col: int) -> bool:
        """Vérifie si une position est valide."""
        return 0 <= row < self.height and 0 <= col < self.width
    
    def is_game_over(self) -> bool:
        """Vérifie si le jeu est terminé."""
        return self.game_state != GameState.ONGOING
    
    def __repr__(self):
        """Représentation textuelle de la grille."""
        result = []
        for r in range(self.height):
            row = []
            for c in range(self.width):
                if self.cell_states[r, c] == CellState.HIDDEN:
                    row.append('?')
                elif self.cell_states[r, c] == CellState.FLAGGED:
                    row.append('F')
                elif self.mines[r, c]:
                    row.append('*')
                else:
                    row.append(str(self.values[r, c]))
            result.append(' '.join(row))
        return '\n'.join(result)
