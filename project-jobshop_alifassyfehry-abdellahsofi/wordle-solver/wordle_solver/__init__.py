"""
Wordle Solver - Un solveur intelligent combinant CSP et LLM.

Ce package fournit des outils pour résoudre Wordle de manière optimale
en utilisant la programmation par contraintes et l'intelligence artificielle.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from .csp import ConstraintManager, WordFilter, HybridSolver
from .game import WordleGame, Feedback, FeedbackResult, generate_feedback
from .dictionaries import DictionaryLoader

__all__ = [
    'ConstraintManager',
    'WordFilter',
    'HybridSolver',
    'WordleGame',
    'Feedback',
    'FeedbackResult',
    'generate_feedback',
    'DictionaryLoader',
]
