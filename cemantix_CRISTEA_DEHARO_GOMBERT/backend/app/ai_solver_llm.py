"""
Module d'IA utilisant un LLM (Large Language Model) pour résoudre le Cemantix
Options cloud (non-local) :
- Hugging Face Inference API (gratuit, cloud)
- Google Gemini API (gratuit avec limitations, cloud)
- OpenAI API (payant, cloud)

Options local :
- Ollama (local, gratuit)
- Hugging Face Transformers (local, nécessite GPU)
"""
from typing import List, Dict, Optional
import os
import json

# Option 1 : Utiliser OpenAI API (cloud, payant)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Option 2 : Utiliser Ollama (local, gratuit)
try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Option 3 : Utiliser Hugging Face Transformers (local)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Option 4 : Utiliser Hugging Face Inference API (cloud, gratuit)
# Pas besoin d'installer transformers, juste requests
HF_INFERENCE_AVAILABLE = OLLAMA_AVAILABLE  # Utilise requests qui est déjà disponible

# Option 5 : Utiliser Google Gemini API (cloud, gratuit avec limitations)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class LLMSolver:
    """IA qui résout le Cemantix en utilisant un LLM pour raisonner"""
    
    def __init__(self, vocab: List[str], vocab_vectors=None, model_type: str = "ollama"):
        """
        Args:
            vocab: Liste des mots du vocabulaire
            vocab_vectors: Vecteurs du vocabulaire (optionnel, pour fallback)
            model_type: 
                Local (pas de clé API): "ollama" (par défaut), "huggingface"
                Cloud (nécessite clé API): "hf_inference", "gemini", "openai"
        """
        self.vocab = vocab
        self.vocab_vectors = vocab_vectors
        self.used_words = set()
        self.model_type = model_type
        
        # Initialiser selon le type de modèle
        if model_type == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY non définie. Utilisez 'hf_inference' (gratuit, pas de clé API) ou définissez la clé.")
            self.client = OpenAI(api_key=api_key)
            self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # ou "gpt-3.5-turbo" pour moins cher
            
        elif model_type == "hf_inference" and HF_INFERENCE_AVAILABLE:
            # Hugging Face Inference API (cloud, gratuit mais nécessite une clé API)
            self.hf_api_key = os.getenv("HF_API_KEY")
            if not self.hf_api_key:
                raise ValueError(
                    "HF_API_KEY non définie. La nouvelle API Hugging Face nécessite une clé API.\n"
                    "Obtenez une clé gratuite sur https://huggingface.co/settings/tokens\n"
                    "Puis définissez : export HF_API_KEY='hf_...'"
                )
            self.hf_model = os.getenv("HF_INFERENCE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
            # Utiliser la nouvelle URL router.huggingface.co (l'ancienne api-inference.huggingface.co n'est plus supportée)
            self.hf_api_url = f"https://router.huggingface.co/models/{self.hf_model}"
            print(f"Utilisation de Hugging Face Inference API (cloud) : {self.hf_model}")
            
        elif model_type == "gemini" and GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY non définie. Obtenez une clé gratuite sur https://makersuite.google.com/app/apikey")
            genai.configure(api_key=api_key)
            self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro")
            self.client = genai.GenerativeModel(self.gemini_model)
            print(f"Utilisation de Google Gemini API (cloud) : {self.gemini_model}")
            
        elif model_type == "ollama" and OLLAMA_AVAILABLE:
            self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2")  # ou "mistral", "qwen2.5"
            
        elif model_type == "huggingface" and HF_AVAILABLE:
            model_name = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
            print(f"Chargement du modèle Hugging Face (local): {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            print("Modèle chargé!")
        else:
            available = []
            if HF_INFERENCE_AVAILABLE:
                available.append("hf_inference (cloud, gratuit)")
            if GEMINI_AVAILABLE:
                available.append("gemini (cloud, gratuit)")
            if OPENAI_AVAILABLE:
                available.append("openai (cloud, payant)")
            if OLLAMA_AVAILABLE:
                available.append("ollama (local)")
            if HF_AVAILABLE:
                available.append("huggingface (local)")
            
            raise ValueError(
                f"Modèle {model_type} non disponible.\n"
                f"Options disponibles : {', '.join(available)}\n"
                f"Installez Ollama depuis https://ollama.ai et lancez 'ollama pull llama3.2'"
            )
    
    def _call_llm(self, prompt: str) -> str:
        """Appelle le LLM avec le prompt"""
        if self.model_type == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Tu es un expert en résolution de jeux de mots sémantiques. Tu dois analyser les indices et proposer le meilleur mot suivant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        
        elif self.model_type == "hf_inference":
            # Hugging Face Inference API (cloud, gratuit mais nécessite une clé API)
            headers = {
                "Authorization": f"Bearer {self.hf_api_key}",
                "Content-Type": "application/json"
            }
            
            # Construire le prompt pour l'API HF
            full_prompt = f"""Tu es un expert en résolution de jeux de mots sémantiques. Tu dois analyser les indices et proposer le meilleur mot suivant.

{prompt}"""
            
            response = requests.post(
                self.hf_api_url,
                headers=headers,
                json={
                    "inputs": full_prompt,
                    "parameters": {
                        "max_new_tokens": 50,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # L'API peut retourner une liste ou un dict
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
                elif isinstance(result, dict):
                    return result.get("generated_text", "").strip()
                return str(result).strip()
            elif response.status_code == 401:
                raise Exception(
                    f"Erreur Hugging Face API: 401 Unauthorized\n"
                    f"Vérifiez que votre clé API HF_API_KEY est correcte.\n"
                    f"Obtenez une clé gratuite sur https://huggingface.co/settings/tokens"
                )
            else:
                # Extraire le message d'erreur si c'est du JSON, sinon utiliser le texte
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", response.text)
                except:
                    error_msg = response.text[:200]  # Limiter la taille
                raise Exception(f"Erreur Hugging Face API: {response.status_code} - {error_msg}")
        
        elif self.model_type == "gemini":
            # Google Gemini API (cloud, gratuit avec limitations)
            response = self.client.generate_content(
                f"""Tu es un expert en résolution de jeux de mots sémantiques. Tu dois analyser les indices et proposer le meilleur mot suivant.

{prompt}"""
            )
            return response.text.strip()
        
        elif self.model_type == "ollama":
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100
                    }
                }
            )
            return response.json()["response"].strip()
        
        elif self.model_type == "huggingface":
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=inputs.input_ids.shape[1] + 100,
                temperature=0.7,
                do_sample=True
            )
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extraire seulement la partie générée (après le prompt)
            return generated_text[len(prompt):].strip()
        
        return ""
    
    def _build_prompt(self, history: List[Dict], available_words: List[str]) -> str:
        """Construit le prompt pour le LLM"""
        prompt = """Tu joues à Cemantix, un jeu où tu dois trouver un mot secret en français.
Tu as proposé des mots et reçu des scores de similarité sémantique (0-100%).

IMPORTANT : Le score mesure la similarité sémantique entre ton mot et le mot secret.
- 100% = mot exactement identique (victoire !)
- 90-99% = mots très proches sémantiquement (synonymes, variantes, mots de la même famille)
- 70-89% = mots proches (même domaine, concepts liés)
- 50-69% = mots moyennement liés
- < 50% = mots peu liés

Plus le score est élevé, plus le mot est proche du mot secret.

Historique COMPLET de toutes tes tentatives :
"""
        # Lister tous les mots déjà proposés avec leurs scores et rangs
        already_proposed = []
        
        for i, guess in enumerate(history, 1):
            rank_str = f"Rang {guess.get('rank', 'N/A')}" if guess.get('rank') else ""
            score = guess.get('score', 0)
            prompt += f"{i}. Mot: '{guess['guess']}' - Score: {score:.1f}% {rank_str}\n"
            already_proposed.append(guess['guess'])
        
        # Analyser les patterns pour aider le LLM
        if len(history) > 0:
            best_guess = max(history, key=lambda h: h.get('score', 0))
            best_score = best_guess.get('score', 0)
            prompt += f"\n📊 Analyse de l'historique :\n"
            prompt += f"- Meilleur score actuel : {best_score:.1f}% avec le mot '{best_guess['guess']}'\n"
            
            # Analyser la progression
            if len(history) >= 2:
                scores = [h.get('score', 0) for h in history]
                progression = scores[-1] - scores[0] if len(scores) > 1 else 0
                if progression > 0:
                    prompt += f"- Progression : +{progression:.1f}% depuis le début\n"
                elif progression < 0:
                    prompt += f"- Attention : {abs(progression):.1f}% de baisse depuis le début\n"
            
            # Analyser les tendances
            if len(history) >= 3:
                recent_scores = [h.get('score', 0) for h in history[-3:]]
                if all(recent_scores[i] <= recent_scores[i+1] for i in range(len(recent_scores)-1)):
                    prompt += f"- Tendance : Scores en amélioration constante !\n"
                elif all(recent_scores[i] >= recent_scores[i+1] for i in range(len(recent_scores)-1)):
                    prompt += f"- Tendance : Scores en baisse, change de stratégie\n"
        
        # Mentionner explicitement les mots déjà proposés
        if already_proposed:
            prompt += f"\n⚠️ Mots déjà proposés (à éviter absolument) : {', '.join(already_proposed)}\n"
        
        # Construire la stratégie selon le meilleur score
        strategy_text = ""
        if len(history) > 0 and best_guess:
            best_word = best_guess.get('guess', '')
            strategy_text = f"""
Stratégie selon le meilleur score ({best_score:.1f}%) :
- Score > 95% : Tu es très proche ! Cherche des synonymes, variantes, ou mots de la même famille que '{best_word}'
- Score 85-95% : Explore autour du meilleur mot '{best_word}', cherche des mots sémantiquement très proches
- Score 70-85% : Explore dans le même domaine sémantique que '{best_word}'
- Score 50-70% : Essaie de trianguler entre les meilleurs mots proposés pour trouver un point commun
- Score < 50% : Explore de nouveaux domaines sémantiques
"""
        else:
            strategy_text = """
Stratégie : C'est ton premier mot, choisis un mot commun et représentatif pour commencer l'exploration.
"""
        
        # Ajouter un avertissement sur la régression
        regression_warning = ""
        if len(history) > 0 and best_guess:
            best_word_str = best_guess.get('guess', '')
            regression_warning = f"""
🚨 CRITIQUE - ÉVITE LA RÉGRESSION :
- Ton meilleur score actuel est {best_score:.1f}% avec le mot '{best_word_str}'
- Tu DOIS proposer un mot qui a de bonnes chances d'être AU MOINS aussi bon que {best_score:.1f}%
- Ne propose JAMAIS un mot qui serait clairement moins bon que tes meilleures tentatives
- Si tu n'es pas sûr, choisis un mot sémantiquement très proche du meilleur mot '{best_word_str}' (score {best_score:.1f}%)
- PRIORITÉ ABSOLUE : Mieux vaut un mot proche de '{best_word_str}' qu'un mot aléatoire qui régresserait
"""
        
        prompt += f"""
Analyse TOUS ces indices et propose le meilleur mot suivant parmi ces options :
{', '.join(available_words[:50])}
{strategy_text}
{regression_warning}
⚠️ RÈGLES IMPORTANTES :
- Ne propose JAMAIS un mot déjà dans la liste des mots proposés ci-dessus
- Analyse TOUS les scores de l'historique pour comprendre la direction
- Si plusieurs mots ont des scores similaires, cherche ce qu'ils ont en commun
- Choisis un mot stratégique qui maximise tes chances de progresser OU au moins maintenir le meilleur score
- PRIORITÉ : Mieux vaut un mot proche du meilleur mot actuel qu'un mot aléatoire qui pourrait régresser

Réponds UNIQUEMENT avec le mot que tu proposes, sans explication ni ponctuation."""
        
        return prompt
    
    def find_best_guess(self, history: List[Dict]) -> Optional[str]:
        """Trouve le meilleur mot en utilisant le LLM avec validation anti-régression"""
        available_vocab = [w for w in self.vocab if w not in self.used_words]
        
        if not available_vocab:
            return None
        
        # Si pas d'historique, choisir un mot commun
        if not history:
            return available_vocab[0] if available_vocab else None
        
        # Obtenir le meilleur score actuel pour validation
        best_guess_data = max(history, key=lambda h: h.get('score', 0))
        best_score = best_guess_data.get('score', 0)
        best_word = best_guess_data.get('guess', '')
        
        # Construire le prompt
        prompt = self._build_prompt(history, available_vocab)
        
        try:
            # Appeler le LLM
            response = self._call_llm(prompt)
            
            # Nettoyer la réponse (enlever guillemets, espaces, etc.)
            guess = response.strip().strip('"').strip("'").strip()
            
            # Vérifier que le mot est dans le vocabulaire disponible
            if guess.lower() in [w.lower() for w in available_vocab]:
                # Trouver la version exacte (avec la bonne casse)
                for word in available_vocab:
                    if word.lower() == guess.lower():
                        # VALIDATION : Vérifier que le mot proposé est sémantiquement proche du meilleur mot
                        # pour éviter les régressions
                        validated_word = self._validate_guess(word, best_word, best_score, available_vocab)
                        return validated_word
            
            # Si le LLM a proposé un mot hors vocabulaire, utiliser le fallback heuristique
            return self._heuristic_fallback(best_word, best_score, available_vocab)
            
        except Exception as e:
            print(f"Erreur lors de l'appel LLM: {e}")
            # Fallback : utiliser l'heuristique
            return self._heuristic_fallback(best_word, best_score, available_vocab)
    
    def _validate_guess(self, proposed_word: str, best_word: str, best_score: float, available_vocab: List[str]) -> str:
        """Valide que le mot proposé n'est pas une régression évidente"""
        from .game import nlp
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Si le score est déjà très élevé (>90%), on veut être sûr que le nouveau mot est proche
        if best_score > 90:
            # Vérifier la similarité sémantique entre le mot proposé et le meilleur mot
            best_doc = nlp(best_word)
            proposed_doc = nlp(proposed_word)
            
            if best_doc.has_vector and proposed_doc.has_vector:
                similarity = float(best_doc.similarity(proposed_doc))
                # Si la similarité est très faible (<0.5), c'est probablement une régression
                if similarity < 0.5:
                    # Utiliser le fallback heuristique à la place
                    return self._heuristic_fallback(best_word, best_score, available_vocab)
        
        # Si le score est moyen-élevé (70-90%), on accepte mais on vérifie quand même
        elif best_score > 70:
            best_doc = nlp(best_word)
            proposed_doc = nlp(proposed_word)
            
            if best_doc.has_vector and proposed_doc.has_vector:
                similarity = float(best_doc.similarity(proposed_doc))
                # Si la similarité est très faible (<0.3), utiliser le fallback
                if similarity < 0.3:
                    return self._heuristic_fallback(best_word, best_score, available_vocab)
        
        # Sinon, accepter le mot proposé
        return proposed_word
    
    def _heuristic_fallback(self, best_word: str, best_score: float, available_vocab: List[str]) -> Optional[str]:
        """Fallback heuristique pour trouver un mot proche du meilleur mot"""
        from .game import nlp
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        if not available_vocab:
            return None
        
        best_doc = nlp(best_word)
        if not best_doc.has_vector:
            return available_vocab[0]
        
        # Trouver les mots les plus proches sémantiquement du meilleur mot
        best_vec = best_doc.vector.reshape(1, -1)
        
        # Obtenir les vecteurs des mots disponibles
        available_docs = [nlp(w) for w in available_vocab]
        available_vectors = np.array([doc.vector for doc in available_docs if doc.has_vector])
        available_words_filtered = [w for w, doc in zip(available_vocab, available_docs) if doc.has_vector]
        
        if len(available_vectors) == 0:
            return available_vocab[0]
        
        # Calculer les similarités
        similarities = cosine_similarity(best_vec, available_vectors)[0]
        
        # Selon le score actuel, choisir une stratégie
        if best_score > 90:
            # Score très élevé : prendre le mot le plus proche
            best_idx = np.argmax(similarities)
            return available_words_filtered[best_idx]
        elif best_score > 70:
            # Score élevé : prendre parmi les top 3
            top_3_indices = np.argsort(similarities)[::-1][:3]
            best_idx = top_3_indices[0]
            return available_words_filtered[best_idx]
        elif best_score > 50:
            # Score moyen : prendre parmi les top 5
            top_5_indices = np.argsort(similarities)[::-1][:5]
            best_idx = top_5_indices[0]
            return available_words_filtered[best_idx]
        else:
            # Score faible : prendre parmi les top 10
            top_10_indices = np.argsort(similarities)[::-1][:10]
            best_idx = top_10_indices[0]
            return available_words_filtered[best_idx]
    
    def solve_game(self, game_manager, game_id: str, max_iterations: int = 6) -> Dict:
        """Résout automatiquement une partie en utilisant le LLM"""
        if game_id not in game_manager.games:
            return {'success': False, 'error': 'Partie non trouvée'}
        
        game = game_manager.games[game_id]
        
        if game.finished:
            return {'success': False, 'error': 'Partie déjà terminée'}
        
        self.used_words = set()
        guesses_made = []
        
        for iteration in range(max_iterations):
            if game.finished:
                break
            
            history = [{"guess": g, "score": s * 100, "rank": r} for g, s, r in game.guesses]
            
            best_guess = self.find_best_guess(history)
            
            if not best_guess:
                break
            
            self.used_words.add(best_guess)
            
            try:
                result = game_manager.score_guess(game_id, best_guess)
                guesses_made.append({
                    'guess': best_guess,
                    'score': result.get('score', 0),
                    'rank': result.get('rank', 0)
                })
                
                if result.get('finished') and result.get('won'):
                    return {
                        'success': True,
                        'guesses': guesses_made,
                        'target': result.get('target'),
                        'attempts': len(guesses_made)
                    }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {
            'success': False,
            'guesses': guesses_made,
            'target': game.target if game.finished else None,
            'attempts': len(guesses_made)
        }

