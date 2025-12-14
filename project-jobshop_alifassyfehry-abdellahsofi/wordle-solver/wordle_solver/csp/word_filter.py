"""
Module de filtrage de mots selon les contraintes CSP.

Implémente un filtrage efficace du dictionnaire de mots
en appliquant toutes les contraintes accumulées.
"""

from typing import Set, List
from .constraint_manager import ConstraintManager


class WordFilter:
    """
    Filtre un dictionnaire de mots selon les contraintes CSP.
    
    Optimisé pour performance avec des opérations sur sets.
    """
    
    def __init__(self, dictionary: Set[str]):
        """
        Initialise le filtre avec un dictionnaire.
        
        Args:
            dictionary: Ensemble de mots valides (5 lettres en majuscules)
        """
        # Normaliser tous les mots en majuscules
        self.full_dictionary = {word.upper() for word in dictionary}
        self.current_candidates = self.full_dictionary.copy()
        self._cache = {}
    
    def filter_by_constraints(self, constraint_manager: ConstraintManager) -> Set[str]:
        """
        Filtre les mots selon les contraintes actuelles.
        
        Args:
            constraint_manager: Le gestionnaire de contraintes
            
        Returns:
            Ensemble de mots valides selon les contraintes
        """
        # Créer une clé de cache basée sur les contraintes
        cache_key = self._create_cache_key(constraint_manager)
        
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # CORRECTION: Toujours filtrer depuis le dictionnaire complet
        # pour éviter de perdre des mots à cause d'un état mutable
        valid_words = {
            word for word in self.full_dictionary
            if constraint_manager.is_word_valid(word)
        }
        
        # Mettre en cache et mettre à jour current_candidates pour info
        self._cache[cache_key] = valid_words
        self.current_candidates = valid_words
        
        return valid_words.copy()
    
    def filter_words(self, words: Set[str], constraint_manager: ConstraintManager) -> Set[str]:
        """
        Filtre un ensemble de mots spécifique (sans utiliser current_candidates).
        
        Args:
            words: Ensemble de mots à filtrer
            constraint_manager: Le gestionnaire de contraintes
            
        Returns:
            Ensemble de mots valides
        """
        return {
            word for word in words
            if constraint_manager.is_word_valid(word)
        }
    
    def _create_cache_key(self, constraint_manager: ConstraintManager) -> str:
        """
        Crée une clé de cache unique basée sur les contraintes.
        
        Args:
            constraint_manager: Le gestionnaire de contraintes
            
        Returns:
            Clé de cache sous forme de string
        """
        summary = constraint_manager.get_constraint_summary()
        
        # Créer une représentation hashable
        correct = tuple(sorted(summary['correct_positions'].items()))
        present = tuple(sorted(
            (k, tuple(sorted(v))) for k, v in summary['present_letters'].items()
        ))
        absent = tuple(sorted(summary['absent_letters']))
        counts = tuple(sorted(summary['letter_counts'].items()))
        
        return f"{correct}|{present}|{absent}|{counts}"
    
    def get_words_by_length(self, length: int) -> Set[str]:
        """
        Retourne les mots d'une longueur spécifique.
        
        Args:
            length: Longueur des mots
            
        Returns:
            Ensemble de mots de cette longueur
        """
        return {word for word in self.current_candidates if len(word) == length}
    
    def get_words_with_letters(self, required_letters: Set[str]) -> Set[str]:
        """
        Retourne les mots contenant toutes les lettres requises.
        
        Args:
            required_letters: Ensemble de lettres qui doivent être présentes
            
        Returns:
            Ensemble de mots contenant toutes ces lettres
        """
        required_upper = {letter.upper() for letter in required_letters}
        return {
            word for word in self.current_candidates
            if required_upper.issubset(set(word))
        }
    
    def get_words_without_letters(self, forbidden_letters: Set[str]) -> Set[str]:
        """
        Retourne les mots ne contenant aucune des lettres interdites.
        
        Args:
            forbidden_letters: Ensemble de lettres qui ne doivent pas être présentes
            
        Returns:
            Ensemble de mots sans ces lettres
        """
        forbidden_upper = {letter.upper() for letter in forbidden_letters}
        return {
            word for word in self.current_candidates
            if not forbidden_upper.intersection(set(word))
        }
    
    def count_candidates(self) -> int:
        """Retourne le nombre de candidats actuels."""
        return len(self.current_candidates)
    
    def reset(self):
        """Réinitialise le filtre à l'état initial."""
        self.current_candidates = self.full_dictionary.copy()
        self._cache.clear()
    
    def get_sample(self, n: int = 10) -> List[str]:
        """
        Retourne un échantillon de mots candidats.
        
        Args:
            n: Nombre de mots à retourner
            
        Returns:
            Liste de n mots (ou moins si moins de candidats)
        """
        return sorted(list(self.current_candidates))[:n]
    
    def get_letter_frequency(self) -> dict[str, float]:
        """
        Calcule la fréquence de chaque lettre dans les mots candidats.
        
        Returns:
            Dictionnaire {lettre: fréquence relative}
        """
        if not self.current_candidates:
            return {}
        
        letter_counts = {}
        total_letters = 0
        
        for word in self.current_candidates:
            for letter in word:
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
                total_letters += 1
        
        # Normaliser en fréquences
        return {
            letter: count / total_letters
            for letter, count in letter_counts.items()
        }
    
    def get_position_letter_frequency(self) -> dict[int, dict[str, float]]:
        """
        Calcule la fréquence de chaque lettre à chaque position.
        
        Returns:
            Dictionnaire {position: {lettre: fréquence}}
        """
        if not self.current_candidates:
            return {}
        
        position_counts = {i: {} for i in range(5)}
        
        for word in self.current_candidates:
            for pos, letter in enumerate(word):
                if letter not in position_counts[pos]:
                    position_counts[pos][letter] = 0
                position_counts[pos][letter] += 1
        
        # Normaliser en fréquences
        n_words = len(self.current_candidates)
        return {
            pos: {letter: count / n_words for letter, count in counts.items()}
            for pos, counts in position_counts.items()
        }
    
    def __len__(self) -> int:
        return len(self.current_candidates)
    
    def __str__(self) -> str:
        return f"WordFilter(candidates={len(self.current_candidates)}/{len(self.full_dictionary)})"
    
    def __repr__(self) -> str:
        return self.__str__()


