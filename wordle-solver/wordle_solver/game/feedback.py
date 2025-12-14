"""
Module de gestion des feedbacks Wordle.

Définit les types de retour possibles pour chaque lettre :
- CORRECT (vert) : lettre correcte à la bonne position
- PRESENT (jaune) : lettre présente mais mal placée
- ABSENT (gris) : lettre absente du mot
"""

from enum import Enum
from typing import List, Tuple


class Feedback(Enum):
    """Représente le feedback pour une lettre dans Wordle."""
    
    CORRECT = "correct"    # Vert - lettre à la bonne position
    PRESENT = "present"    # Jaune - lettre présente ailleurs
    ABSENT = "absent"      # Gris - lettre absente du mot
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_symbol(cls, symbol: str) -> "Feedback":
        """
        Crée un Feedback à partir d'un symbole.
        
        Args:
            symbol: '🟩' (vert), '🟨' (jaune), ou '⬜' (gris)
            
        Returns:
            Instance de Feedback correspondante
        """
        mapping = {
            '🟩': cls.CORRECT,
            '🟨': cls.PRESENT,
            '⬜': cls.ABSENT,
            'G': cls.CORRECT,  # Green
            'Y': cls.PRESENT,  # Yellow
            'B': cls.ABSENT,   # Black/Gray
        }
        return mapping.get(symbol.upper(), cls.ABSENT)
    
    def to_symbol(self) -> str:
        """Convertit le feedback en symbole visuel."""
        mapping = {
            Feedback.CORRECT: '🟩',
            Feedback.PRESENT: '🟨',
            Feedback.ABSENT: '⬜',
        }
        return mapping[self]
    
    def to_color(self) -> str:
        """Retourne le code couleur pour l'affichage CLI."""
        mapping = {
            Feedback.CORRECT: 'green',
            Feedback.PRESENT: 'yellow',
            Feedback.ABSENT: 'white',
        }
        return mapping[self]


class FeedbackResult:
    """Représente le résultat complet d'une tentative."""
    
    def __init__(self, guess: str, feedbacks: List[Feedback]):
        """
        Initialise un résultat de feedback.
        
        Args:
            guess: Le mot deviné
            feedbacks: Liste de 5 Feedback (un par lettre)
        """
        if len(guess) != 5:
            raise ValueError("Le mot doit contenir exactement 5 lettres")
        if len(feedbacks) != 5:
            raise ValueError("Il doit y avoir exactement 5 feedbacks")
        
        self.guess = guess.upper()
        self.feedbacks = feedbacks
    
    def is_correct(self) -> bool:
        """Vérifie si toutes les lettres sont correctes (mot trouvé)."""
        return all(fb == Feedback.CORRECT for fb in self.feedbacks)
    
    def get_correct_positions(self) -> List[Tuple[int, str]]:
        """
        Retourne les positions avec lettres correctes.
        
        Returns:
            Liste de tuples (position, lettre)
        """
        return [
            (i, self.guess[i]) 
            for i, fb in enumerate(self.feedbacks) 
            if fb == Feedback.CORRECT
        ]
    
    def get_present_letters(self) -> List[Tuple[int, str]]:
        """
        Retourne les lettres présentes mais mal placées.
        
        Returns:
            Liste de tuples (position_tentée, lettre)
        """
        return [
            (i, self.guess[i]) 
            for i, fb in enumerate(self.feedbacks) 
            if fb == Feedback.PRESENT
        ]
    
    def get_absent_letters(self) -> List[str]:
        """
        Retourne les lettres absentes du mot.
        
        Returns:
            Liste de lettres absentes
        """
        # Attention : une lettre peut être présente ET absente
        # (si elle apparaît 2 fois dans la tentative mais 1 seule fois dans le mot cible)
        present_or_correct = {
            self.guess[i] 
            for i, fb in enumerate(self.feedbacks) 
            if fb in (Feedback.CORRECT, Feedback.PRESENT)
        }
        
        return [
            self.guess[i] 
            for i, fb in enumerate(self.feedbacks) 
            if fb == Feedback.ABSENT and self.guess[i] not in present_or_correct
        ]
    
    def to_string(self) -> str:
        """Convertit le résultat en chaîne de caractères visuelle."""
        symbols = [fb.to_symbol() for fb in self.feedbacks]
        return f"{self.guess} {''.join(symbols)}"
    
    def to_pattern(self) -> str:
        """
        Convertit le résultat en pattern (pour debug/logs).
        
        Returns:
            String comme "GYBBG" (G=green, Y=yellow, B=black)
        """
        mapping = {
            Feedback.CORRECT: 'G',
            Feedback.PRESENT: 'Y',
            Feedback.ABSENT: 'B',
        }
        return ''.join(mapping[fb] for fb in self.feedbacks)
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __repr__(self) -> str:
        return f"FeedbackResult(guess='{self.guess}', pattern='{self.to_pattern()}')"


def generate_feedback(guess: str, target: str) -> FeedbackResult:
    """
    Génère le feedback pour une tentative donnée.
    
    Cette fonction implémente la logique exacte de Wordle pour gérer
    les cas complexes (lettres dupliquées, etc.).
    
    Args:
        guess: Le mot deviné (5 lettres)
        target: Le mot cible (5 lettres)
        
    Returns:
        FeedbackResult contenant les feedbacks pour chaque position
        
    Example:
        >>> generate_feedback("AROSE", "ROBOT")
        FeedbackResult(guess='AROSE', pattern='BYBBB')
    """
    guess = guess.upper()
    target = target.upper()
    
    if len(guess) != 5 or len(target) != 5:
        raise ValueError("Les mots doivent contenir exactement 5 lettres")
    
    feedbacks = [Feedback.ABSENT] * 5
    target_letters = list(target)
    
    # Premier passage : marquer les lettres correctes (vertes)
    for i in range(5):
        if guess[i] == target[i]:
            feedbacks[i] = Feedback.CORRECT
            target_letters[i] = None  # Marquer comme utilisée
    
    # Deuxième passage : marquer les lettres présentes (jaunes)
    for i in range(5):
        if feedbacks[i] == Feedback.ABSENT and guess[i] in target_letters:
            feedbacks[i] = Feedback.PRESENT
            # Retirer la première occurrence de cette lettre
            target_letters[target_letters.index(guess[i])] = None
    
    return FeedbackResult(guess, feedbacks)
