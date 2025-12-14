from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
import asyncio
from pathlib import Path

from .game import GameManager
from .ai_solver import AISolver

BASE_DIR = Path(__file__).resolve().parent
VOCAB_FILE = BASE_DIR / "vocab.txt"

if not VOCAB_FILE.exists():
    raise RuntimeError(f"Fichier vocab introuvable : {VOCAB_FILE}")

with VOCAB_FILE.open(encoding="utf-8") as f:
    vocab = [line.strip() for line in f if line.strip()]

game_manager = GameManager(vocab=vocab)

app = FastAPI(title="Cemantix léger (FR)")

# Autoriser le frontend local (Angular) à accéder à l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Nécessaire pour SSE
)

class StartPayload(BaseModel):
    target: Optional[str] = None
    max_attempts: Optional[int] = 6

class GuessPayload(BaseModel):
    game_id: str
    guess: str

class AddAttemptsPayload(BaseModel):
    game_id: str
    additional_attempts: int

class RevealTargetPayload(BaseModel):
    game_id: str

class AISolvePayload(BaseModel):
    game_id: str
    use_llm: Optional[bool] = None  # None = utiliser la variable d'environnement USE_LLM (True par défaut)
    llm_model: Optional[str] = None  # None = utiliser la variable d'environnement LLM_MODEL ("ollama" par défaut - local, gratuit, pas de clé API)

class AISuggestPayload(BaseModel):
    game_id: str
    llm_model: Optional[str] = None  # None = utiliser la variable d'environnement LLM_MODEL ("ollama" par défaut - local, gratuit, pas de clé API)

@app.get("/game/{game_id}")
def get_game_status(game_id: str):
    """Récupère le statut et l'historique d'une partie sans faire de guess"""
    if game_id not in game_manager.games:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    game = game_manager.games[game_id]
    
    # Initialiser target_revealed si la partie a été créée avant cette fonctionnalité
    if not hasattr(game, 'target_revealed'):
        game.target_revealed = False
    
    # Révéler le mot cible seulement si la partie est gagnée OU si le mot a été révélé manuellement
    should_reveal_target = (game.finished and game.won) or (hasattr(game, 'target_revealed') and game.target_revealed)
    
    return {
        "game_id": game.id,
        "attempts": game.attempts,
        "max_attempts": game.max_attempts,
        "finished": game.finished,
        "won": game.won,
        # Révéler le mot cible seulement si gagné OU révélé manuellement
        "target": game.target if should_reveal_target else None,
        "history": [{"guess": g, "score": round(s * 100, 2), "rank": r} for g, s, r in game.guesses]
    }

@app.post("/start")
def start_game(p: StartPayload):
    if p.target and p.target not in vocab:
        raise HTTPException(status_code=400, detail="Le mot cible doit appartenir au vocabulaire (ou laissez vide).")
    g = game_manager.start_game(target=p.target, max_attempts=p.max_attempts or 6)
    return {"message": "Partie démarrée", "game_id": g.id, "max_attempts": g.max_attempts}

@app.post("/guess")
def make_guess(p: GuessPayload):
    try:
        res = game_manager.score_guess(p.game_id, p.guess)
        return res
    except KeyError:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-attempts")
