from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import random
import uuid

from app.data.load_fr_word import load_fr_words
from app.data.load_en_word import load_en_words
from app.services.csp_solver import CSPSolver, WordleConstraints
from app.services.csp_llm_solver import HybridWordleSolver
from app.services.llm_service import GeminiLLM
from app.models.schemas import Feedback, WordSuggestionsRequest

router = APIRouter()

# Dictionnaires
words_fr = load_fr_words()
words_en = load_en_words()

# Solveurs CSP
csp_solver_fr = CSPSolver(word_length=5)
csp_solver_fr.set_valid_words(words_fr)

csp_solver_en = CSPSolver(word_length=5)
csp_solver_en.set_valid_words(words_en)

# Solveurs hybrides
hybrid_solver_fr = HybridWordleSolver(words_fr)
hybrid_solver_en = HybridWordleSolver(words_en)

# Service LLM
llm_service = GeminiLLM()

# 🎮 STOCKAGE DES PARTIES ACTIVES
# Format: {session_id: {"secret_word": "xxxxx", "language": "fr", "attempts": 0}}
active_games: Dict[str, Dict] = {}


class WordleRequest(BaseModel):
    feedback: Feedback
    language: Optional[str] = "fr"
    previous_guesses: Optional[List[str]] = []
    session_id: Optional[str] = None


class StartGameResponse(BaseModel):
    session_id: str
    message: str


def filter_already_guessed(candidates: List[str], previous_guesses: List[str]) -> List[str]:
    """Filtre les mots déjà essayés"""
    previous_lower = [g.lower() for g in previous_guesses]
    return [c for c in candidates if c.lower() not in previous_lower]


# ============================================================
# ROUTE 0 — DÉMARRER UNE NOUVELLE PARTIE
# ============================================================
@router.post("/start", response_model=StartGameResponse)
def start_game(language: str = "fr"):
    """Démarre une nouvelle partie et retourne un session_id"""
    lang = language.lower()
    word_list = words_fr if lang == "fr" else words_en
    
    session_id = str(uuid.uuid4())
    secret_word = random.choice(word_list).lower()
    
    # Stocker la partie
    active_games[session_id] = {
        "secret_word": secret_word,
        "language": lang,
        "attempts": 0
    }
    
    # Reset du solveur pour cette langue
    solver = hybrid_solver_fr if lang == "fr" else hybrid_solver_en
    solver.reset()
    
    print(f"🆕 [{session_id[:8]}] Nouvelle partie - Mot secret: {secret_word.upper()}")
    
    return StartGameResponse(
        session_id=session_id,
        message=f"Nouvelle partie démarrée ! Mot secret caché."
    )


# ============================================================
# ROUTE 1 — VÉRIFIER UN MOT
# ============================================================
@router.post("/check")
def check_guess(
    session_id: str,
    guess: str,
    language: str = "fr"
):
    """Vérifie un mot contre le mot secret et retourne le feedback"""
    
    if session_id not in active_games:
        raise HTTPException(status_code=404, detail="Session introuvable. Démarrez une nouvelle partie avec /start")
    
    game = active_games[session_id]
    secret_word = game["secret_word"]
    guess = guess.lower()
    
    # Vérifier que le mot est valide
    word_list = words_fr if language == "fr" else words_en
    if guess not in [w.lower() for w in word_list]:
        raise HTTPException(status_code=400, detail=f"Mot invalide : {guess}")
    
    game["attempts"] += 1
    
    # Calculer le feedback
    feedback = {
        "green": {},
        "yellow": {},
        "grey": []
    }
    
    secret_counts = {}
    for letter in secret_word:
        secret_counts[letter] = secret_counts.get(letter, 0) + 1
    
    # Lettres vertes
    for i, (g, t) in enumerate(zip(guess, secret_word)):
        if g == t:
            feedback["green"][i] = g
            secret_counts[g] -= 1
    
    # Lettres jaunes et grises
    for i, g in enumerate(guess):
        if i in feedback["green"]:
            continue
        if g in secret_counts and secret_counts[g] > 0:
            if i not in feedback["yellow"]:
                feedback["yellow"][i] = []
            feedback["yellow"][i].append(g)
            secret_counts[g] -= 1
        else:
            if g not in feedback["grey"]:
                feedback["grey"].append(g)
    
    is_win = (guess == secret_word)
    is_game_over = is_win or game["attempts"] >= 6
    
    result = {
        "feedback": feedback,
        "is_correct": is_win,
        "is_game_over": is_game_over,
        "attempts": game["attempts"]
    }
    
    if is_game_over:
        result["secret_word"] = secret_word.upper()
        print(f"🏁 [{session_id[:8]}] Partie terminée - {'Gagné' if is_win else 'Perdu'}")
        del active_games[session_id]
    
    return result


