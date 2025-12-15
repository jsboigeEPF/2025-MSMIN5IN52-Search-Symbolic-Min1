# -*- coding: utf-8 -*-
"""
Représentation de la grille de mots-croisés.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict

from .models import Slot, Intersection


class CrosswordGrid:
    """
    Représentation d'une grille de mots-croisés.
    Gère la structure de la grille et l'extraction des slots.
    """
    
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        # True = case noire, False = case blanche
        self.black_cells: Set[Tuple[int, int]] = set()
        self.slots: List[Slot] = []
        self.intersections: List[Intersection] = []
        self.solution: Dict[int, str] = {}  # slot_id -> mot
    
    def set_black(self, row: int, col: int):
        """Définit une case comme noire"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.black_cells.add((row, col))
    
    def set_white(self, row: int, col: int):
        """Définit une case comme blanche"""
        if (row, col) in self.black_cells:
            self.black_cells.remove((row, col))
    
    def is_black(self, row: int, col: int) -> bool:
        """Vérifie si une case est noire"""
        return (row, col) in self.black_cells
    
    def load_pattern(self, pattern: List[str]):
        """
        Charge un motif de grille.
        '#' ou '█' = case noire, autre = case blanche
        """
        self.black_cells.clear()
        for row, line in enumerate(pattern):
            for col, char in enumerate(line):
                if char in '#█':
                    self.set_black(row, col)
    
    def generate_random_pattern(self, black_ratio: float = 0.2, symmetric: bool = True):
        """
        Génère un motif aléatoire de cases noires.
        
        Args:
            black_ratio: Proportion de cases noires (0.0 à 1.0)
            symmetric: Si True, génère une grille symétrique (rotation 180°)
        """
        import random
        
        self.black_cells.clear()
        num_black = int(self.rows * self.cols * black_ratio)
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        
        if symmetric:
            # Ne considère que la moitié de la grille pour la symétrie
            half_positions = [(r, c) for r, c in positions 
                            if r < self.rows // 2 or (r == self.rows // 2 and c <= self.cols // 2)]
            random.shuffle(half_positions)
            
            blacks_placed = 0
            for r, c in half_positions:
                if blacks_placed >= num_black // 2:
                    break
                # Place la case noire et son symétrique
                self.set_black(r, c)
                self.set_black(self.rows - 1 - r, self.cols - 1 - c)
                blacks_placed += 1
        else:
            random.shuffle(positions)
            for i in range(min(num_black, len(positions))):
                r, c = positions[i]
                self.set_black(r, c)
    
    def extract_slots(self, min_length: int = 2) -> List[Slot]:
        """
        Extrait tous les slots (emplacements de mots) de la grille.
        Un slot est une séquence de cases blanches consécutives (H ou V).
        """
        self.slots = []
        slot_id = 0
        
        # Slots horizontaux
        for row in range(self.rows):
            col = 0
            while col < self.cols:
                if not self.is_black(row, col):
                    # Début d'un slot potentiel
                    start_col = col
                    cells = []
                    while col < self.cols and not self.is_black(row, col):
                        cells.append((row, col))
                        col += 1
                    if len(cells) >= min_length:
                        slot = Slot(
                            id=slot_id,
                            start_row=row,
                            start_col=start_col,
                            length=len(cells),
                            direction='H',
                            cells=cells
                        )
                        self.slots.append(slot)
                        slot_id += 1
                else:
                    col += 1
        
        # Slots verticaux
        for col in range(self.cols):
            row = 0
            while row < self.rows:
                if not self.is_black(row, col):
                    # Début d'un slot potentiel
                    start_row = row
                    cells = []
                    while row < self.rows and not self.is_black(row, col):
                        cells.append((row, col))
                        row += 1
                    if len(cells) >= min_length:
                        slot = Slot(
                            id=slot_id,
                            start_row=start_row,
                            start_col=col,
                            length=len(cells),
                            direction='V',
                            cells=cells
                        )
                        self.slots.append(slot)
                        slot_id += 1
                else:
                    row += 1
        
        return self.slots
    
    def find_intersections(self) -> List[Intersection]:
        """
        Trouve toutes les intersections entre les slots.
        Une intersection existe quand un slot H et un slot V partagent une cellule.
        """
        self.intersections = []
        
        # Crée un dictionnaire cell -> slots qui passent par cette cellule
        cell_to_slots: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        # cell -> [(slot_id, position_in_slot), ...]
        
        for slot in self.slots:
            for pos, cell in enumerate(slot.cells):
                cell_to_slots[cell].append((slot.id, pos))
        
        # Pour chaque cellule avec plusieurs slots, crée une intersection
        for cell, slot_infos in cell_to_slots.items():
            if len(slot_infos) == 2:
                (slot1_id, pos1), (slot2_id, pos2) = slot_infos
                intersection = Intersection(
                    slot1_id=slot1_id,
                    slot1_pos=pos1,
                    slot2_id=slot2_id,
                    slot2_pos=pos2,
                    cell=cell
                )
                self.intersections.append(intersection)
        
        return self.intersections
    
    def display_structure(self):
        """Affiche la structure de la grille (cases noires/blanches)"""
        print("\n╔" + "═" * (self.cols * 2 + 1) + "╗")
        for row in range(self.rows):
            print("║ ", end="")
            for col in range(self.cols):
                if self.is_black(row, col):
                    print("██", end="")
                else:
                    print("░░", end="")
            print(" ║")
        print("╚" + "═" * (self.cols * 2 + 1) + "╝")
    
    def display_solution(self):
        """Affiche la grille avec la solution"""
        if not self.solution:
            print("⚠ Pas de solution trouvée")
            return
        
        # Crée une grille de lettres
        letter_grid = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for slot in self.slots:
            if slot.id in self.solution:
                word = self.solution[slot.id]
                for i, (row, col) in enumerate(slot.cells):
                    if i < len(word):
                        letter_grid[row][col] = word[i]
        
        print("\n╔" + "═══" * self.cols + "═╗")
        for row in range(self.rows):
            print("║", end="")
            for col in range(self.cols):
                if self.is_black(row, col):
                    print(" ██", end="")
                else:
                    letter = letter_grid[row][col]
                    print(f" {letter} ", end="")
            print(" ║")
        print("╚" + "═══" * self.cols + "═╝")
    
    def get_solution_words(self) -> Dict[str, List[Tuple[str, Tuple[int, int]]]]:
        """Retourne les mots de la solution organisés par direction"""
        result = {'Horizontal': [], 'Vertical': []}
        for slot in sorted(self.slots, key=lambda s: (s.start_row, s.start_col)):
            if slot.id in self.solution:
                word = self.solution[slot.id]
                direction = 'Horizontal' if slot.direction == 'H' else 'Vertical'
                result[direction].append((word, (slot.start_row + 1, slot.start_col + 1)))
        return result
