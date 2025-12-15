"""
Module de gestion des contraintes pour le CSP Wordle.

Maintient l'état des connaissances accumulées :
- Lettres correctes à chaque position (contraintes vertes)
- Lettres présentes mais mal placées (contraintes jaunes)
- Lettres absentes du mot (contraintes grises)
- Contraintes de fréquence pour les lettres dupliquées
"""

from typing import Dict, Set, List, Optional
from ..game.feedback import FeedbackResult, Feedback


class ConstraintManager:
    """
    Gère toutes les contraintes accumulées pendant la résolution.
    
    Les contraintes sont organisées en 4 catégories :
    1. correct_positions: {position: lettre} - lettres vertes
    2. present_letters: {lettre: set(positions_interdites)} - lettres jaunes
    3. absent_letters: set(lettres) - lettres grises
    4. letter_counts: {lettre: (min, max)} - contraintes de fréquence
    """
    
    def __init__(self):
        """Initialise un gestionnaire de contraintes vide."""
        # Positions connues (index 0-4)
        self.correct_positions: Dict[int, str] = {}
        
        # Lettres présentes mais positions où elles ne peuvent PAS être
        self.present_letters: Dict[str, Set[int]] = {}
        
        # Lettres absentes du mot
        self.absent_letters: Set[str] = set()
        
        # Contraintes de fréquence : {lettre: (min, max)}
        # min = nombre minimum d'occurrences
        # max = nombre maximum d'occurrences (None = illimité)
        self.letter_counts: Dict[str, tuple[int, Optional[int]]] = {}
    
    def apply_feedback(self, feedback: FeedbackResult):
        """
        Applique un nouveau feedback pour mettre à jour les contraintes.
        
        Args:
            feedback: Résultat d'une tentative
        """
        guess = feedback.guess
        
        # Compter les occurrences de chaque lettre dans le feedback
        letter_feedback_counts: Dict[str, Dict[str, int]] = {}
        for i, (letter, fb) in enumerate(zip(guess, feedback.feedbacks)):
            if letter not in letter_feedback_counts:
                letter_feedback_counts[letter] = {'correct': 0, 'present': 0, 'absent': 0}
            
            if fb == Feedback.CORRECT:
                letter_feedback_counts[letter]['correct'] += 1
            elif fb == Feedback.PRESENT:
                letter_feedback_counts[letter]['present'] += 1
            else:
                letter_feedback_counts[letter]['absent'] += 1
        
        # Traiter chaque lettre
        for i, (letter, fb) in enumerate(zip(guess, feedback.feedbacks)):
            if fb == Feedback.CORRECT:
                self._add_correct_position(i, letter)
            
            elif fb == Feedback.PRESENT:
                self._add_present_letter(letter, i)
            
            elif fb == Feedback.ABSENT:
                # Une lettre absente ne signifie pas toujours qu'elle n'est pas dans le mot
                # Elle peut apparaître ailleurs (si elle a aussi des feedbacks vert/jaune)
                counts = letter_feedback_counts[letter]
                if counts['correct'] == 0 and counts['present'] == 0:
                    # Vraiment absente du mot
                    self._add_absent_letter(letter)
                else:
                    # La lettre est présente, mais pas plus de fois que les vert+jaune
                    total_present = counts['correct'] + counts['present']
                    self._update_letter_count(letter, min_count=total_present, max_count=total_present)
    
    def _add_correct_position(self, position: int, letter: str):
        """Ajoute une contrainte de position correcte."""
        self.correct_positions[position] = letter
        
        # S'assurer que cette lettre est marquée comme présente
        if letter not in self.present_letters:
            self.present_letters[letter] = set()
        
        # Mettre à jour le compteur minimum
        current_min = self.letter_counts.get(letter, (0, None))[0]
        # Compter le nombre de positions correctes pour cette lettre
        correct_count = sum(1 for l in self.correct_positions.values() if l == letter)
        self._update_letter_count(letter, min_count=max(current_min, correct_count))
    
    def _add_present_letter(self, letter: str, forbidden_position: int):
        """Ajoute une contrainte de lettre présente."""
        if letter not in self.present_letters:
            self.present_letters[letter] = set()
        self.present_letters[letter].add(forbidden_position)
        
        # Mettre à jour le compteur minimum
        current_min = self.letter_counts.get(letter, (0, None))[0]
        self._update_letter_count(letter, min_count=max(current_min, 1))
    
    def _add_absent_letter(self, letter: str):
        """Ajoute une lettre absente."""
        self.absent_letters.add(letter)
        self._update_letter_count(letter, min_count=0, max_count=0)
    
    def _update_letter_count(self, letter: str, min_count: Optional[int] = None, max_count: Optional[int] = None):
        """
        Met à jour les contraintes de fréquence pour une lettre.
        
        Args:
            letter: La lettre concernée
            min_count: Nombre minimum d'occurrences (None = ne pas changer)
            max_count: Nombre maximum d'occurrences (None = ne pas changer)
        """
        current_min, current_max = self.letter_counts.get(letter, (0, None))
        
        if min_count is not None:
            current_min = max(current_min, min_count)
        
        if max_count is not None:
            if current_max is None:
                current_max = max_count
            else:
                current_max = min(current_max, max_count)
        
        self.letter_counts[letter] = (current_min, current_max)
    
    def is_word_valid(self, word: str) -> bool:
        """
        Vérifie si un mot respecte toutes les contraintes.
        
        Args:
            word: Le mot à vérifier (5 lettres en majuscules)
            
        Returns:
            True si le mot respecte toutes les contraintes
        """
        word = word.upper()
        
        if len(word) != 5:
            return False
        
        # Vérifier les positions correctes
        for pos, letter in self.correct_positions.items():
            if word[pos] != letter:
                return False
        
        # Vérifier les lettres absentes
        for letter in self.absent_letters:
            if letter in word:
                return False
        
        # Vérifier les lettres présentes et leurs positions interdites
        for letter, forbidden_positions in self.present_letters.items():
            if letter not in word:
                return False
            
            for pos in forbidden_positions:
                if word[pos] == letter:
                    return False
        
        # Vérifier les contraintes de fréquence
        letter_count_in_word = {}
        for letter in word:
            letter_count_in_word[letter] = letter_count_in_word.get(letter, 0) + 1
        
        for letter, (min_count, max_count) in self.letter_counts.items():
            count = letter_count_in_word.get(letter, 0)
            
            if count < min_count:
                return False
            
            if max_count is not None and count > max_count:
                return False
        
        return True
    
    def get_constraint_summary(self) -> dict:
        """
        Retourne un résumé des contraintes actuelles.
        
        Returns:
            Dictionnaire avec toutes les contraintes
        """
        return {
            'correct_positions': dict(self.correct_positions),
            'present_letters': {k: list(v) for k, v in self.present_letters.items()},
            'absent_letters': list(self.absent_letters),
            'letter_counts': dict(self.letter_counts),
            'total_constraints': len(self.correct_positions) + len(self.present_letters) + len(self.absent_letters)
        }
    
    def get_known_letters(self) -> Set[str]:
        """Retourne l'ensemble des lettres connues (vertes + jaunes)."""
        known = set(self.correct_positions.values())
        known.update(self.present_letters.keys())
        return known
    
    def get_unknown_positions(self) -> List[int]:
        """Retourne les positions qui ne sont pas encore connues."""
        return [i for i in range(5) if i not in self.correct_positions]
    
    def reset(self):
        """Réinitialise toutes les contraintes."""
        self.correct_positions.clear()
        self.present_letters.clear()
        self.absent_letters.clear()
        self.letter_counts.clear()
    
    def __str__(self) -> str:
        summary = self.get_constraint_summary()
        return f"ConstraintManager(constraints={summary['total_constraints']}, known_positions={len(self.correct_positions)})"
    
    def __repr__(self) -> str:
        return self.__str__()
