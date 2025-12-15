"""
Module de validation des mots Wordle.

Vérifie que les mots respectent les règles :
- 5 lettres exactement
- Uniquement des lettres (pas de chiffres ou caractères spéciaux)
- Présent dans le dictionnaire autorisé
"""

import re
from typing import Set, Optional


class WordValidator:
    """Validateur de mots pour Wordle."""
    
    def __init__(self, valid_words: Optional[Set[str]] = None):
        """
        Initialise le validateur.
        
        Args:
            valid_words: Ensemble des mots valides (optionnel)
                        Si None, seules les règles de base sont vérifiées
        """
        self.valid_words = {word.upper() for word in valid_words} if valid_words else None
        self.pattern = re.compile(r'^[A-Za-z]{5}$')
    
    def is_valid_format(self, word: str) -> bool:
        """
        Vérifie que le mot a le bon format (5 lettres).
        
        Args:
            word: Le mot à vérifier
            
        Returns:
            True si le format est valide
        """
        return bool(self.pattern.match(word))
    
    def is_in_dictionary(self, word: str) -> bool:
        """
        Vérifie que le mot est dans le dictionnaire.
        
        Args:
            word: Le mot à vérifier
            
        Returns:
            True si le mot est dans le dictionnaire (ou si pas de dictionnaire chargé)
        """
        if self.valid_words is None:
            return True  # Pas de dictionnaire = accepter tous les mots
        return word.upper() in self.valid_words
    
    def is_valid(self, word: str) -> bool:
        """
        Vérifie que le mot est valide (format ET dictionnaire).
        
        Args:
            word: Le mot à vérifier
            
        Returns:
            True si le mot est valide
        """
        return self.is_valid_format(word) and self.is_in_dictionary(word)
    
    def validate(self, word: str) -> tuple[bool, Optional[str]]:
        """
        Valide un mot et retourne un message d'erreur si invalide.
        
        Args:
            word: Le mot à valider
            
        Returns:
            Tuple (is_valid, error_message)
            error_message est None si le mot est valide
        """
        if not word:
            return False, "Le mot ne peut pas être vide"
        
        if len(word) != 5:
            return False, f"Le mot doit contenir exactement 5 lettres (reçu: {len(word)})"
        
        if not self.is_valid_format(word):
            return False, "Le mot doit contenir uniquement des lettres"
        
        if not self.is_in_dictionary(word):
            return False, f"Le mot '{word.upper()}' n'est pas dans le dictionnaire"
        
        return True, None
    
    def get_valid_words(self) -> Set[str]:
        """
        Retourne l'ensemble des mots valides.
        
        Returns:
            Set de mots valides (vide si pas de dictionnaire)
        """
        return self.valid_words if self.valid_words else set()
    
    def count_valid_words(self) -> int:
        """
        Retourne le nombre de mots valides dans le dictionnaire.
        
        Returns:
            Nombre de mots (0 si pas de dictionnaire)
        """
        return len(self.valid_words) if self.valid_words else 0


def create_validator_from_file(filepath: str) -> WordValidator:
    """
    Crée un validateur à partir d'un fichier de mots.
    
    Args:
        filepath: Chemin vers le fichier contenant les mots (un par ligne)
        
    Returns:
        WordValidator avec les mots chargés
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            words = {line.strip().upper() for line in f if line.strip()}
        return WordValidator(words)
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier dictionnaire introuvable : {filepath}")
    except Exception as e:
        raise Exception(f"Erreur lors du chargement du dictionnaire : {e}")