def add_attempts(p: AddAttemptsPayload):
    """Ajoute des tentatives supplémentaires à une partie terminée (perdue)"""
    try:
        if p.game_id not in game_manager.games:
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        game = game_manager.games[p.game_id]
        
        # Initialiser target_revealed si la partie a été créée avant cette fonctionnalité
        if not hasattr(game, 'target_revealed'):
            game.target_revealed = False
        
        # On ne peut ajouter des tentatives que si la partie est terminée ET perdue ET le mot n'est pas révélé
        if not game.finished:
            raise HTTPException(status_code=400, detail="La partie n'est pas encore terminée. Attendez que la partie se termine pour ajouter des tentatives.")
        
        if game.won:
            raise HTTPException(status_code=400, detail="Impossible d'ajouter des tentatives à une partie gagnée")
        
        # Si le mot a été révélé (partie définitivement terminée), on ne peut plus ajouter de tentatives
        if game.target_revealed:
            raise HTTPException(status_code=400, detail="Impossible d'ajouter des tentatives après avoir révélé le mot cible")
        
        if p.additional_attempts <= 0:
            raise HTTPException(status_code=400, detail="Le nombre de tentatives supplémentaires doit être positif")
        
        # Réactiver la partie et ajouter les tentatives
        game.max_attempts += p.additional_attempts
        game.finished = False  # Réactiver la partie
        
        return {
            "message": f"{p.additional_attempts} tentative(s) ajoutée(s)",
            "game_id": game.id,
            "max_attempts": game.max_attempts,
            "remaining": game.max_attempts - game.attempts,
            "finished": False
        }
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reveal-target")
def reveal_target(p: RevealTargetPayload):
    """Révèle le mot cible et termine définitivement la partie (défaite)"""
    try:
        if p.game_id not in game_manager.games:
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        game = game_manager.games[p.game_id]
        
        # Initialiser target_revealed si la partie a été créée avant cette fonctionnalité
        if not hasattr(game, 'target_revealed'):
            game.target_revealed = False
        
        # Si la partie est déjà gagnée, on peut quand même révéler
        if game.won:
            return {
                "message": "Partie déjà gagnée",
                "game_id": game.id,
                "target": game.target,
                "finished": True,
                "won": True
            }
        
        # Terminer définitivement la partie et révéler le mot
        game.finished = True
        game.won = False
        game.target_revealed = True  # Marquer que le mot a été révélé
        
        return {
            "message": "Mot cible révélé - Partie terminée",
            "game_id": game.id,
            "target": game.target,
            "finished": True,
            "won": False,
            "attempts": game.attempts,
            "max_attempts": game.max_attempts
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vocab")
def get_vocab(limit: Optional[int] = 200):
    return {"vocab": game_manager.get_vocab(limit)}

async def solve_game_stream(game_manager, game_id: str, use_llm: bool, llm_model: str, max_iterations: int):
    """Générateur qui stream les résultats de résolution en temps réel"""
    try:
        if game_id not in game_manager.games:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Partie non trouvée'})}\n\n"
            return
        
        game = game_manager.games[game_id]
        
        # Initialiser target_revealed si la partie a été créée avant cette fonctionnalité
        if not hasattr(game, 'target_revealed'):
            game.target_revealed = False
        
        # Si la partie est gagnée, on ne peut plus jouer
        if game.finished and game.won:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Partie déjà gagnée', 'won': game.won, 'target': game.target})}\n\n"
            return
        
        # Si la partie était perdue mais qu'on a ajouté des tentatives, on peut continuer
        # SAUF si le mot a été révélé (partie définitivement terminée)
        if game.finished and not game.won and not game.target_revealed:
            game.finished = False  # Réactiver la partie pour permettre de continuer
        
        # Choisir le type de solver
        if use_llm:
            from .ai_solver_llm import LLMSolver
            solver = LLMSolver(
                game_manager.vocab, 
                vocab_vectors=game_manager.vocab_vectors,
                model_type=llm_model
            )
        else:
            solver = AISolver(game_manager.vocab, game_manager.vocab_vectors)
        
        solver.used_words = set()
        guesses_made = []
        
        yield f"data: {json.dumps({'type': 'start', 'message': 'Début de la résolution...'})}\n\n"
        
        for iteration in range(max_iterations):
            if game.finished:
                break
            
            # Récupérer l'historique actuel
            history = [{"guess": g, "score": s * 100, "rank": r} for g, s, r in game.guesses]
            
            # Trouver le meilleur guess
            yield f"data: {json.dumps({'type': 'thinking', 'message': f'Réflexion... (tentative {iteration + 1}/{max_iterations})'})}\n\n"
            
            best_guess = solver.find_best_guess(history)
            
            if not best_guess:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Aucun mot disponible'})}\n\n"
                break
            
            solver.used_words.add(best_guess)
            
            # Faire le guess
            try:
                result = game_manager.score_guess(game_id, best_guess)
                
                guess_data = {
                    'guess': best_guess,
                    'score': result.get('score', 0),
                    'rank': result.get('rank', 0),
                    'attempt': iteration + 1
                }
                guesses_made.append(guess_data)
                
                # Envoyer le résultat en temps réel
                yield f"data: {json.dumps({'type': 'guess', 'data': guess_data})}\n\n"
                
                # Petit délai pour que l'utilisateur puisse voir
                await asyncio.sleep(0.5)
                
                if result.get('finished') and result.get('won'):
                    yield f"data: {json.dumps({'type': 'success', 'message': f'Mot trouvé en {len(guesses_made)} essai(s) !', 'target': result.get('target'), 'guesses': guesses_made})}\n\n"
                    return
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return
        
        # Partie terminée sans succès
        yield f"data: {json.dumps({'type': 'finished', 'message': f'Partie terminée après {len(guesses_made)} essai(s)', 'target': game.target if game.finished else None, 'guesses': guesses_made, 'success': False})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/ai/solve")
