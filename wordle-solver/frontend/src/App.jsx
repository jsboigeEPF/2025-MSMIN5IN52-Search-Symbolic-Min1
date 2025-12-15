import React, { useState, useEffect, useCallback } from 'react';
import { Brain, Github } from 'lucide-react';
import WordleGrid from './components/WordleGrid';
import Keyboard from './components/Keyboard';
import SuggestionsPanel from './components/SuggestionsPanel';
import GameControls from './components/GameControls';
import GameStats from './components/GameStats';
import WordDefinition from './components/WordDefinition';
import wordleApi from './services/api';

function App() {
  // État du jeu
  const [gameId, setGameId] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [currentGuess, setCurrentGuess] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [isOver, setIsOver] = useState(false);
  const [isWon, setIsWon] = useState(false);
  const [loading, setLoading] = useState(false);

  // État des suggestions
  const [suggestions, setSuggestions] = useState({
    suggestedWord: null,
    possibleWords: [],
    possibleWordsCount: 0,
    explanation: '',
    strategy: ''
  });

  // État du clavier
  const [letterStates, setLetterStates] = useState({});

  // Configuration
  const [languages, setLanguages] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [currentLanguage, setCurrentLanguage] = useState('en');

  // État pour les erreurs de connexion
  const [backendError, setBackendError] = useState(false);

  // Charger les langues et stratégies au démarrage
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const [langsData, stratsData] = await Promise.all([
          wordleApi.getLanguages(),
          wordleApi.getStrategies()
        ]);
        setLanguages(langsData.languages);
        setStrategies(stratsData.strategies);
        setBackendError(false);
      } catch (error) {
        console.error('Erreur lors du chargement de la configuration:', error);
        setBackendError(true);
      }
    };
    loadConfig();
  }, []);

  // Mettre à jour l'état du clavier en fonction des tentatives
  useEffect(() => {
    const newLetterStates = {};
    
    attempts.forEach(attempt => {
      attempt.guess.split('').forEach((letter, index) => {
        const feedback = attempt.feedbacks[index];
        
        // Ne pas downgrader l'état d'une lettre
        if (feedback === 'CORRECT') {
          newLetterStates[letter] = 'CORRECT';
        } else if (feedback === 'PRESENT' && newLetterStates[letter] !== 'CORRECT') {
          newLetterStates[letter] = 'PRESENT';
        } else if (feedback === 'ABSENT' && !newLetterStates[letter]) {
          newLetterStates[letter] = 'ABSENT';
        }
      });
    });
    
    setLetterStates(newLetterStates);
  }, [attempts]);

  // Démarrer une nouvelle partie
  const handleNewGame = async (language, strategy) => {
    setLoading(true);
    try {
      const response = await wordleApi.newGame(language, strategy);
      setGameId(response.game_id);
      setAttempts([]);
      setCurrentGuess('');
      setIsPlaying(true);
      setIsOver(false);
      setIsWon(false);
      setCurrentLanguage(language);
      setSuggestions({
        suggestedWord: null,
        possibleWords: [],
        possibleWordsCount: 0,
        explanation: '',
        strategy: ''
      });
      setLetterStates({});
      
      // Obtenir immédiatement les suggestions pour la première tentative
      setTimeout(() => handleGetSuggestion(response.game_id), 100);
    } catch (error) {
      console.error('Erreur lors de la création de la partie:', error);
      setBackendError(true);
      alert('❌ Erreur de connexion au backend.\n\n' +
            '📝 Solution :\n' +
            '1. Ouvrez un terminal\n' +
            '2. cd backend\n' +
            '3. python main.py\n\n' +
            'Consultez TROUBLESHOOTING.md pour plus d\'aide.');
    } finally {
      setLoading(false);
    }
  };

  // Obtenir des suggestions
  const handleGetSuggestion = async (gId = gameId) => {
    if (!gId) return;
    
    setLoading(true);
    try {
      const response = await wordleApi.getSuggestions(gId, 50);
      setSuggestions({
        suggestedWord: response.suggested_word,
        possibleWords: response.possible_words,
        possibleWordsCount: response.possible_words_count,
        explanation: response.explanation,
        strategy: response.strategy
      });
    } catch (error) {
      console.error('Erreur lors de la récupération des suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Faire une tentative
  const handleMakeGuess = async (guess) => {
    if (!gameId || isOver || guess.length !== 5) return;
    
    setLoading(true);
    try {
      const response = await wordleApi.makeGuess(gameId, guess);
      
      if (response.success) {
        setAttempts([...attempts, response.feedback]);
        setCurrentGuess('');
        setIsOver(response.is_over);
        setIsWon(response.is_won);
        
        // Mettre à jour les suggestions avec les mots possibles
        setSuggestions(prev => ({
          ...prev,
          possibleWords: response.possible_words,
          possibleWordsCount: response.possible_words_count
        }));
        
        // Si la partie n'est pas terminée, obtenir une nouvelle suggestion
        if (!response.is_over) {
          setTimeout(() => handleGetSuggestion(), 500);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la tentative:', error);
      alert(error.response?.data?.detail || 'Erreur lors de la tentative');
    } finally {
      setLoading(false);
    }
  };

  // Gérer les touches du clavier
  const handleKeyPress = useCallback((key) => {
    if (isOver || loading) return;
    
    if (key === 'BACKSPACE') {
      setCurrentGuess(prev => prev.slice(0, -1));
    } else if (key === 'ENTER') {
      if (currentGuess.length === 5) {
        handleMakeGuess(currentGuess);
      }
    } else if (currentGuess.length < 5 && /^[A-Z]$/.test(key)) {
      setCurrentGuess(prev => prev + key);
    }
  }, [currentGuess, isOver, loading]);

  // Écouter les touches du clavier physique
  useEffect(() => {
    const handlePhysicalKeyPress = (e) => {
      if (e.key === 'Backspace') {
        handleKeyPress('BACKSPACE');
      } else if (e.key === 'Enter') {
        handleKeyPress('ENTER');
      } else if (/^[a-zA-Z]$/.test(e.key)) {
        handleKeyPress(e.key.toUpperCase());
      }
    };

    window.addEventListener('keydown', handlePhysicalKeyPress);
    return () => window.removeEventListener('keydown', handlePhysicalKeyPress);
  }, [handleKeyPress]);

  // Sélectionner un mot depuis les suggestions
  const handleSelectWord = (word) => {
    if (!isOver && !loading) {
      setCurrentGuess(word);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="text-blue-600" size={32} />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Wordle Solver
                </h1>
                <p className="text-sm text-gray-600">
                  Solveur intelligent avec CSP + IA
                </p>
              </div>
            </div>
            <a
              href="https://github.com/ivanoffffff/2025-MSMIN5IN52-Search-Symbolic-Min1"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              <Github size={20} />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Erreur de connexion backend */}
        {backendError && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-red-900 mb-2">
                  ⚠️ Backend non accessible
                </h3>
                <p className="text-red-800 mb-3">
                  Le frontend ne peut pas se connecter au backend sur <code className="bg-red-100 px-2 py-1 rounded">http://localhost:8000</code>
                </p>
                <div className="bg-white border border-red-200 rounded p-4 mb-3">
                  <p className="font-semibold text-red-900 mb-2">📝 Solution :</p>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-red-800">
                    <li>Ouvrir un nouveau terminal</li>
                    <li>Aller dans le dossier : <code className="bg-red-50 px-1 rounded">cd backend</code></li>
                    <li>Démarrer le backend : <code className="bg-red-50 px-1 rounded">python main.py</code></li>
                    <li>Attendre le message : <code className="bg-red-50 px-1 rounded">Uvicorn running on http://0.0.0.0:8000</code></li>
                    <li>Rafraîchir cette page</li>
                  </ol>
                </div>
                <details className="text-sm">
                  <summary className="cursor-pointer text-red-700 hover:text-red-900 font-medium">
                    📚 Plus d'aide
                  </summary>
                  <div className="mt-2 text-red-700 space-y-1">
                    <p>• Consultez le fichier <code className="bg-red-50 px-1 rounded">TROUBLESHOOTING.md</code></p>
                    <p>• Exécutez le script de diagnostic : <code className="bg-red-50 px-1 rounded">./diagnose.sh</code></p>
                    <p>• Vérifiez que Python 3.8+ est installé</p>
                    <p>• Vérifiez que le port 8000 est libre</p>
                  </div>
                </details>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Colonne gauche : Contrôles */}
          <div className="space-y-6">
            <GameControls
              onNewGame={handleNewGame}
              onGetSuggestion={handleGetSuggestion}
              languages={languages}
              strategies={strategies}
              isPlaying={isPlaying}
              disabled={loading}
            />
            <GameStats
              attemptsCount={attempts.length}
              maxAttempts={6}
              possibleWordsCount={suggestions.possibleWordsCount}
              isWon={isWon}
              isOver={isOver}
            />
            
          </div>

          {/* Colonne centrale : Jeu */}
          <div className="lg:col-span-1">
            <div className="card">
              {!isPlaying && (
                <div className="text-center py-12">
                  <Brain className="mx-auto mb-4 text-blue-600" size={64} />
                  <h2 className="text-2xl font-bold mb-2">
                    Prêt à commencer ?
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Cliquez sur "Démarrer" pour lancer une nouvelle partie
                  </p>
                </div>
              )}

              {isPlaying && (
                <>
                  <WordleGrid
                    attempts={attempts}
                    currentGuess={currentGuess}
                    maxAttempts={6}
                  />
                  
                  <div className="mb-4">
                    <Keyboard
                      onKeyPress={handleKeyPress}
                      letterStates={letterStates}
                    />
                  </div>

                  {loading && (
                    <div className="text-center text-gray-600 py-2">
                      Chargement...
                    </div>
                  )}

                  {isOver && (
                    <div className="text-center">
                      <button
                        onClick={() => handleNewGame('en', 'frequency')}
                        className="btn-primary"
                      >
                        Nouvelle Partie
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Colonne droite : Suggestions */}
          <div className="space-y-6">
            <SuggestionsPanel
              suggestedWord={suggestions.suggestedWord}
              possibleWords={suggestions.possibleWords}
              possibleWordsCount={suggestions.possibleWordsCount}
              explanation={suggestions.explanation}
              strategy={suggestions.strategy}
              onSelectWord={handleSelectWord}
            />
            {/* Nouveau composant pour les définitions */}
            <WordDefinition language={currentLanguage} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-gray-600 text-sm">
          <p>
            Wordle Solver - Projet éducatif combinant CSP (OR-Tools) et IA
          </p>
          <p className="mt-1">
            Construit avec React, FastAPI, et OR-Tools
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
