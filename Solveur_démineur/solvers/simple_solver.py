"""
Solveur simple avec règles AFN/AMN et probabilités naïves.

Approche baseline pour comparaison avec le solveur CSP.
Utilise uniquement des règles locales sans croiser les contraintes.
"""

from typing import Optional, Tuple, Dict, List
from collections import defaultdict
from game.board import Board, CellState
from solvers.base_solver import BaseSolver


class SimpleSolver(BaseSolver):
    """
    Solveur baseline utilisant des règles simples.
    
    Règles implémentées :
    - AFN (All Free Neighbors) : Si mines_restantes = 0 → toutes les cases voisines sont sûres
    - AMN (All Mines Neighbors) : Si mines_restantes = voisins_cachés → toutes sont des mines
    - Probabilités naïves : prob = mines_restantes / voisins_cachés (local, sans contraintes croisées)
    """
    
    def __init__(self, board: Board):
        """
        Initialise le solveur simple.
        
        Args:
            board: Grille de démineur
        """
        super().__init__(board)
        self.last_probabilities = {}
    
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """
        Calcule le prochain coup avec règles simples.
        
        Returns:
            Position (row, col) à révéler, ou None si impossible
        """
        # Première case : choisir une case centrale
        if self.board.first_click:
            return self._choose_first_cell()
        
        # Chercher les cases évidentes avec règles AFN/AMN
        safe_cells, mine_cells = self._apply_simple_rules()
        
        # Si des cases sûres sont trouvées, en choisir une
        if safe_cells:
            self.num_logical_deductions += 1
            self.last_probabilities = {pos: 0.0 for pos in safe_cells}
            return list(safe_cells)[0]
        
        # Marquer les mines trouvées
        for row, col in mine_cells:
            self.board.flag(row, col)
        
        # Calculer les probabilités naïves pour les cases restantes
        probabilities = self._calculate_naive_probabilities()
        self.last_probabilities = probabilities
        
        if not probabilities:
            # Aucune case cachée accessible, prendre n'importe quelle case cachée
            hidden = self.board.get_hidden_cells()
            if hidden:
                self.num_probability_guesses += 1
                return hidden[0]
            return None
        
        # Choisir la case avec la probabilité minimale
        self.num_probability_guesses += 1
        best_cell = min(probabilities.items(), key=lambda x: x[1])
        return best_cell[0]
    
    def get_probabilities(self) -> Dict[Tuple[int, int], float]:
        """
        Retourne les probabilités calculées lors du dernier coup.
        
        Returns:
            Dictionnaire {(row, col): probability}
        """
        return self.last_probabilities
    
    def _apply_simple_rules(self) -> Tuple[set, set]:
        """
        Applique les règles AFN et AMN.
        
        Returns:
            Tuple (safe_cells, mine_cells)
        """
        safe_cells = set()
        mine_cells = set()
        
        for row, col in self.board.get_revealed_cells():
            value = self.board.values[row, col]
            
            # Obtenir les voisins
            neighbors = self.board.get_neighbors(row, col)
            
            # Compter les mines déjà marquées
            flagged_count = sum(1 for nr, nc in neighbors 
                              if self.board.cell_states[nr, nc] == CellState.FLAGGED)
            
            # Compter les cases cachées
            hidden_neighbors = [(nr, nc) for nr, nc in neighbors 
                              if self.board.cell_states[nr, nc] == CellState.HIDDEN]
            
            if not hidden_neighbors:
                continue
            
            mines_remaining = value - flagged_count
            
            # Règle AFN : Toutes les cases voisines sont sûres
            if mines_remaining == 0:
                for pos in hidden_neighbors:
                    safe_cells.add(pos)
            
            # Règle AMN : Toutes les cases voisines sont des mines
            elif mines_remaining == len(hidden_neighbors):
                for pos in hidden_neighbors:
                    mine_cells.add(pos)
        
        return safe_cells, mine_cells
    
    def _calculate_naive_probabilities(self) -> Dict[Tuple[int, int], float]:
        """
        Calcule les probabilités naïves locales (sans contraintes croisées).
        
        Pour chaque case cachée, calcule la probabilité moyenne basée sur
        ses voisins révélés, SANS croiser les informations.
        
        Returns:
            Dictionnaire {(row, col): probability}
        """
        hidden_cells = self.board.get_hidden_cells()
        
        if not hidden_cells:
            return {}
        
        # Pour chaque case cachée, calculer la probabilité moyenne
        probabilities = {}
        
        for hidden_row, hidden_col in hidden_cells:
            # Trouver toutes les cases révélées voisines
            neighbors = self.board.get_neighbors(hidden_row, hidden_col)
            
            local_probs = []
            
            for nr, nc in neighbors:
                if self.board.cell_states[nr, nc] == CellState.REVEALED:
                    value = self.board.values[nr, nc]
                    
                    # Compter les mines déjà marquées autour de cette case révélée
                    cell_neighbors = self.board.get_neighbors(nr, nc)
                    flagged_count = sum(1 for cnr, cnc in cell_neighbors
                                      if self.board.cell_states[cnr, cnc] == CellState.FLAGGED)
                    
                    # Compter les cases cachées autour
                    hidden_count = sum(1 for cnr, cnc in cell_neighbors
                                     if self.board.cell_states[cnr, cnc] == CellState.HIDDEN)
                    
                    if hidden_count > 0:
                        mines_remaining = value - flagged_count
                        # Probabilité naïve locale
                        local_prob = max(0.0, min(1.0, mines_remaining / hidden_count))
                        local_probs.append(local_prob)
            
            if local_probs:
                # Moyenne des probabilités locales (approche naïve)
                probabilities[(hidden_row, hidden_col)] = sum(local_probs) / len(local_probs)
            else:
                # Aucune info, probabilité basée sur la densité globale
                total_hidden = len(hidden_cells)
                total_mines = self.board.num_mines
                flagged = sum(1 for r in range(self.board.height) for c in range(self.board.width)
                            if self.board.cell_states[r, c] == CellState.FLAGGED)
                mines_remaining = total_mines - flagged
                
                if total_hidden > 0:
                    probabilities[(hidden_row, hidden_col)] = mines_remaining / total_hidden
                else:
                    probabilities[(hidden_row, hidden_col)] = 0.5
        
        return probabilities
    
    def _choose_first_cell(self) -> Tuple[int, int]:
        """
        Choisit la première case à révéler.
        
        Returns:
            Position (row, col)
        """
        # Stratégie : choisir le centre
        center_row = self.board.height // 2
        center_col = self.board.width // 2
        return (center_row, center_col)
