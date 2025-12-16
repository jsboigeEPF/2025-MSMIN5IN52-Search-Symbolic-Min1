import React from "react";
import { Brain, Lightbulb, Target, Zap, Sparkles, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

export function SolverPanel({ 
  solverData, 
  isLoading = false, 
  aiSuggestion, 
  onRequestAI, 
  onRequestCSP,
  onRequestHybrid,
  language = "fr",
  solverMode = "hybrid"
}) {
  const remainingCount = solverData?.remainingCount ?? 0;
  const topSuggestions = solverData?.topSuggestions ?? [];
  const entropy = solverData?.entropy ?? 0;
  const bestGuess = solverData?.bestGuess ?? null;
  const possibleWords = (solverData?.possibleWords ?? []).filter(Boolean);


  const texts = {
    fr: {
      title: "Solveur CSP / Hybrid / IA",
      subtitle: "Résolution par contraintes + LLM",
      possibleWords: "Mots possibles",
      entropy: "Entropie",
      bestGuess: "Meilleure suggestion CSP",
      aiSuggestion: "Suggestion IA",
      cspSuggestion: "Suggestion CSP",
      hybridSuggestion: "Suggestion Hybride",
      loading: "Analyse en cours...",
      loadingLLM: "Analyse LLM en cours...",
      loadingCSP: "Calcul CSP en cours...",
      clickForSuggestion: "Cliquer pour obtenir une suggestion CSP + IA",
      clickForAISuggestion: "Cliquer pour obtenir une suggestion IA",
      clickForCSPSuggestion: "Cliquer pour obtenir une suggestion CSP",
      topSuggestions: "Top suggestions",
      remaining: "Mots restants :",
      countwords: "Nombre de mots possibles :"
    },
    en: {
      title: "CSP / Hybrid / AI Solver",
      subtitle: "Constraint satisfaction + LLM solving",
      possibleWords: "Possible words",
      entropy: "Entropy",
      bestGuess: "Best CSP suggestion",
      aiSuggestion: "AI Suggestion",
      cspSuggestion: "CSP Suggestion",
      hybridSuggestion: "Hybrid Suggestion",
      loading: "Analysis in progress...",
      loadingLLM: "LLM analysis in progress...",
      loadingCSP: "CSP calculation in progress...",
      clickForSuggestion: "Click to get a suggestion CSP + AI",
      clickForAISuggestion: "Click to get an AI suggestion",
      clickForCSPSuggestion: "Click to get a CSP suggestion",
      topSuggestions: "Top suggestions",
      remaining: "Remaining words : ",
      countwords: "Number of possible words :"
    }
  };

  const t = texts[language] || texts.fr;

  const getSuggestionConfig = () => {
    switch (solverMode) {
      case "csp":
        return {
          title: t.cspSuggestion,
          icon: <Cpu className="w-4 h-4 text-primary" />,
          loadingText: t.loadingCSP,
          clickText: t.clickForCSPSuggestion,
          gradientClass: "from-primary/10 to-primary/5 border-primary/30 hover:from-primary/20 hover:to-primary/10 hover:border-primary/50 hover:shadow-primary/30",
          iconColor: "text-black text-x3"
        };
      case "hybrid":
        return {
          title: t.hybridSuggestion,
          icon: <Sparkles className="w-4 h-5 text-accent" />,
          loadingText: t.loading,
          clickText: t.clickForSuggestion,
          gradientClass: "from-accent/10 to-accent/5 border-accent/30 hover:from-accent/20 hover:to-accent/10 hover:border-accent/50 hover:shadow-accent/20",
          iconColor: "text-black text-x3"
        };
      case "ai":
        return {
          title: t.aiSuggestion,
          icon: <Brain className="w-4 h-4 text-purple-500" />,
          loadingText: t.loadingLLM,
          clickText: t.clickForAISuggestion,
          gradientClass: "from-purple-500/10 to-purple-500/5 border-purple-500/30 hover:from-purple-500/20 hover:to-purple-500/10 hover:border-purple-500/50 hover:shadow-purple-500/30",
          iconColor: "text-black text-x3"
        };
      default:
        return {
          title: t.aiSuggestion,
          icon: <Sparkles className="w-4 h-4 text-accent" />,
          loadingText: t.loading,
          clickText: t.clickForSuggestion,
          gradientClass: "from-accent/10 to-accent/5 border-accent/30 hover:from-accent/20 hover:to-accent/10 hover:border-accent/50 hover:shadow-accent/20",
          iconColor: "text-black text-x3"
        };
    }
  };

  const config = getSuggestionConfig();

  return (
    <div className="flex flex-col gap-4 p-4 bg-card rounded-xl border border-border shadow-lg">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="p-2 rounded-lg bg-solver-bg glow-accent">
          <Brain className="w-8 h-8 text-accent" />
        </div>
        <div>
          <h3 className="font-semibold text-foreground">{t.title}</h3>
          <p className="text-xs text-muted-foreground">{t.subtitle}</p>
        </div>
      </div>

      {/* Nombre de mots restants */}
      {remainingCount > 0 && (
      <div className="p-3 rounded-lg bg-secondary/50">
        <div className="flex items-center gap-2 text-black/60 dark:text-muted-foreground text-xs mb-1 ">
          <Target className="w-3 h-3 " />
          {t.countwords}
        </div>
        <div className="text-2xl font-bold text-foreground font-mono text-center">
          {remainingCount}
        </div>
        </div>
      )}
      {/* Best Guess */}
      {bestGuess && (
        <div className="p-3 rounded-lg bg-primary/10 border border-primary/30">
          <div className="flex items-center gap-2 text-primary text-xs mb-2">
            <Lightbulb className="w-3 h-3" />
            {t.bestGuess}
          </div>
          <div className="text-xl font-bold text-primary font-mono tracking-widest">
            {bestGuess}
          </div>
        </div>
      )}

      {/* Suggestion Button */}
      <button
        onClick={() =>
          solverMode === "csp"
            ? onRequestCSP()
            : solverMode === "hybrid"
            ? onRequestHybrid()
            : onRequestAI()
        }
        disabled={isLoading}
        className={cn(
          "p-4 rounded-lg border transition-all",
          `bg-gradient-to-br ${config.gradientClass}`,
          "hover:shadow-lg",
          isLoading && "animate-pulse cursor-not-allowed",
          !isLoading && "active:scale-[0.98]"
        )}
      >
        <div className="flex items-center gap-2 mb-2">
          {isLoading ? (
            <>
              <div
                className={cn(
                  "w-4 h-4 border-2 border-t-transparent rounded-full animate-spin",
                  solverMode === "csp" ? "border-primary" : "border-accent"
                )}
              />
              <span className={cn("text-xs font-medium", config.iconColor)}>
                {config.loadingText}
              </span>
            </>
          ) : (
            <>
              {config.icon}
              <span className={cn("text-xs font-medium", config.iconColor)}>
                {config.title}
              </span>
            </>
          )}
        </div>
        {aiSuggestion ? (
          <div
            className={cn(
              "text-2xl font-bold font-mono tracking-widest",
              config.iconColor
            )}
          >
            {aiSuggestion}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">
            {config.clickText}
          </div>
        )}
      </button>

      {/* Top Suggestions */}
      {topSuggestions.length > 0 && (
        <div>
          <h4 className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
            <Target className="w-3 h-3" />
            {t.topSuggestions}
          </h4>
          <div className="flex flex-wrap gap-2">
            {topSuggestions.map(({ word, score }) => (
              <div
                key={word}
                className="px-2 py-1 rounded bg-secondary text-foreground text-sm font-mono border border-border/50 hover:bg-secondary/80 transition-colors"
                title={`Score: ${score.toFixed(0)}`}
              >
                {word}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Remaining Words */}
      {possibleWords.length > 0 && (
        <div>
          <h4 className="text-xs text-black/60 dark:text-muted-foreground mb-2 flex items-center gap-1">
          <Target className="w-3 h-3" />
          {t.remaining}
          </h4>
          <div className="flex flex-wrap gap-1 max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
            {possibleWords.map((word) => (
              <span
                key={word}
                className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-xs font-mono border border-border/30"
              >
                {word}
              </span>
            ))}
          </div>
        </div>
      )}
      {/* Mode indicator */}
      <div className="text-xs text-muted-foreground text-center pt-2 border-t border-border/50">
        Mode actif:{" "}
        <span className="font-semibold">{solverMode.toUpperCase()}</span>
      </div>
    </div>
  );
}