class FastWordFilter:
    """
    Version optimisée du filtre de mots utilisant des techniques avancées.
    
    Utilise des index pré-calculés pour accélérer les opérations de filtrage.
    """
    
    def __init__(self, dictionary: Set[str]):
        """
        Initialise le filtre optimisé.
        
        Args:
            dictionary: Ensemble de mots valides
        """
        self.dictionary = {word.upper() for word in dictionary}
        
        # Index par position
        self.by_position: dict[int, dict[str, Set[str]]] = self._build_position_index()
        
        # Index par lettre présente
        self.by_letter: dict[str, Set[str]] = self._build_letter_index()
    
    def _build_position_index(self) -> dict[int, dict[str, Set[str]]]:
        """Construit un index des mots par lettre à chaque position."""
        index = {i: {} for i in range(5)}
        
        for word in self.dictionary:
            for pos, letter in enumerate(word):
                if letter not in index[pos]:
                    index[pos][letter] = set()
                index[pos][letter].add(word)
        
        return index
    
    def _build_letter_index(self) -> dict[str, Set[str]]:
        """Construit un index des mots contenant chaque lettre."""
        index = {}
        
        for word in self.dictionary:
            for letter in set(word):
                if letter not in index:
                    index[letter] = set()
                index[letter].add(word)
        
        return index
    
    def filter_by_constraints(self, constraint_manager: ConstraintManager) -> Set[str]:
        """
        Filtre rapidement selon les contraintes en utilisant les index.
        
        Args:
            constraint_manager: Le gestionnaire de contraintes
            
        Returns:
            Ensemble de mots valides
        """
        candidates = self.dictionary.copy()
        
        # Filtrer par positions correctes (très sélectif)
        for pos, letter in constraint_manager.correct_positions.items():
            if letter in self.by_position[pos]:
                candidates &= self.by_position[pos][letter]
            else:
                return set()  # Aucun mot possible
        
        # Filtrer par lettres présentes
        for letter in constraint_manager.present_letters.keys():
            if letter in self.by_letter:
                candidates &= self.by_letter[letter]
            else:
                return set()
        
        # Filtrer par lettres absentes
        for letter in constraint_manager.absent_letters:
            if letter in self.by_letter:
                candidates -= self.by_letter[letter]
        
        # Validation finale pour les contraintes complexes
        return {
            word for word in candidates
            if constraint_manager.is_word_valid(word)
        }
