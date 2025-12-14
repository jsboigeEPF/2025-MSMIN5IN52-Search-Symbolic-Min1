"""
Stratégie basée sur la fréquence des lettres.

Cette stratégie privilégie les mots contenant les lettres les plus
fréquentes dans les mots encore possibles.
"""

from typing import Set, Optional, Dict
from collections import Counter
from .base_strategy import BaseStrategy
from ..csp import ConstraintManager


class FrequencyStrategy(BaseStrategy):
    """
    Stratégie qui maximise l'utilisation des lettres fréquentes.
    
    Principe :
    - Calcule la fréquence de chaque lettre dans les mots possibles
    - Choisit le mot dont les lettres ont le score cumulé le plus élevé
    - Pénalise les lettres déjà testées (contraintes connues)
    
    Avantages :
    - Rapide à calculer
    - Intuitive
    - Bonne pour réduire rapidement l'espace de recherche
    
    Inconvénients :
    - Ne considère pas les positions des lettres
    - Peut manquer des opportunités d'élimination optimale
    """
    
    def __init__(self, penalize_known: bool = True, unique_letters_bonus: bool = True):
        """
        Initialise la stratégie de fréquence.
        
        Args:
            penalize_known: Si True, pénalise les lettres déjà connues
            unique_letters_bonus: Si True, bonus pour mots avec lettres uniques
        """
        super().__init__(name="Fréquence des lettres")
        self.penalize_known = penalize_known
        self.unique_letters_bonus = unique_letters_bonus
        self._frequency_cache = {}
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """
        Choisit le mot avec le meilleur score de fréquence.
        
        Args:
            possible_words: Mots encore possibles
            constraint_manager: Gestionnaire de contraintes
            attempt_number: Numéro de la tentative
            **kwargs: Arguments supplémentaires
            
        Returns:
            Le mot avec le meilleur score de fréquence
        """
        if not possible_words:
            return None
        
        # Si un seul mot possible, le retourner directement
        if len(possible_words) == 1:
            return list(possible_words)[0]
        
        # Calculer les fréquences des lettres
        letter_frequencies = self._calculate_letter_frequencies(possible_words)
        
        # Obtenir les lettres déjà connues
        known_letters = constraint_manager.get_known_letters() if self.penalize_known else set()
        
        # Évaluer chaque mot
        best_word = None
        best_score = -1
        
        for word in possible_words:
            score = self._score_word(word, letter_frequencies, known_letters)
            
            if score > best_score:
                best_score = score
                best_word = word
        
        self.stats['words_evaluated'] = len(possible_words)
        return best_word
    
    def _calculate_letter_frequencies(self, words: Set[str]) -> Dict[str, float]:
        """
        Calcule la fréquence de chaque lettre dans l'ensemble de mots.
        
        Args:
            words: Ensemble de mots
            
        Returns:
            Dictionnaire {lettre: fréquence relative}
        """
        # Utiliser le cache si disponible
        cache_key = frozenset(words)
        if cache_key in self._frequency_cache:
            self.stats['cache_hits'] += 1
            return self._frequency_cache[cache_key]
        
        # Compter toutes les lettres
        letter_counts = Counter()
        for word in words:
            # Compter chaque lettre une fois par mot (évite le biais des doublons)
            for letter in set(word):
                letter_counts[letter] += 1
        
        # Normaliser en fréquences
        total = sum(letter_counts.values())
        frequencies = {
            letter: count / total
            for letter, count in letter_counts.items()
        }
        
        # Mettre en cache
        self._frequency_cache[cache_key] = frequencies
        return frequencies
    
    def _score_word(
        self,
        word: str,
        letter_frequencies: Dict[str, float],
        known_letters: Set[str]
    ) -> float:
        """
        Calcule le score d'un mot basé sur les fréquences.
        
        Args:
            word: Le mot à scorer
            letter_frequencies: Fréquences des lettres
            known_letters: Lettres déjà connues
            
        Returns:
            Score du mot (plus élevé = meilleur)
        """
        score = 0.0
        unique_letters = set(word)
        
        # Ajouter le score de chaque lettre unique
        for letter in unique_letters:
            letter_score = letter_frequencies.get(letter, 0.0)
            
            # Pénaliser les lettres déjà connues
            if self.penalize_known and letter in known_letters:
                letter_score *= 0.5  # Réduire le score de moitié
            
            score += letter_score
        
        # Bonus pour les mots avec toutes lettres différentes
        if self.unique_letters_bonus and len(unique_letters) == 5:
            score *= 1.2  # Bonus de 20%
        
        return score
    
    def get_first_guess(self, language: str = "en") -> str:
        """
        Retourne le meilleur premier mot basé sur l'analyse de fréquence.
        
        Args:
            language: Langue du jeu
            
        Returns:
            Mot optimal pour le premier coup
        """
        # Mots optimaux basés sur l'analyse de fréquence
        optimal_first_words = {
            'en': 'SOARE',  # S, O, A, R, E sont les lettres les plus fréquentes
            'fr': 'AIMER',  # A, I, M, E, R sont très fréquents en français
        }
        return optimal_first_words.get(language, 'AROSE')
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        """Explique le choix basé sur les fréquences."""
        letter_frequencies = kwargs.get('letter_frequencies', {})
        
        if letter_frequencies:
            word_letters = set(chosen_word)
            avg_freq = sum(letter_frequencies.get(l, 0) for l in word_letters) / len(word_letters)
            
            return (
                f"Stratégie Fréquence : '{chosen_word}' choisi pour ses lettres fréquentes "
                f"(score moyen: {avg_freq:.3f}) parmi {len(possible_words)} mots"
            )
        
        return super().explain_choice(chosen_word, possible_words, **kwargs)
    
    def reset_cache(self):
        """Vide le cache des fréquences."""
        self._frequency_cache.clear()


