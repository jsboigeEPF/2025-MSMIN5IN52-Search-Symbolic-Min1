import os
import time
import requests
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class GeminiLLM:
    """Service Gemini Wordle optimisé pour économiser le quota."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-flash-latest"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("La clé API Gemini n'est pas définie (GEMINI_API_KEY)")
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def suggest_word(
        self,
        candidates: List[str],
        feedback_history: Optional[List[Dict]] = None,
        word_length: int = 5,
        language: str = "fr",
        max_retries: int = 3,
        max_candidates_prompt: int = 30,
        max_output_tokens: int =200
    ) -> Tuple[str, str]:
        """Retourne le mot suggéré par le LLM avec optimisation et retry"""

        feedback_history = feedback_history or []
        candidates = [c for c in candidates if len(c) == word_length]
        if not candidates:
            raise ValueError("Aucun candidat de la longueur demandée")

        # Limiter le nombre de candidats dans le prompt
        prompt_candidates = candidates[:max_candidates_prompt]
        print("promptCandidat",prompt_candidates)

        prompt = f"""
Tu es un expert Wordle en {language.upper()}.
Choisis **UN SEUL mot** de {word_length} lettres parmi cette liste de candidats : {', '.join(prompt_candidates)}.

⚠️ IMPORTANT :
- Le mot doit avoir exactement {word_length} lettres.
- Le mot doit être présent dans la liste des candidats.
- Réponds uniquement dans ce format :

MOT: [le mot choisi]
EXPLICATION: [courte raison]

Choisis le mot avec les lettres les plus fréquentes et distinctes.
"""

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": max_output_tokens
            }
        }

        retries = 0
        while retries <= max_retries:
            try:
                response = requests.post(self.endpoint, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                print("RAW GEMINI RESPONSE:")
                print(data)
                # Extraction robuste du texte
                content = ""
                candidates_list = data.get("candidates", [])
                if candidates_list:
                    content_dict = candidates_list[0].get("content", {})
                    if "parts" in content_dict and content_dict["parts"]:
                        content = content_dict["parts"][0].get("text", "").strip()
                    elif "text" in content_dict:
                        content = content_dict["text"].strip()
                    elif "outputText" in content_dict:
                        content = content_dict["outputText"].strip()

                if not content:
                    return candidates[0].lower(), "Mot par défaut (LLM n'a pas renvoyé de texte)"

                # Parse mot et explication
                word = None
                explanation = "Suggestion basée sur l'analyse des lettres"
                for line in content.split("\n"):
                    if line.upper().startswith("MOT:"):
                        word = line.split(":", 1)[1].strip().lower()
                    elif line.upper().startswith("EXPLICATION:"):
                        explanation = line.split(":", 1)[1].strip()

                # Validation stricte
                if not word or len(word) != word_length or word.lower() not in [c.lower() for c in candidates]:
                    word = candidates[0].lower()
                    explanation = "Mot par défaut (LLM n'a pas choisi un candidat valide)"

                return word, explanation

            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    wait = 2 ** retries
                    print(f"⚠️ Quota atteint. Retry dans {wait}s...")
                    time.sleep(wait)
                    retries += 1
                    continue
                return candidates[0].lower(), f"Erreur API, mot par défaut: {str(e)}"
            except Exception as e:
                return candidates[0].lower(), f"Erreur parsing ou connexion, mot par défaut: {str(e)}"

        return candidates[0].lower(), "Mot par défaut après plusieurs tentatives (quota dépassé)"
