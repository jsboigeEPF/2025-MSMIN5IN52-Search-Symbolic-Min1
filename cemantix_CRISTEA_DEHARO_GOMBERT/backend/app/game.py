from typing import Dict, List, Optional, Tuple
from uuid import uuid4
import random
import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity

# Chargement du modèle de langue (contient les vecteurs sémantiques)
# On essaie d'abord le modèle large (plus précis), puis on fallback sur medium
print("Chargement du modèle spaCy...")
nlp = None
try:
    nlp = spacy.load("fr_core_news_lg")
    print("✓ Modèle 'fr_core_news_lg' chargé (vecteurs 300D, plus précis)")
except OSError:
    try:
        nlp = spacy.load("fr_core_news_md")
        print("⚠ Modèle 'fr_core_news_md' chargé (vecteurs 300D, moins précis)")
        print("  Pour de meilleurs résultats, installez 'fr_core_news_lg': python -m spacy download fr_core_news_lg")
    except OSError:
        raise RuntimeError("Aucun modèle spaCy trouvé. Lancez: python -m spacy download fr_core_news_lg (recommandé) ou fr_core_news_md")

class Game:
    def __init__(self, target: str, max_attempts: int = 6):
        self.id = str(uuid4())
        self.target = target
        self.attempts: int = 0
        self.max_attempts = max_attempts
        self.guesses: List[Tuple[str, float, int]] = []  # (guess, score, rank) 
        self.finished: bool = False
        self.won: bool = False
        self.target_revealed: bool = False  # Indique si le mot cible a été révélé manuellement

