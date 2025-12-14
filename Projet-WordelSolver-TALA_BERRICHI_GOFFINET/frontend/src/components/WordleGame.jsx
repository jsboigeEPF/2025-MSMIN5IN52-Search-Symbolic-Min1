// frontend/src/components/WordleGame.jsx
import { useState, useCallback, useEffect } from "react";
import { GameBoard } from "./GameBoard";
import { Keyboard } from "./Keyboard";
import { SolverPanel } from "./SolverPanel";
import { GameStats } from "./GameStats";
import { toast } from "sonner";
import { Brain, Gamepad2, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { DarkModeToggle } from "./DarkModeToggle";

// Evaluation simple côté frontend pour l'affichage du board
function evaluateGuess(guess, target) {
  return guess.split("").map((letter, idx) => {
    if (!target) return { letter, state: "empty" };
    if (target[idx] === letter) return { letter, state: "correct" };
    else if (target.includes(letter)) return { letter, state: "present" };
    else return { letter, state: "absent" };
  });
}

export function WordleGame() {
  const [language, setLanguage] = useState("fr");
  const [targetWord, setTargetWord] = useState(""); // Le mot sera déterminé côté backend
  const [guesses, setGuesses] = useState([]);
  const [results, setResults] = useState([]);
  const [currentGuess, setCurrentGuess] = useState("");
  const [letterStates, setLetterStates] = useState(new Map());
  const [isRevealing, setIsRevealing] = useState(false);
  const [isGameOver, setIsGameOver] = useState(false);
  const [isWon, setIsWon] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState();
  const [isLoadingAI, setIsLoadingAI] = useState(false);

  const currentRow = guesses.length;

  // Mise à jour des états des lettres pour le clavier
  const updateLetterStates = useCallback((newResults) => {
    setLetterStates((prev) => {
      const updated = new Map(prev);
      for (const result of newResults) {
        const current = updated.get(result.letter);
        if (
          !current ||
          (current === "absent" && result.state !== "absent") ||
          (current === "present" && result.state === "correct")
        ) {
          updated.set(result.letter, result.state);
        }
      }
      return updated;
    });
  }, []);

  // Soumission du mot actuel
  const submitGuess = useCallback(async () => {
    if (currentGuess.length !== 5) {
      toast.error(language === "fr" ? "Le mot doit contenir 5 lettres" : "Word must be 5 letters");
      return;
    }
  
    setIsRevealing(true);
  
    try {
      // Construire le feedback depuis les résultats actuels
      const feedback = {
        green: {},
        yellow: {},
        grey: []
      };
      
      // Analyser les résultats précédents pour construire le feedback
      results.forEach((row) => {
        row.forEach((cell, idx) => {
          const letter = cell.letter.toLowerCase();
          
          if (cell.state === "correct") {
            feedback.green[idx] = letter;
          } else if (cell.state === "present") {
            if (!feedback.yellow[idx]) {
              feedback.yellow[idx] = [];
            }
            if (!feedback.yellow[idx].includes(letter)) {
              feedback.yellow[idx].push(letter);
            }
          } else if (cell.state === "absent") {
            if (!feedback.grey.includes(letter)) {
              feedback.grey.push(letter);
            }
          }
        });
      });
  
      // Appel au backend avec le bon format
      const res = await axios.post("/wordle/guess", {
        feedback: feedback,
        language: language,
        use_llm: false  // Mettez true si vous voulez utiliser le LLM
      });
  
      const nextWord = res.data.next_guess.toUpperCase();
  
      // Évaluer le mot actuel
      const resultRow = evaluateGuess(currentGuess.toUpperCase(), targetWord || nextWord);
  
      setGuesses((prev) => [...prev, currentGuess.toUpperCase()]);
      setResults((prev) => [...prev, resultRow]);
      updateLetterStates(resultRow);
      setCurrentGuess("");
      setAiSuggestion(nextWord);
      setIsRevealing(false);
  
      if (currentGuess.toUpperCase() === (targetWord || nextWord)) {
        setIsWon(true);
        setIsGameOver(true);
      } else if (guesses.length + 1 >= 6) {
        setIsGameOver(true);
      }
    } catch (error) {
      console.error(error);
      const errorMsg = error.response?.data?.detail || "Erreur serveur";
      toast.error(errorMsg);
      setIsRevealing(false);
    }
  }, [currentGuess, results, guesses, updateLetterStates, language, targetWord]);

  // Gestion du clavier
  const handleKeyPress = useCallback(
    (key) => {
      if (isGameOver || isRevealing) return;
      if (key === "ENTER") submitGuess();
      else if (key === "⌫") setCurrentGuess((prev) => prev.slice(0, -1));
      else if (currentGuess.length < 5 && /^[A-Z]$/i.test(key)) setCurrentGuess((prev) => prev + key.toUpperCase());
    },
    [currentGuess, isGameOver, isRevealing, submitGuess]
  );

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === "Enter") handleKeyPress("ENTER");
      else if (e.key === "Backspace") handleKeyPress("⌫");
      else if (/^[a-zA-Z]$/.test(e.key)) handleKeyPress(e.key.toUpperCase());
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyPress]);

  // Démarrer une nouvelle partie
  const handleNewGame = useCallback(() => {
    setTargetWord("");
    setGuesses([]);
    setResults([]);
    setCurrentGuess("");
    setLetterStates(new Map());
    setIsGameOver(false);
    setIsWon(false);
    setAiSuggestion(undefined);
  }, []);