# ============================================================
# ROUTE 2 — SUGGESTION CSP
# ============================================================
@router.post("/suggest/csp")
def suggest_csp(req: WordleRequest):
    """Suggère un mot basé sur CSP uniquement"""
    lang = (req.language or "fr").lower()
    solver = csp_solver_fr if lang == "fr" else csp_solver_en

    # Créer des contraintes locales (ne pas toucher au solver global)
    constraints = WordleConstraints()
    constraints.update(req.feedback.dict())
    
    candidates = solver.filter_candidates(constraints)
    
    if not candidates:
        return {
            "suggested_word": None,
            "explanation": "Aucun candidat trouvé",
            "candidates_count": 0,
            "candidates": []
        }
    
    # Filtrer les mots déjà essayés
    filtered_candidates = filter_already_guessed(candidates, req.previous_guesses or [])
    if not filtered_candidates:
        filtered_candidates = candidates
    
    next_guess = random.choice(filtered_candidates)
    
    return {
        "suggested_word": next_guess.upper(),
        "explanation": f"Suggestion CSP parmi {len(filtered_candidates)} candidats",
        "candidates_count": len(filtered_candidates),
        "candidates": [c.upper() for c in filtered_candidates[:30]]
    }


# ============================================================
# ROUTE 3 — SUGGESTION HYBRIDE
# ============================================================
@router.post("/suggest/hybrid")
def suggest_hybrid(req: WordleRequest):
    """Suggère un mot basé sur CSP + LLM"""
    lang = (req.language or "fr").lower()
    solver = hybrid_solver_fr if lang == "fr" else hybrid_solver_en

    # Reset si nouvelle session
    if not req.previous_guesses or len(req.previous_guesses) == 0:
        solver.reset()
        print(f"🔄 [HYBRID] Reset du solveur pour nouvelle session")
    
    # Mettre à jour les contraintes
    solver.update_constraints(req.feedback.dict())
    
    try:
        candidates = solver.csp.filter_candidates(solver.constraints)
        
        if not candidates:
            return {
                "suggested_word": None,
                "explanation": "Aucun candidat trouvé",
                "candidates_count": 0,
                "candidates": []
            }
        
        # Filtrer les mots déjà essayés
        filtered_candidates = filter_already_guessed(candidates, req.previous_guesses or [])
        if not filtered_candidates:
            filtered_candidates = candidates
        
        # LLM suggère
        llm_word, llm_explanation = llm_service.suggest_word(
            candidates=list(filtered_candidates)[:50],
            feedback_history=[solver.constraints_dict()],
            word_length=5,
            language=lang
        )
        
        # Double vérification
        if llm_word.lower() in [g.lower() for g in (req.previous_guesses or [])]:
            llm_word = filtered_candidates[0] if filtered_candidates else candidates[0]
            llm_explanation = "Mot alternatif (LLM déjà essayé)"
        
        return {
            "suggested_word": llm_word.upper(),
            "explanation": f"{llm_explanation} ({len(filtered_candidates)} candidats)",
            "candidates_count": len(filtered_candidates),
            "candidates": [c.upper() for c in filtered_candidates[:30]]
        }
    
    except Exception as e:
        print(f"❌ Erreur Hybrid: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ROUTE 4 — SUGGESTION IA PURE
# ============================================================
@router.post("/suggest/ai")
def suggest_ai(req: WordSuggestionsRequest):
    """Suggère un mot basé sur IA uniquement"""
    lang = req.language.lower()
    solver = hybrid_solver_fr if lang == "fr" else hybrid_solver_en

    # Reset si nouvelle session
    if not req.previous_guesses or len(req.previous_guesses) == 0:
        solver.reset()
        print(f"🔄 [AI] Reset du solveur pour nouvelle session")
    
    solver.update_constraints(req.feedback.dict())
    candidates = solver.csp.filter_candidates(solver.constraints)
    
    if not candidates:
        raise HTTPException(status_code=400, detail="Aucun candidat trouvé")
    
    # Filtrer les mots déjà essayés
    filtered_candidates = filter_already_guessed(candidates, req.previous_guesses or [])
    if not filtered_candidates:
        filtered_candidates = candidates
    
    llm_word, llm_explanation = llm_service.suggest_word(
        candidates=list(filtered_candidates)[:50],
        feedback_history=[],
        word_length=5,
        language=lang
    )
    
    # Double vérification
    if llm_word.lower() in [g.lower() for g in (req.previous_guesses or [])]:
        llm_word = filtered_candidates[0] if filtered_candidates else candidates[0]
        llm_explanation = "Mot alternatif (IA déjà essayé)"
    
    return {
        "suggested_word": llm_word.upper(),
        "explanation": llm_explanation,
        "candidates_count": len(filtered_candidates),
        "candidates": [c.upper() for c in filtered_candidates[:30]]

    }