class GameManager:
    def __init__(self, vocab: List[str]):
        self.vocab = vocab
        self.games: Dict[str, Game] = {}
        
        # 1. Prétraitement : On ne garde que les mots connus du modèle spaCy
        # pour éviter les erreurs ou les vecteurs vides (zéro)
        self.valid_vocab = []
        vectors_list = []
        
        print("Indexation du vocabulaire...")
        # nlp.pipe est plus rapide pour traiter une liste
        for doc in nlp.pipe(self.vocab):
            # On ne garde que si le mot a un vecteur valide
            if doc.has_vector and doc.vector_norm > 0:
                self.valid_vocab.append(doc.text)
                vectors_list.append(doc.vector)
        
        self.vocab = self.valid_vocab
        # Matrice numpy contenant tous les vecteurs du vocabulaire
        self.vocab_vectors = np.array(vectors_list)
        print(f"Vocabulaire chargé : {len(self.vocab)} mots vectorisés.")

    def start_game(self, target: Optional[str] = None, max_attempts: int = 6) -> Game:
        if target is None:
            target = random.choice(self.vocab)
        # Si la cible demandée n'est pas dans notre vocabulaire vectorisé, on fallback
        if target not in self.vocab:
             # On essaye de trouver le mot s'il existe quand même dans spacy
             if not nlp(target).has_vector:
                 raise ValueError(f"Le mot cible '{target}' n'est pas connu du modèle sémantique.")
        
        g = Game(target=target, max_attempts=max_attempts)
        self.games[g.id] = g
        return g

    def score_guess(self, game_id: str, guess: str) -> Dict:
        if game_id not in self.games:
            raise KeyError("Partie introuvable")
        game = self.games[game_id]
        
        # Si la partie est gagnée, on ne peut plus jouer
        if game.finished and game.won:
            return {"error": "Partie terminée (gagnée)", "finished": True, "won": game.won, "target": game.target}
        
        # Initialiser target_revealed si la partie a été créée avant cette fonctionnalité
        if not hasattr(game, 'target_revealed'):
            game.target_revealed = False
        
        # Si la partie était perdue mais qu'on a ajouté des tentatives, on peut continuer
        # SAUF si le mot a été révélé (partie définitivement terminée)
        if game.finished and not game.won and not game.target_revealed:
            game.finished = False  # Réactiver la partie

        game.attempts += 1
        guess_norm = guess.strip()
        
        # --- Calcul UNIFIÉ du Score et du Rang ---
        # On calcule TOUJOURS avec le vocabulaire pour garantir la cohérence
        target_doc = nlp(game.target)
        guess_doc = nlp(guess_norm)

        # Si le mot n'a pas de vecteur (mot inconnu / faute de frappe)
        if not guess_doc.has_vector or guess_doc.vector_norm == 0:
            score = 0.0
            rank = len(self.vocab) + 1  # Dernier rang si pas de vecteur
        else:
            # Normaliser le vecteur cible pour un calcul cohérent
            target_vec_raw = target_doc.vector
            target_norm = np.linalg.norm(target_vec_raw)
            if target_norm > 0:
                target_vec_normalized = target_vec_raw / target_norm
            else:
                target_vec_normalized = target_vec_raw
            
            target_vec = target_vec_normalized.reshape(1, -1)
            
            # Normaliser les vecteurs du vocabulaire pour un calcul cohérent
            vocab_norms = np.linalg.norm(self.vocab_vectors, axis=1, keepdims=True)
            vocab_norms = np.where(vocab_norms == 0, 1, vocab_norms)
            vocab_vectors_normalized = self.vocab_vectors / vocab_norms
            
            # Calculer la similarité cosinus entre la cible et TOUS les mots du vocabulaire
            # Cela garantit que le score et le rang sont calculés de la même manière
            sims = cosine_similarity(target_vec, vocab_vectors_normalized)[0]
            
            # Calculer le score du mot deviné avec la MÊME méthode que pour le vocabulaire
            # pour garantir la cohérence absolue entre score et rang
            guess_vec_raw = guess_doc.vector
            guess_norm_val = np.linalg.norm(guess_vec_raw)
            if guess_norm_val > 0:
                guess_vec_normalized = guess_vec_raw / guess_norm_val
            else:
                guess_vec_normalized = guess_vec_raw
            
            guess_vec = guess_vec_normalized.reshape(1, -1)
            # Calculer la similarité avec le vecteur cible normalisé (même méthode que pour vocab)
            score = float(cosine_similarity(target_vec, guess_vec)[0][0])
            
            # S'assurer que le score est dans [0, 1]
            score = max(0.0, min(1.0, score))
            
            # Si le mot est dans le vocabulaire, utiliser son score exact du tableau pour cohérence
            if guess_norm in self.vocab:
                idx = self.vocab.index(guess_norm)
                score_from_vocab = float(sims[idx])
                # Utiliser le score du vocabulaire pour garantir la cohérence exacte avec le rang
                score = score_from_vocab
            
            # Calculer le rang : combien de mots du vocabulaire ont un score supérieur ?
            # On utilise une comparaison avec une petite tolérance pour éviter les problèmes de précision
            # Le rang est calculé en comptant combien de mots du vocabulaire ont un score STRICTEMENT supérieur
            # puis on ajoute 1 (car le rang commence à 1, pas 0)
            rank = int(np.sum(sims > (score + 1e-10))) + 1
            
            # Note importante : Le score et le rang sont maintenant calculés de manière cohérente.
            # Si un mot est au rang 25 avec 20%, cela signifie qu'il y a 24 mots dans le vocabulaire
            # avec un score supérieur à 20%. Cela peut sembler contre-intuitif, mais c'est mathématiquement correct.
            # La similarité sémantique entre mots peut être faible même pour des mots "proches" conceptuellement.

        # Mise à jour état du jeu
        game.guesses.append((guess_norm, score, rank))

        # Condition de victoire (Score très proche de 1 ou mot identique)
        if guess_norm.lower() == game.target.lower():
            score = 1.0 # Force 1.0
            rank = 1
            game.finished = True
            game.won = True
        elif game.attempts >= game.max_attempts:
            # Marquer comme terminée seulement si on n'a pas gagné
            # Cela permet d'ajouter des tentatives plus tard si on a perdu
            if not game.won:
                game.finished = True
                game.won = False

        # Récupérer les mots les plus proches pour info (optionnel, aide au debug)
        # top_k_idx = sims.argsort()[::-1][:10]
        # top_k = [{"word": self.vocab[i], "sim": float(sims[i])} for i in top_k_idx]

        # Initialiser target_revealed si la partie a été créée avant cette fonctionnalité
        if not hasattr(game, 'target_revealed'):
            game.target_revealed = False
        
        # Révéler le mot cible seulement si la partie est gagnée OU si le mot a été révélé manuellement
        should_reveal_target = (game.finished and game.won) or (hasattr(game, 'target_revealed') and game.target_revealed)
        
        return {
            "game_id": game.id,
            "guess": guess_norm,
            "score": round(score * 100, 2), # En pourcentage souvent plus lisible (0-100)
            "rank": rank,
            "attempts": game.attempts,
            "remaining": max(0, game.max_attempts - game.attempts),
            "finished": game.finished,
            "won": game.won,
            # Révéler le mot cible seulement si gagné OU révélé manuellement
            "target": game.target if should_reveal_target else None,
            "history": [{"guess": g, "score": round(s * 100, 2), "rank": r} for g, s, r in game.guesses],
        }

    def get_vocab(self, limit: int = 200) -> List[str]:
        return self.vocab[:limit]