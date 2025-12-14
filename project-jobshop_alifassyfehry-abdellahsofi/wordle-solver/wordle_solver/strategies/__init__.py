"""Module de stratégies de jeu Wordle."""

from .base_strategy import BaseStrategy, SimpleStrategy, RandomStrategy
from .frequency_strategy import FrequencyStrategy, PositionalFrequencyStrategy
from .entropy_strategy import EntropyStrategy, FastEntropyStrategy
from .minimax_strategy import MinimaxStrategy, ExpectedSizeStrategy
from .comparator import StrategyComparator, quick_benchmark, GameResult, StrategyStats

__all__ = [
    # Classes de base
    'BaseStrategy',
    'SimpleStrategy',
    'RandomStrategy',
    
    # Stratégies par fréquence
    'FrequencyStrategy',
    'PositionalFrequencyStrategy',
    
    # Stratégies par entropie
    'EntropyStrategy',
    'FastEntropyStrategy',
    
    # Stratégies minimax
    'MinimaxStrategy',
    'ExpectedSizeStrategy',
    
    # Comparaison
    'StrategyComparator',
    'quick_benchmark',
    'GameResult',
    'StrategyStats',
]
