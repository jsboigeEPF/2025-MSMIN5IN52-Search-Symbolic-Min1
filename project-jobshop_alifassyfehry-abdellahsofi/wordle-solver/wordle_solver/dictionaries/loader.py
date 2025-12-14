"""
Module de chargement des dictionnaires de mots.

Gère le chargement des mots français et anglais depuis des fichiers.
"""

import os
from typing import Set
from pathlib import Path


class DictionaryLoader:
    """Chargeur de dictionnaires pour Wordle."""
    
    # Chemins par défaut
    DEFAULT_DIR = Path(__file__).parent
    EN_FILE = "en_words.txt"
    FR_FILE = "fr_words.txt"
    
    @staticmethod
    def load_from_file(filepath: str) -> Set[str]:
        """
        Charge un dictionnaire depuis un fichier.
        
        Args:
            filepath: Chemin vers le fichier
            
        Returns:
            Ensemble de mots (en majuscules)
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fichier introuvable : {filepath}")
        
        words = set()
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().upper()
                if len(word) == 5 and word.isalpha():
                    words.add(word)
        
        return words
    
    @classmethod
    def load_english(cls, custom_path: str = None) -> Set[str]:
        """
        Charge le dictionnaire anglais.
        
        Args:
            custom_path: Chemin personnalisé (optionnel)
            
        Returns:
            Ensemble de mots anglais
        """
        path = custom_path or str(cls.DEFAULT_DIR / cls.EN_FILE)
        return cls.load_from_file(path)
    
    @classmethod
    def load_french(cls, custom_path: str = None) -> Set[str]:
        """
        Charge le dictionnaire français.
        
        Args:
            custom_path: Chemin personnalisé (optionnel)
            
        Returns:
            Ensemble de mots français
        """
        path = custom_path or str(cls.DEFAULT_DIR / cls.FR_FILE)
        return cls.load_from_file(path)
    
    @classmethod
    def load_language(cls, language: str, custom_path: str = None) -> Set[str]:
        """
        Charge un dictionnaire selon la langue.
        
        Args:
            language: 'en' ou 'fr'
            custom_path: Chemin personnalisé (optionnel)
            
        Returns:
            Ensemble de mots
            
        Raises:
            ValueError: Si la langue n'est pas supportée
        """
        if language.lower() == 'en':
            return cls.load_english(custom_path)
        elif language.lower() == 'fr':
            return cls.load_french(custom_path)
        else:
            raise ValueError(f"Langue non supportée : {language}. Utilisez 'en' ou 'fr'.")
    
    @staticmethod
    def save_to_file(words: Set[str], filepath: str):
        """
        Sauvegarde un dictionnaire dans un fichier.
        
        Args:
            words: Ensemble de mots à sauvegarder
            filepath: Chemin du fichier de sortie
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            for word in sorted(words):
                f.write(f"{word.upper()}\n")
    
    @staticmethod
    def merge_dictionaries(*dictionaries: Set[str]) -> Set[str]:
        """
        Fusionne plusieurs dictionnaires.
        
        Args:
            *dictionaries: Dictionnaires à fusionner
            
        Returns:
            Dictionnaire fusionné
        """
        merged = set()
        for dictionary in dictionaries:
            merged.update(dictionary)
        return merged
    
    @staticmethod
    def filter_by_length(words: Set[str], length: int) -> Set[str]:
        """
        Filtre les mots par longueur.
        
        Args:
            words: Ensemble de mots
            length: Longueur désirée
            
        Returns:
            Mots de la longueur spécifiée
        """
        return {word for word in words if len(word) == length}
    
    @staticmethod
    def get_statistics(words: Set[str]) -> dict:
        """
        Retourne des statistiques sur un dictionnaire.
        
        Args:
            words: Ensemble de mots
            
        Returns:
            Dictionnaire avec statistiques
        """
        if not words:
            return {
                'total_words': 0,
                'unique_letters': 0,
                'avg_unique_letters_per_word': 0
            }
        
        all_letters = set()
        unique_letters_per_word = []
        
        for word in words:
            letters = set(word)
            all_letters.update(letters)
            unique_letters_per_word.append(len(letters))
        
        return {
            'total_words': len(words),
            'unique_letters': len(all_letters),
            'avg_unique_letters_per_word': sum(unique_letters_per_word) / len(unique_letters_per_word),
            'letters': sorted(all_letters)
        }
