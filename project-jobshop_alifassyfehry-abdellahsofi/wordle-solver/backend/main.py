"""
API FastAPI pour le Wordle Solver.

Expose les fonctionnalités du solver via une API REST.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Set
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wordle_solver import (
    WordleGame,
    HybridSolver,
    ConstraintManager,
    DictionaryLoader,
    generate_feedback,
    FeedbackResult,
    Feedback
)
from wordle_solver.strategies import (
    FrequencyStrategy,
    EntropyStrategy,
    MinimaxStrategy,
    SimpleStrategy
)
from gemini_service import get_gemini_service

app = FastAPI(
    title="Wordle Solver API",
    description="API pour résoudre Wordle avec différentes stratégies",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache global pour les dictionnaires et solveurs
_solvers: Dict[str, HybridSolver] = {}
_strategies: Dict[str, any] = {}
_games: Dict[str, Dict] = {}  # game_id -> {game, constraint_manager, solver, strategy}


def get_solver(language: str) -> HybridSolver:
    """Récupère ou crée un solver pour une langue."""
    if language not in _solvers:
        dictionary = DictionaryLoader.load_language(language)
        _solvers[language] = HybridSolver(dictionary)
    return _solvers[language]


def get_strategy(strategy_name: str):
    """Récupère ou crée une stratégie."""
    if strategy_name not in _strategies:
        strategies_map = {
            'frequency': FrequencyStrategy(),
            'entropy': EntropyStrategy(max_words_to_evaluate=100),
            'minimax': MinimaxStrategy(),
            'simple': SimpleStrategy()
        }
        _strategies[strategy_name] = strategies_map.get(strategy_name, FrequencyStrategy())
    return _strategies[strategy_name]


# Modèles Pydantic
class NewGameRequest(BaseModel):
    language: str = "en"
    strategy: str = "frequency"
    target_word: Optional[str] = None


class GuessRequest(BaseModel):
    game_id: str
    guess: str


class SuggestRequest(BaseModel):
    game_id: str
    limit: int = 10


class GameState(BaseModel):
    game_id: str
    language: str
    strategy: str
    attempts: List[Dict]
    is_over: bool
    is_won: bool
    possible_words_count: int
    constraints: Dict


class SuggestionResponse(BaseModel):
    suggested_word: str
    possible_words: List[str]
    possible_words_count: int
    explanation: str


class WordDefinitionRequest(BaseModel):
    word: str
    language: str = "fr"


class WordDefinitionResponse(BaseModel):
    word: str
    language: str
    definition: Optional[str]
    success: bool
    error: Optional[str] = None


@app.get("/")
async def root():
    """Point d'entrée de l'API."""
    return {
        "message": "Wordle Solver API",
        "version": "1.0.0",
        "endpoints": {
            "new_game": "/api/game/new",
            "make_guess": "/api/game/guess",
            "get_suggestions": "/api/game/suggest",
            "get_state": "/api/game/state/{game_id}",
            "languages": "/api/languages",
            "strategies": "/api/strategies"
        }
    }


@app.get("/api/languages")
async def get_languages():
    """Retourne les langues disponibles."""
    return {
        "languages": [
            {"code": "en", "name": "English", "word_count": 15921},
            {"code": "fr", "name": "Français", "word_count": 6760}
        ]
    }


@app.get("/api/strategies")
async def get_strategies():
    """Retourne les stratégies disponibles."""
    return {
        "strategies": [
            {
                "id": "frequency",
                "name": "Fréquence",
                "description": "Maximise l'utilisation des lettres fréquentes",
                "speed": "fast",
                "recommended": True
            },
            {
                "id": "entropy",
                "name": "Entropie",
                "description": "Maximise l'information gagnée (théoriquement optimal)",
                "speed": "medium",
                "recommended": True
            },
            {
                "id": "minimax",
                "name": "Minimax",
                "description": "Minimise le pire cas possible",
                "speed": "medium",
                "recommended": False
            },
            {
                "id": "simple",
                "name": "Simple",
                "description": "Baseline alphabétique",
                "speed": "fast",
                "recommended": False
            }
        ]
    }


@app.post("/api/game/new")
async def new_game(request: NewGameRequest):
    """Crée une nouvelle partie."""
    import uuid
    import random
    
    game_id = str(uuid.uuid4())
    
    # Charger le dictionnaire et créer le solver
    solver = get_solver(request.language)
    strategy = get_strategy(request.strategy)
    
    # Choisir un mot cible
    if request.target_word:
        target_word = request.target_word.upper()
    else:
        # Choisir un mot aléatoire du dictionnaire
        dictionary = DictionaryLoader.load_language(request.language)
        target_word = random.choice(list(dictionary))
    
    # Créer la partie
    game = WordleGame(target_word)
    constraint_manager = ConstraintManager()
    
    # Stocker la partie
    _games[game_id] = {
        'game': game,
        'constraint_manager': constraint_manager,
        'solver': solver,
        'strategy': strategy,
        'language': request.language,
        'strategy_name': request.strategy,
        'target_word': target_word
    }
    
    return {
        "game_id": game_id,
        "language": request.language,
        "strategy": request.strategy,
        "message": "Nouvelle partie créée",
        "target_word_length": len(target_word)
    }


@app.post("/api/game/guess")
async def make_guess(request: GuessRequest):
    """Fait une tentative."""
    if request.game_id not in _games:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    game_data = _games[request.game_id]
    game = game_data['game']
    constraint_manager = game_data['constraint_manager']
    solver = game_data['solver']
    
    guess = request.guess.upper()
    
    try:
        # Faire la tentative
        feedback = game.make_guess(guess)
        
        # Appliquer les contraintes
        constraint_manager.apply_feedback(feedback)
        
        # Calculer les mots possibles
        possible_words = solver.get_possible_words(constraint_manager, limit=100)
        
        # Formater le feedback
        feedback_data = {
            'guess': feedback.guess,
            'feedbacks': [fb.name for fb in feedback.feedbacks],
            'display': feedback.to_string(),
            'correct_positions': feedback.get_correct_positions(),
            'present_letters': feedback.get_present_letters(),
            'absent_letters': list(feedback.get_absent_letters())
        }
        
        return {
            "success": True,
            "feedback": feedback_data,
            "is_over": game.is_over,
            "is_won": game.is_won,
            "attempts_count": len(game.attempts),
            "possible_words_count": len(possible_words),
            "possible_words": possible_words[:20],
            "constraints": constraint_manager.get_constraint_summary()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/game/suggest")
async def get_suggestions(request: SuggestRequest):
    """Obtient des suggestions de mots."""
    if request.game_id not in _games:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    game_data = _games[request.game_id]
    constraint_manager = game_data['constraint_manager']
    solver = game_data['solver']
    strategy = game_data['strategy']
    game = game_data['game']
    
    # Obtenir les mots possibles
    possible_words = solver.solve(constraint_manager, use_cpsat=False)
    
    if not possible_words:
        return {
            "suggested_word": None,
            "possible_words": [],
            "possible_words_count": 0,
            "explanation": "Aucun mot possible trouvé"
        }
    
    # Utiliser la stratégie pour choisir le meilleur mot
    attempt_number = len(game.attempts) + 1
    
    if attempt_number == 1:
        suggested = strategy.get_first_guess(game_data['language'])
    else:
        dictionary = DictionaryLoader.load_language(game_data['language'])
        suggested = strategy.choose_word(
            possible_words,
            constraint_manager,
            attempt_number,
            full_dictionary=dictionary
        )
    
    explanation = strategy.explain_choice(suggested, possible_words)
    
    return {
        "suggested_word": suggested,
        "possible_words": sorted(list(possible_words))[:request.limit],
        "possible_words_count": len(possible_words),
        "explanation": explanation,
        "strategy": game_data['strategy_name']
    }


@app.get("/api/game/state/{game_id}")
async def get_game_state(game_id: str):
    """Obtient l'état actuel d'une partie."""
    if game_id not in _games:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    game_data = _games[game_id]
    game = game_data['game']
    constraint_manager = game_data['constraint_manager']
    solver = game_data['solver']
    
    # Formater l'historique
    attempts = []
    for fb in game.get_history():
        attempts.append({
            'guess': fb.guess,
            'feedbacks': [f.name for f in fb.feedbacks],
            'display': fb.to_string()
        })
    
    # Calculer les mots possibles
    possible_words = solver.get_possible_words(constraint_manager, limit=100)
    
    return {
        "game_id": game_id,
        "language": game_data['language'],
        "strategy": game_data['strategy_name'],
        "attempts": attempts,
        "is_over": game.is_over,
        "is_won": game.is_won,
        "possible_words_count": len(possible_words),
        "possible_words": possible_words[:20],
        "constraints": constraint_manager.get_constraint_summary()
    }


@app.delete("/api/game/{game_id}")
async def delete_game(game_id: str):
    """Supprime une partie."""
    if game_id not in _games:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    del _games[game_id]
    return {"message": "Partie supprimée", "game_id": game_id}


@app.get("/api/stats")
async def get_stats():
    """Obtient des statistiques globales."""
    return {
        "active_games": len(_games),
        "loaded_dictionaries": list(_solvers.keys()),
        "available_strategies": list(_strategies.keys())
    }


@app.post("/api/word/definition")
async def get_word_definition(request: WordDefinitionRequest):
    """
    Obtient la définition d'un mot via l'API Gemini.
    
    Args:
        request: Contient le mot et la langue
    
    Returns:
        La définition du mot ou une erreur
    """
    gemini_service = get_gemini_service()
    
    if gemini_service is None:
        return WordDefinitionResponse(
            word=request.word,
            language=request.language,
            definition=None,
            success=False,
            error="Service Gemini non configuré. Veuillez ajouter GEMINI_API_KEY dans votre fichier .env"
        )
    
    try:
        definition = gemini_service.get_word_definition(
            word=request.word,
            language=request.language
        )
        
        if definition:
            return WordDefinitionResponse(
                word=request.word,
                language=request.language,
                definition=definition,
                success=True
            )
        else:
            return WordDefinitionResponse(
                word=request.word,
                language=request.language,
                definition=None,
                success=False,
                error="Impossible d'obtenir la définition"
            )
    
    except Exception as e:
        return WordDefinitionResponse(
            word=request.word,
            language=request.language,
            definition=None,
            success=False,
            error=f"Erreur: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
