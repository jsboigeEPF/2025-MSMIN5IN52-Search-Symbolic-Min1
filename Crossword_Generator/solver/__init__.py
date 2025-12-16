# -*- coding: utf-8 -*-
"""
Package solver pour le générateur de mots-croisés.

Ce package contient tous les modules nécessaires pour la génération
et la résolution de grilles de mots-croisés.
"""

from .models import Slot, Intersection
from .dictionary import WordDictionary, remove_accents
from .definitions import DefinitionService
from .grid import CrosswordGrid
from .solver import CrosswordSolver, SolutionCallback
from .patterns import GRID_PATTERNS

__all__ = [
    'Slot',
    'Intersection',
    'WordDictionary',
    'remove_accents',
    'DefinitionService',
    'CrosswordGrid',
    'CrosswordSolver',
    'SolutionCallback',
    'GRID_PATTERNS',
]