class PositionalFrequencyStrategy(BaseStrategy):
    """
    Variante qui considère la fréquence des lettres À CHAQUE POSITION.
    
    Plus sophistiqué que FrequencyStrategy car il tient compte
    de la position des lettres dans le mot.
    """
    
    def __init__(self):
        super().__init__(name="Fréquence positionnelle")
        self._position_freq_cache = {}
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """Choisit le mot avec le meilleur score positionnel."""
        if not possible_words:
            return None
        
        if len(possible_words) == 1:
            return list(possible_words)[0]
        
        # Calculer les fréquences positionnelles
        position_frequencies = self._calculate_position_frequencies(possible_words)
        
        # Évaluer chaque mot
        best_word = None
        best_score = -1
        
        for word in possible_words:
            score = self._score_word_positional(word, position_frequencies)
            
            if score > best_score:
                best_score = score
                best_word = word
        
        self.stats['words_evaluated'] = len(possible_words)
        return best_word
    
    def _calculate_position_frequencies(self, words: Set[str]) -> Dict[int, Dict[str, float]]:
        """
        Calcule la fréquence de chaque lettre à chaque position.
        
        Returns:
            {position: {lettre: fréquence}}
        """
        cache_key = frozenset(words)
        if cache_key in self._position_freq_cache:
            self.stats['cache_hits'] += 1
            return self._position_freq_cache[cache_key]
        
        # Compter les lettres par position
        position_counts = {i: Counter() for i in range(5)}
        
        for word in words:
            for pos, letter in enumerate(word):
                position_counts[pos][letter] += 1
        
        # Normaliser en fréquences
        n_words = len(words)
        position_frequencies = {
            pos: {letter: count / n_words for letter, count in counts.items()}
            for pos, counts in position_counts.items()
        }
        
        self._position_freq_cache[cache_key] = position_frequencies
        return position_frequencies
    
    def _score_word_positional(
        self,
        word: str,
        position_frequencies: Dict[int, Dict[str, float]]
    ) -> float:
        """Score un mot selon les fréquences positionnelles."""
        score = 0.0
        
        for pos, letter in enumerate(word):
            score += position_frequencies[pos].get(letter, 0.0)
        
        return score
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        return (
            f"Stratégie Fréquence Positionnelle : '{chosen_word}' "
            f"choisi pour l'optimisation position par position "
            f"(parmi {len(possible_words)} mots)"
        )