// Obtenir une suggestion IA depuis le backend
const handleRequestAI = useCallback(async () => {
  setIsLoadingAI(true);
  try {
    // Préparer le feedback selon le schéma backend
    const feedback = {
      green: {},      // {position: lettre}
      yellow: {},     // {position: [lettres]}
      grey: []        // [lettres]
    };
    
    // Analyser les résultats pour construire le feedback
    results.forEach((row) => {
      row.forEach((cell, idx) => {
        const letter = cell.letter.toLowerCase();
        
        if (cell.state === "correct") {
          // Lettre à la bonne position
          feedback.green[idx] = letter;
        } else if (cell.state === "present") {
          // Lettre présente mais mauvaise position
          if (!feedback.yellow[idx]) {
            feedback.yellow[idx] = [];
          }
          if (!feedback.yellow[idx].includes(letter)) {
            feedback.yellow[idx].push(letter);
          }
        } else if (cell.state === "absent") {
          // Lettre absente
          if (!feedback.grey.includes(letter)) {
            feedback.grey.push(letter);
          }
        }
      });
    });
    
    console.log("📤 Feedback envoyé:", feedback);
    
    const res = await axios.post("/wordle/suggest-ai", {
      feedback: feedback,
      language: language,
    });
    
    console.log("📥 Réponse reçue:", res.data);
    
    setAiSuggestion(res.data.suggested_word.toUpperCase());
    
    const successMsg = language === "fr"
      ? `Suggestion IA: ${res.data.suggested_word.toUpperCase()}`
      : `AI Suggestion: ${res.data.suggested_word.toUpperCase()}`;
    
    toast.success(successMsg, {
      description: res.data.explanation,
      duration: 5000,
    });
    
  } catch (error) {
    console.error("❌ Erreur:", error);
    const errorMsg = error.response?.data?.detail || 
                     (language === "fr" ? "Erreur serveur" : "Server error");
    toast.error(errorMsg);
  } finally {
    setIsLoadingAI(false);
  }
}, [results, language]);

  // Switch langue
  const handleLanguageSwitch = useCallback(() => {
    setLanguage((prev) => (prev === "fr" ? "en" : "fr"));
    handleNewGame();
  }, [handleNewGame]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/20">
              <Gamepad2 className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Wordle CSP</h1>
              <p className="text-xs text-muted-foreground">
                {language === "fr" ? "Solveur par contraintes + LLM" : "CSP Solver + LLM"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleLanguageSwitch}
              className="flex items-center gap-2"
            >
              <Globe className="w-4 h-4" />
              <span className="font-medium">{language === "fr" ? "FR" : "EN"}</span>
            </Button>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 border border-accent/30">
              <Brain className="w-4 h-4 text-accent" />
              <span className="text-xs text-accent font-medium">{language === "fr" ? "IA Activée" : "AI Enabled"}</span>
            </div>
              {/* Toggle Dark Mode */}
              <DarkModeToggle />
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6 justify-center items-start">
          <div className="flex flex-col items-center">
          <div className="mb-4 text-center">
            <h1 className="text-3xl font-bold text-wordle">Wordle <span className="text-foreground">Solver</span></h1>
            <p className="text-sm text-muted-foreground">Devinez moins, gagnez plus : laissez le solveur CSP et l’IA faire le reste !</p>
          </div>
            <GameBoard
              guesses={guesses}
              results={results}
              currentGuess={currentGuess}
              currentRow={currentRow}
              isRevealing={isRevealing}
            />
            <Keyboard
              letterStates={letterStates}
              onKeyPress={handleKeyPress}
              disabled={isGameOver || isRevealing}
            />
          </div>
          <div className="w-full lg:w-80">
            <SolverPanel
              solver={{ getRemainingCount: () => 0, getTopSuggestions: () => [], getEntropy: () => 0, getBestGuess: () => null, getPossibleWords: () => [] }}
              isLoading={isLoadingAI}
              aiSuggestion={aiSuggestion}
              onRequestAI={handleRequestAI}
            />
          </div>
        </div>
      </main>

      {/* Game Over Modal */}
      <GameStats
        isGameOver={isGameOver}
        isWon={isWon}
        targetWord={targetWord || aiSuggestion}
        attempts={guesses.length}
        onNewGame={handleNewGame}
      />
    </div>
  );
}
export default WordleGame;
