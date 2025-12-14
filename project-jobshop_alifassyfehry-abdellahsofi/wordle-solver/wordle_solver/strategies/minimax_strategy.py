"""
Stratégie Minimax pour Wordle.

Cette stratégie minimise le pire cas en choisissant le mot qui garantit
le meilleur résultat dans le scénario le moins favorable.
"""

from typing import Set, Optional, Dict, Tuple
from collections import defaultdict
from .base_strategy import BaseStrategy
from ..csp import ConstraintManager
from ..game import generate_feedback


class MinimaxStrategy(BaseStrategy):
    """
    Stratégie Minimax : minimise le pire cas.
    
    Principe :
    - Pour chaque mot candidat, simule tous les feedbacks possibles
    - Identifie le pire cas (le groupe le plus grand après feedback)
    - Choisit le mot dont le pire cas est le meilleur
    
    Mathématiquement :
    Score(mot) = max(taille_groupe) pour tous les patterns de feedback
    Choisir le mot avec le min(Score)
    
    Avantages :
    - Garantit un nombre maximum de tentatives
    - Stratégie défensive robuste
    - Évite les mauvaises surprises
    
    Inconvénients :
    - Peut être conservateur
    - Pas toujours optimal en moyenne
    - Coûteux en calcul
    """
    
    def __init__(self, tie_breaker: str = "entropy"):
        """
        Initialise la stratégie minimax.
        
        Args:
            tie_breaker: Méthode pour départager les ex-aequo
                        ("entropy", "frequency", "alphabetical")
        """
        super().__init__(name="Minimax")
        self.tie_breaker = tie_breaker
        self._cache = {}
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """
        Choisit le mot qui minimise le pire cas.
        
        Args:
            possible_words: Mots encore possibles
            constraint_manager: Gestionnaire de contraintes
            attempt_number: Numéro de la tentative
            **kwargs: Arguments supplémentaires
            
        Returns:
            Le mot qui minimise le pire cas
        """
        if not possible_words:
            return None
        
        if len(possible_words) == 1:
            return list(possible_words)[0]
        
        # Si 2 mots, retourner le premier alphabétiquement
        if len(possible_words) == 2:
            return sorted(possible_words)[0]
        
        # Évaluer chaque mot
        best_words = []
        best_worst_case = float('inf')
        
        for candidate in possible_words:
            worst_case = self._calculate_worst_case(candidate, possible_words)
            
            if worst_case < best_worst_case:
                best_worst_case = worst_case
                best_words = [candidate]
            elif worst_case == best_worst_case:
                best_words.append(candidate)
        
        self.stats['words_evaluated'] = len(possible_words)
        
        # Si plusieurs mots avec le même pire cas, départager
        if len(best_words) > 1:
            return self._break_tie(best_words, possible_words)
        
        return best_words[0]
    
    def _calculate_worst_case(self, candidate: str, targets: Set[str]) -> int:
        """
        Calcule la taille du pire groupe après feedback.
        
        Args:
            candidate: Mot candidat
            targets: Mots cibles possibles
            
        Returns:
            Taille du plus grand groupe
        """
        cache_key = (candidate, frozenset(targets))
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]
        
        # Grouper les cibles par pattern de feedback
        pattern_groups = defaultdict(list)
        
        for target in targets:
            feedback = generate_feedback(candidate, target)
            pattern = feedback.to_pattern()
            pattern_groups[pattern].append(target)
        
        # Trouver le groupe le plus grand
        worst_case = max(len(group) for group in pattern_groups.values())
        
        self._cache[cache_key] = worst_case
        return worst_case
    
    def _break_tie(self, tied_words: list, possible_words: Set[str]) -> str:
        """
        Départage les ex-aequo selon la méthode choisie.
        
        Args:
            tied_words: Liste de mots ex-aequo
            possible_words: Mots possibles
            
        Returns:
            Le mot choisi
        """
        if self.tie_breaker == "alphabetical":
            return sorted(tied_words)[0]
        
        elif self.tie_breaker == "entropy":
            # Calculer une entropie simplifiée
            best_word = tied_words[0]
            best_score = -1
            
            for word in tied_words:
                score = self._simple_entropy(word, possible_words)
                if score > best_score:
                    best_score = score
                    best_word = word
            
            return best_word
        
        elif self.tie_breaker == "frequency":
            # Choisir le mot avec les lettres les plus fréquentes
            from .frequency_strategy import FrequencyStrategy
            freq_strategy = FrequencyStrategy()
            
            best_word = tied_words[0]
            best_score = -1
            
            letter_freqs = freq_strategy._calculate_letter_frequencies(possible_words)
            
            for word in tied_words:
                score = freq_strategy._score_word(word, letter_freqs, set())
                if score > best_score:
                    best_score = score
                    best_word = word
            
            return best_word
        
        return tied_words[0]
    
    def _simple_entropy(self, candidate: str, targets: Set[str]) -> float:
        """Calcule une entropie simplifiée pour départager."""
        pattern_counts = defaultdict(int)
        
        for target in targets:
            feedback = generate_feedback(candidate, target)
            pattern = feedback.to_pattern()
            pattern_counts[pattern] += 1
        
        # Nombre de groupes différents (plus = mieux)
        return len(pattern_counts)
    
    def get_first_guess(self, language: str = "en") -> str:
        """
        Retourne le premier mot optimal selon minimax.
        
        Args:
            language: Langue du jeu
            
        Returns:
            Mot optimal minimax
        """
        # Ces mots ont de bonnes propriétés minimax
        optimal_words = {
            'en': 'RAISE',  # Bon équilibre minimax
            'fr': 'AIMER',
        }
        return optimal_words.get(language, 'AROSE')
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        """Explique le choix minimax."""
        worst_case = kwargs.get('worst_case', None)
        
        if worst_case is not None:
            return (
                f"Stratégie Minimax : '{chosen_word}' minimise le pire cas "
                f"(max {worst_case} mots restants) parmi {len(possible_words)} mots"
            )
        
        return (
            f"Stratégie Minimax : '{chosen_word}' choisi pour minimiser "
            f"le pire scénario (parmi {len(possible_words)} mots)"
        )


