"""
Service pour l'intégration avec l'API Gemini de Google.
Permet d'obtenir des définitions de mots.
"""

import os
from typing import Optional
from google import genai
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class GeminiService:
    """Service pour interagir avec l'API Gemini."""
    
    def __init__(self):
        """Initialise le client Gemini avec la clé API depuis les variables d'environnement."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY non trouvée dans les variables d'environnement. "
                "Veuillez créer un fichier .env avec votre clé API Gemini."
            )
        
        # Le client récupère automatiquement la clé depuis GEMINI_API_KEY
        self.client = genai.Client()
        self.model = "gemini-2.5-flash-lite"
    
    def get_word_definition(self, word: str, language: str = "fr") -> Optional[str]:
        """
        Obtient une définition simple d'un mot via l'API Gemini.
        
        Args:
            word: Le mot à définir
            language: La langue de la définition ("fr" ou "en")
        
        Returns:
            La définition du mot, ou None en cas d'erreur
        """
        try:
            # Construire le prompt selon la langue
            if language.lower() == "fr":
                prompt = f'Donne une définition simple et concise (maximum 2-3 phrases) du mot "{word}" en français.'
            else:
                prompt = f'Give a simple and concise definition (maximum 2-3 sentences) of the word "{word}" in English.'
            
            # Appel à l'API Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Erreur lors de la récupération de la définition: {e}")
            return None
    
    def get_word_info(self, word: str, language: str = "fr") -> Optional[dict]:
        """
        Obtient des informations détaillées sur un mot (définition + contexte).
        
        Args:
            word: Le mot à analyser
            language: La langue de l'information ("fr" ou "en")
        
        Returns:
            Un dictionnaire avec la définition et des exemples, ou None en cas d'erreur
        """
        try:
            # Construire le prompt selon la langue
            if language.lower() == "fr":
                prompt = (
                    f'Pour le mot "{word}", donne:\n'
                    f'1. Une définition simple (1-2 phrases)\n'
                    f'2. Un exemple d\'utilisation dans une phrase\n'
                    f'Réponds en français de manière concise.'
                )
            else:
                prompt = (
                    f'For the word "{word}", provide:\n'
                    f'1. A simple definition (1-2 sentences)\n'
                    f'2. An example of usage in a sentence\n'
                    f'Answer in English concisely.'
                )
            
            # Appel à l'API Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            text = response.text.strip()
            
            # Parser la réponse (basique)
            lines = text.split('\n')
            return {
                "word": word,
                "language": language,
                "full_text": text,
                "definition": text
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération des informations: {e}")
            return None


# Instance globale du service (singleton)
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> Optional[GeminiService]:
    """
    Retourne l'instance globale du service Gemini.
    Retourne None si la clé API n'est pas configurée.
    """
    global _gemini_service
    
    if _gemini_service is None:
        try:
            _gemini_service = GeminiService()
        except ValueError as e:
            print(f"⚠️  Service Gemini non disponible: {e}")
            return None
    
    return _gemini_service
