"""
Module de simulation du jeu Wordle.

Permet de simuler une partie complète de Wordle avec :
- Choix d'un mot cible
- Jusqu'à 6 tentatives
- Génération automatique des feedbacks
- Suivi de l'historique
"""

from typing import List, Optional
from .feedback import FeedbackResult, generate_feedback
from .validator import WordValidator


class WordleGame:
    """Simulateur d'une partie de Wordle."""
    
    MAX_ATTEMPTS = 6
    
    def __init__(self, target_word: str, validator: Optional[WordValidator] = None):
        """
        Initialise une nouvelle partie de Wordle.
        
        Args:
            target_word: Le mot à deviner (5 lettres)
            validator: Validateur optionnel pour vérifier les tentatives
        """
        if len(target_word) != 5:
            raise ValueError("Le mot cible doit contenir exactement 5 lettres")
        
        self.target_word = target_word.upper()
        self.validator = validator or WordValidator()
        self.attempts: List[FeedbackResult] = []
        self.is_won = False
        self.is_over = False
    
    def get_remaining_attempts(self) -> int:
        """Retourne le nombre de tentatives restantes."""
        return self.MAX_ATTEMPTS - len(self.attempts)
    
    def get_attempt_number(self) -> int:
        """Retourne le numéro de la tentative actuelle (1-6)."""
        return len(self.attempts) + 1
    
    def make_guess(self, guess: str) -> FeedbackResult:
        """
        Fait une tentative de deviner le mot.
        
        Args:
            guess: Le mot deviné (5 lettres)
            
        Returns:
            FeedbackResult avec les retours pour chaque lettre
            
        Raises:
            ValueError: Si la partie est terminée ou le mot invalide
        """
        if self.is_over:
            raise ValueError("La partie est terminée")
        
        # Valider le mot
        is_valid, error = self.validator.validate(guess)
        if not is_valid:
            raise ValueError(f"Mot invalide : {error}")
        
        # Générer le feedback
        feedback = generate_feedback(guess, self.target_word)
        self.attempts.append(feedback)
        
        # Vérifier si gagné
        if feedback.is_correct():
            self.is_won = True
            self.is_over = True
        
        # Vérifier si plus de tentatives
        elif len(self.attempts) >= self.MAX_ATTEMPTS:
            self.is_over = True
        
        return feedback
    
    def get_history(self) -> List[FeedbackResult]:
        """Retourne l'historique complet des tentatives."""
        return self.attempts.copy()
    
    def get_last_feedback(self) -> Optional[FeedbackResult]:
        """Retourne le dernier feedback (ou None si aucune tentative)."""
        return self.attempts[-1] if self.attempts else None
    
    def get_game_state(self) -> dict:
        """
        Retourne l'état complet de la partie.
        
        Returns:
            Dictionnaire avec l'état de la partie
        """
        return {
            'target_word': self.target_word,
            'attempts': len(self.attempts),
            'max_attempts': self.MAX_ATTEMPTS,
            'remaining_attempts': self.get_remaining_attempts(),
            'is_won': self.is_won,
            'is_over': self.is_over,
            'history': [
                {
                    'guess': fb.guess,
                    'pattern': fb.to_pattern(),
                    'symbols': fb.to_string()
                }
                for fb in self.attempts
            ]
        }
    
    def reset(self, new_target: Optional[str] = None):
        """
        Réinitialise la partie.
        
        Args:
            new_target: Nouveau mot cible (optionnel, garde l'ancien si None)
        """
        if new_target:
            if len(new_target) != 5:
                raise ValueError("Le mot cible doit contenir exactement 5 lettres")
            self.target_word = new_target.upper()
        
        self.attempts = []
        self.is_won = False
        self.is_over = False
    
    def __str__(self) -> str:
        status = "Gagné" if self.is_won else ("Perdu" if self.is_over else "En cours")
        return f"Wordle [{status}] - Tentative {self.get_attempt_number()}/{self.MAX_ATTEMPTS}"
    
    def __repr__(self) -> str:
        return f"WordleGame(target='{self.target_word}', attempts={len(self.attempts)}, won={self.is_won})"


class WordleGameSimulator:
    """
    Simulateur pour tester des stratégies de résolution.
    
    Permet de jouer plusieurs parties automatiquement et collecter des statistiques.
    """
    
    def __init__(self, validator: Optional[WordValidator] = None):
        """
        Initialise le simulateur.
        
        Args:
            validator: Validateur de mots (optionnel)
        """
        self.validator = validator
        self.games_played = 0
        self.games_won = 0
        self.total_attempts = 0
        self.attempt_distribution = [0] * 7  # Index 0 = perdu, 1-6 = gagné en N tentatives
    
    def play_game(self, target_word: str, guesses: List[str]) -> WordleGame:
        """
        Joue une partie complète avec une séquence de tentatives.
        
        Args:
            target_word: Le mot cible
            guesses: Liste des tentatives à faire
            
        Returns:
            L'objet WordleGame avec les résultats
        """
        game = WordleGame(target_word, self.validator)
        
        for guess in guesses:
            if game.is_over:
                break
            try:
                game.make_guess(guess)
            except ValueError as e:
                print(f"Erreur lors de la tentative '{guess}': {e}")
                break
        
        # Mettre à jour les statistiques
        self.games_played += 1
        if game.is_won:
            self.games_won += 1
            self.total_attempts += len(game.attempts)
            self.attempt_distribution[len(game.attempts)] += 1
        else:
            self.attempt_distribution[0] += 1
        
        return game
    
    def get_statistics(self) -> dict:
        """
        Retourne les statistiques globales.
        
        Returns:
            Dictionnaire avec les stats
        """
        win_rate = (self.games_won / self.games_played * 100) if self.games_played > 0 else 0
        avg_attempts = (self.total_attempts / self.games_won) if self.games_won > 0 else 0
        
        return {
            'games_played': self.games_played,
            'games_won': self.games_won,
            'games_lost': self.games_played - self.games_won,
            'win_rate': round(win_rate, 2),
            'average_attempts': round(avg_attempts, 2),
            'attempt_distribution': {
                'lost': self.attempt_distribution[0],
                '1': self.attempt_distribution[1],
                '2': self.attempt_distribution[2],
                '3': self.attempt_distribution[3],
                '4': self.attempt_distribution[4],
                '5': self.attempt_distribution[5],
                '6': self.attempt_distribution[6],
            }
        }
    
    def reset_statistics(self):
        """Réinitialise toutes les statistiques."""
        self.games_played = 0
        self.games_won = 0
        self.total_attempts = 0
        self.attempt_distribution = [0] * 7