async def ai_solve(p: AISolvePayload):
    """Demande à l'IA de résoudre automatiquement la partie avec streaming en temps réel"""
    try:
        if p.game_id not in game_manager.games:
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        game = game_manager.games[p.game_id]
        
        # Déterminer si on utilise le LLM (par défaut: True pour ce projet)
        use_llm = p.use_llm if p.use_llm is not None else os.getenv("USE_LLM", "true").lower() == "true"
        # Par défaut, utiliser Ollama (local, gratuit, PAS de clé API nécessaire)
        llm_model = p.llm_model or os.getenv("LLM_MODEL", "ollama")
        
        max_iterations = game.max_attempts - game.attempts
        
        # Retourner une réponse streaming avec Server-Sent Events
        return StreamingResponse(
            solve_game_stream(game_manager, p.game_id, use_llm, llm_model, max_iterations),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except KeyError:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/suggest")
def ai_suggest(p: AISuggestPayload):
    """Obtient une suggestion unique du LLM pour le prochain mot à proposer"""
    try:
        if p.game_id not in game_manager.games:
            raise HTTPException(status_code=404, detail="Partie non trouvée")
        
        game = game_manager.games[p.game_id]
        
        if game.finished:
            return {
                "suggestion": None,
                "error": "Partie déjà terminée",
                "finished": True
            }
        
        # Utiliser le LLM par défaut (Ollama - local, gratuit, pas de clé API)
        llm_model = p.llm_model or os.getenv("LLM_MODEL", "ollama")
        
        from .ai_solver_llm import LLMSolver
        solver = LLMSolver(
            game_manager.vocab, 
            vocab_vectors=game_manager.vocab_vectors,
            model_type=llm_model
        )
        
        # Récupérer l'historique avec les scores et rangs
        history = [{"guess": g, "score": s * 100, "rank": r} for g, s, r in game.guesses]
        
        # Initialiser les mots déjà utilisés avec ceux de l'historique
        # C'est crucial pour que la suggestion soit différente à chaque fois
        solver.used_words = {g for g, _, _ in game.guesses}
        
        # Obtenir une suggestion basée sur l'historique actuel
        # C'est exactement ce que l'IA proposerait si elle jouait elle-même
        suggestion = solver.find_best_guess(history)
        
        if not suggestion:
            return {
                "suggestion": None,
                "error": "Aucune suggestion disponible"
            }
        
        return {
            "suggestion": suggestion,
            "history_count": len(history)
        }
        
    except KeyError:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
