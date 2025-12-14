"""
Stratégie par maximisation d'entropie (information theory).

Cette stratégie choisit le mot qui maximise l'information gagnée,
c'est-à-dire celui qui divise le mieux l'espace des possibilités.
"""

from typing import Set, Optional, Dict, List, Tuple
from collections import defaultdict
import math
from .base_strategy import BaseStrategy
from ..csp import ConstraintManager
from ..game import generate_feedback


class EntropyStrategy(BaseStrategy):
    """
    Stratégie par maximisation d'entropie.
    
    Principe :
    - Pour chaque mot candidat, simule le feedback pour tous les mots possibles
    - Calcule l'entropie (distribution des patterns de feedback)
    - Choisit le mot qui maximise l'entropie = maximise l'information
    
    Mathématiquement :
    Entropie(mot) = -Σ p(pattern) * log2(p(pattern))
    où p(pattern) est la probabilité d'obtenir ce pattern de feedback
    
    Avantages :
    - Théoriquement optimal (minimise le nombre moyen de tentatives)
    - Performances excellentes en pratique
    - Basé sur la théorie de l'information
    
    Inconvénients :
    - Très coûteux en calcul (O(n²) où n = nombre de mots possibles)
    - Nécessite de simuler tous les feedbacks possibles
    """
    
    def __init__(self, use_full_dictionary: bool = False, max_words_to_evaluate: int = None):
        """
        Initialise la stratégie d'entropie.
        
        Args:
            use_full_dictionary: Si True, évalue aussi les mots hors possibles
            max_words_to_evaluate: Limite le nombre de mots à évaluer (optimisation)
        """
        super().__init__(name="Entropie (Information Theory)")
        self.use_full_dictionary = use_full_dictionary
        self.max_words_to_evaluate = max_words_to_evaluate
        self._entropy_cache = {}
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """
        Choisit le mot qui maximise l'entropie.
        
        Args:
            possible_words: Mots encore possibles
            constraint_manager: Gestionnaire de contraintes (non utilisé ici)
            attempt_number: Numéro de la tentative
            **kwargs: Peut contenir 'full_dictionary' pour évaluation élargie
            
        Returns:
            Le mot qui maximise l'entropie attendue
        """
        if not possible_words:
            return None
        
        # Si un seul mot, le retourner
        if len(possible_words) == 1:
            return list(possible_words)[0]
        
        # Si peu de mots restants, retourner simplement le premier
        if len(possible_words) <= 2:
            return sorted(possible_words)[0]
        
        # Déterminer les mots à évaluer
        if self.use_full_dictionary and 'full_dictionary' in kwargs:
            words_to_evaluate = kwargs['full_dictionary']
        else:
            words_to_evaluate = possible_words
        
        # Limiter le nombre de mots à évaluer si nécessaire
        if self.max_words_to_evaluate and len(words_to_evaluate) > self.max_words_to_evaluate:
            # Prendre un échantillon représentatif
            words_to_evaluate = self._sample_words(words_to_evaluate, self.max_words_to_evaluate)
        
        # Calculer l'entropie de chaque mot
        best_word = None
        best_entropy = -1
        
        for candidate in words_to_evaluate:
            entropy = self._calculate_entropy(candidate, possible_words)
            
            if entropy > best_entropy:
                best_entropy = entropy
                best_word = candidate
        
        self.stats['words_evaluated'] = len(words_to_evaluate)
        return best_word
    
    def _calculate_entropy(self, candidate: str, possible_targets: Set[str]) -> float:
        """
        Calcule l'entropie d'un mot candidat.
        
        Args:
            candidate: Le mot à évaluer
            possible_targets: Les mots cibles possibles
            
        Returns:
            Entropie du mot (bits d'information)
        """
        # Vérifier le cache
        cache_key = (candidate, frozenset(possible_targets))
        if cache_key in self._entropy_cache:
            self.stats['cache_hits'] += 1
            return self._entropy_cache[cache_key]
        
        # Simuler le feedback pour chaque mot cible possible
        pattern_counts = defaultdict(int)
        
        for target in possible_targets:
            # Générer le feedback
            feedback = generate_feedback(candidate, target)
            pattern = feedback.to_pattern()  # "GYBBG" par exemple
            pattern_counts[pattern] += 1
        
        # Calculer l'entropie
        n_total = len(possible_targets)
        entropy = 0.0
        
        for count in pattern_counts.values():
            if count > 0:
                probability = count / n_total
                entropy -= probability * math.log2(probability)
        
        # Mettre en cache
        self._entropy_cache[cache_key] = entropy
        return entropy
    
    def _sample_words(self, words: Set[str], n: int) -> Set[str]:
        """
        Échantillonne n mots de manière représentative.
        
        Args:
            words: Ensemble de mots
            n: Nombre de mots à échantillonner
            
        Returns:
            Sous-ensemble de mots
        """
        words_list = sorted(words)
        step = max(1, len(words_list) // n)
        return set(words_list[::step][:n])
    
    def get_first_guess(self, language: str = "en") -> str:
        """
        Retourne le premier mot optimal selon l'analyse d'entropie.
        
        Ces mots ont été pré-calculés par analyse exhaustive.
        
        Args:
            language: Langue du jeu
            
        Returns:
            Mot optimal
        """
        # Mots optimaux selon analyse d'entropie
        # (calculés sur l'ensemble du dictionnaire)
        optimal_words = {
            'en': 'SOARE',  # ~5.89 bits d'entropie moyenne
            'fr': 'AIMER',  # Analyse similaire pour français
        }
        return optimal_words.get(language, 'AROSE')
    
    def explain_choice(
        self,
        chosen_word: str,
        possible_words: Set[str],
        **kwargs
    ) -> str:
        """Explique le choix basé sur l'entropie."""
        entropy = kwargs.get('entropy', None)
        
        if entropy is not None:
            return (
                f"Stratégie Entropie : '{chosen_word}' maximise l'information "
                f"(entropie: {entropy:.2f} bits) parmi {len(possible_words)} mots"
            )
        
        return (
            f"Stratégie Entropie : '{chosen_word}' choisi pour maximiser "
            f"l'information gagnée (parmi {len(possible_words)} mots)"
        )
    
    def reset_cache(self):
        """Vide le cache d'entropie."""
        self._entropy_cache.clear()


class FastEntropyStrategy(BaseStrategy):
    """
    Version optimisée de la stratégie d'entropie.
    
    Utilise des heuristiques pour réduire le temps de calcul :
    - Limite le nombre de mots évalués
    - Utilise un cache agressif
    - Échantillonnage intelligent
    """
    
    def __init__(self, evaluation_limit: int = 50):
        """
        Initialise la stratégie d'entropie rapide.
        
        Args:
            evaluation_limit: Nombre maximum de mots à évaluer
        """
        super().__init__(name="Entropie Rapide")
        self.evaluation_limit = evaluation_limit
        self._cache = {}
    
    def choose_word(
        self,
        possible_words: Set[str],
        constraint_manager: ConstraintManager,
        attempt_number: int,
        **kwargs
    ) -> Optional[str]:
        """Choisit le mot avec la meilleure entropie (version rapide)."""
        if not possible_words:
            return None
        
        if len(possible_words) <= 2:
            return sorted(possible_words)[0]
        
        # Limiter les mots à évaluer
        if len(possible_words) > self.evaluation_limit:
            # Stratégie hybride : 
            # 1. Prendre les X premiers alphabétiquement
            # 2. Échantillonner le reste
            sorted_words = sorted(possible_words)
            words_to_eval = set(sorted_words[:self.evaluation_limit // 2])
            
            # Ajouter un échantillon du reste
            remaining = set(sorted_words[self.evaluation_limit // 2:])
            sample_size = self.evaluation_limit // 2
            if len(remaining) > sample_size:
                step = len(remaining) // sample_size
                sampled = [w for i, w in enumerate(sorted(remaining)) if i % step == 0]
                words_to_eval.update(sampled[:sample_size])
            else:
                words_to_eval.update(remaining)
        else:
            words_to_eval = possible_words
        
        # Calculer l'entropie approximative
        best_word = None
        best_score = -1
        
        for candidate in words_to_eval:
            score = self._approximate_entropy(candidate, possible_words)
            
            if score > best_score:
                best_score = score
                best_word = candidate
        
        self.stats['words_evaluated'] = len(words_to_eval)
        return best_word
    
    def _approximate_entropy(self, candidate: str, targets: Set[str]) -> float:
        """
        Calcule une approximation rapide de l'entropie.
        
        Utilise un échantillon si le nombre de cibles est trop grand.
        """
        # Si peu de cibles, calcul exact
        if len(targets) <= 20:
            return self._calculate_exact_entropy(candidate, targets)
        
        # Sinon, échantillonner
        sample_size = 20
        targets_list = sorted(targets)
        step = max(1, len(targets_list) // sample_size)
        sample = set(targets_list[::step][:sample_size])
        
        return self._calculate_exact_entropy(candidate, sample)
    
    def _calculate_exact_entropy(self, candidate: str, targets: Set[str]) -> float:
        """Calcule l'entropie exacte."""
        cache_key = (candidate, frozenset(targets))
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]
        
        pattern_counts = defaultdict(int)
        for target in targets:
            feedback = generate_feedback(candidate, target)
            pattern = feedback.to_pattern()
            pattern_counts[pattern] += 1
        
        n_total = len(targets)
        entropy = 0.0
        
        for count in pattern_counts.values():
            if count > 0:
                p = count / n_total
                entropy -= p * math.log2(p)
        
        self._cache[cache_key] = entropy
        return entropy
