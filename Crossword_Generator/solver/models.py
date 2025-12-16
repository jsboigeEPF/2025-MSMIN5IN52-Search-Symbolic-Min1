# -*- coding: utf-8 -*-
"""
Structures de données pour le générateur de mots-croisés.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Slot:
    """
    Représente un emplacement de mot dans la grille.
    
    Attributes:
        id: Identifiant unique du slot
        start_row: Ligne de départ (0-indexé)
        start_col: Colonne de départ (0-indexé)
        length: Longueur du mot
        direction: 'H' (horizontal) ou 'V' (vertical)
        cells: Liste des coordonnées (row, col) des cellules du slot
    """
    id: int
    start_row: int
    start_col: int
    length: int
    direction: str  # 'H' ou 'V'
    cells: List[Tuple[int, int]]
    
    def __repr__(self):
        return f"Slot({self.id}, {self.direction}, pos=({self.start_row},{self.start_col}), len={self.length})"


@dataclass
class Intersection:
    """
    Représente une intersection entre deux slots.
    
    Attributes:
        slot1_id: ID du premier slot
        slot1_pos: Position dans le premier slot où l'intersection a lieu
        slot2_id: ID du second slot
        slot2_pos: Position dans le second slot où l'intersection a lieu
        cell: Coordonnées (row, col) de la cellule d'intersection
    """
    slot1_id: int
    slot1_pos: int
    slot2_id: int
    slot2_pos: int
    cell: Tuple[int, int]
    
    def __repr__(self):
        return f"Intersection(slots={self.slot1_id}[{self.slot1_pos}]∩{self.slot2_id}[{self.slot2_pos}], cell={self.cell})"