class ExpectedSizeStrategy(BaseStrategy):
    """
    Variante qui minimise la taille MOYENNE (espérée) des groupes.
    
    Compromis entre Minimax (pessimiste) et Entropie (optimiste).
    """
    
    def __init__(self):
        super().__init__(name="Taille Espérée")
        self._cache = {}
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """Choisit le mot qui minimise la taille moyenne attendue."""
        if not possible_words:
            return None
        
        if len(possible_words) <= 2:
            return sorted(possible_words)[0]
        
        best_word = None
        best_expected = float('inf')
        
        for candidate in possible_words:
            expected = self._calculate_expected_size(candidate, possible_words)
            
            if expected < best_expected:
                best_expected = expected
                best_word = candidate
        
        self.stats['words_evaluated'] = len(possible_words)
        return best_word
    
    def _calculate_expected_size(self, candidate: str, targets: Set[str]) -> float:
        """
        Calcule la taille moyenne attendue des groupes.
        
        Args:
            candidate: Mot candidat
            targets: Mots cibles possibles
            
        Returns:
            Taille moyenne pondérée des groupes
        """
        cache_key = (candidate, frozenset(targets))
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]
        
        # Grouper par pattern
        pattern_groups = defaultdict(list)
        
        for target in targets:
            feedback = generate_feedback(candidate, target)
            pattern = feedback.to_pattern()
            pattern_groups[pattern].append(target)
        
        # Calculer la moyenne pondérée
        n_total = len(targets)
        expected = sum(
            len(group) * len(group) / n_total
            for group in pattern_groups.values()
        )
        
        self._cache[cache_key] = expected
        return expected
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        return (
            f"Stratégie Taille Espérée : '{chosen_word}' minimise "
            f"le nombre moyen de mots restants (parmi {len(possible_words)} mots)"
        )
