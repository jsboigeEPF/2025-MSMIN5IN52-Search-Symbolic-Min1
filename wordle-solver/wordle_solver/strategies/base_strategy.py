"""
Classe de base abstraite pour les stratégies de résolution Wordle.

Toutes les stratégies doivent hériter de cette classe et implémenter
la méthode choose_word().
"""

from abc import ABC, abstractmethod
from typing import Set, Optional, Dict, Any
from ..csp import ConstraintManager


class BaseStrategy(ABC):
    """
    Classe abstraite définissant l'interface pour les stratégies de jeu.
    
    Une stratégie détermine quel mot choisir parmi les mots possibles
    en fonction de l'état actuel du jeu.
    """
    
    def __init__(self, name: str = "Base Strategy"):
        """
        Initialise la stratégie.
        
        Args:
            name: Nom de la stratégie
        """
        self.name = name
        self.stats = {
            'words_evaluated': 0,
            'time_taken': 0.0,
            'cache_hits': 0,
        }
    
    @abstractmethod
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """
        Choisit le meilleur mot à jouer selon la stratégie.
        
        Args:
            possible_words: Ensemble des mots encore possibles
            constraint_manager: Gestionnaire de contraintes actuel
            attempt_number: Numéro de la tentative (1-6)
            **kwargs: Arguments supplémentaires spécifiques à la stratégie
            
        Returns:
            Le mot choisi, ou None si aucun mot n'est possible
        """
        pass
    
    def get_first_guess(self, language: str = "en") -> str:
        """
        Retourne le meilleur premier mot selon la stratégie.
        
        Ce mot est généralement pré-calculé pour optimiser la performance.
        
        Args:
            language: Langue ('en' ou 'fr')
            
        Returns:
            Le mot recommandé pour la première tentative
        """
        # Mots recommandés par défaut (basés sur des analyses)
        first_guesses = {
            'en': 'SOARE',  # Optimal selon études (SOARE > ROATE > RAISE)
            'fr': 'AIMER',  # Bon équilibre pour le français
        }
        return first_guesses.get(language, first_guesses['en'])
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        """
        Explique pourquoi ce mot a été choisi.
        
        Args:
            chosen_word: Le mot qui a été choisi
            possible_words: Les mots qui étaient possibles
            **kwargs: Informations supplémentaires sur le choix
            
        Returns:
            Explication textuelle du choix
        """
        return f"Stratégie {self.name} a choisi '{chosen_word}' parmi {len(possible_words)} mots possibles."
    
    def reset_stats(self):
        """Réinitialise les statistiques de la stratégie."""
        self.stats = {
            'words_evaluated': 0,
            'time_taken': 0.0,
            'cache_hits': 0,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la stratégie."""
        return self.stats.copy()
    
    def __str__(self) -> str:
        return f"{self.name}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"


class SimpleStrategy(BaseStrategy):
    """
    Stratégie simple : choisit le premier mot alphabétiquement.
    
    Utilisée comme baseline pour comparer les autres stratégies.
    """
    
    def __init__(self):
        super().__init__(name="Simple (Alphabétique)")
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """Choisit le premier mot alphabétiquement."""
        if not possible_words:
            return None
        
        self.stats['words_evaluated'] = len(possible_words)
        return sorted(possible_words)[0]
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        return f"Choix alphabétique simple : '{chosen_word}' (premier parmi {len(possible_words)} mots)"


class RandomStrategy(BaseStrategy):
    """
    Stratégie aléatoire : choisit un mot au hasard.
    
    Utilisée comme baseline pour mesurer l'efficacité des autres stratégies.
    """
    
    def __init__(self):
        super().__init__(name="Aléatoire")
        self._rng = None
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """Choisit un mot aléatoirement."""
        if not possible_words:
            return None
        
        import random
        if self._rng is None:
            self._rng = random.Random(kwargs.get('seed', None))
        
        self.stats['words_evaluated'] = len(possible_words)
        return self._rng.choice(list(possible_words))
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        return f"Choix aléatoire : '{chosen_word}' (parmi {len(possible_words)} mots)"
