import React, { useEffect, useState } from "react";
import clsx from "clsx";

export function GameTile({ letter, state, isRevealing, delay, isCurrentRow }) {
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    if (isRevealing) {
      const timeout = setTimeout(() => setFlipped(true), delay * 250);
      return () => clearTimeout(timeout);
    } else {
      setFlipped(false);
    }
  }, [isRevealing, delay]);

  // Couleurs basées sur tes variables CSS
  const bgClass = clsx({
    "bg-[hsl(var(--background))] border-[hsl(var(--border))]": state === "empty",
    "bg-[hsl(var(--wordle-correct))] text-[hsl(var(--card-foreground))] border-[hsl(var(--wordle-correct))]": state === "correct",
    "bg-[hsl(var(--wordle-present))] text-[hsl(var(--card-foreground))] border-[hsl(var(--wordle-present))]": state === "present",
    "bg-[hsl(var(--muted))] text-[hsl(var(--card-foreground))] border-[hsl(var(--muted))]": state === "absent",
  });

  // Glow optionnel
  const glowClass = clsx({
    "glow-correct": state === "correct",
    "glow-present": state === "present",
  });

  return (
    <div
      className={clsx(
        "w-14 h-14 sm:w-16 sm:h-16 border-2 flex items-center justify-center text-2xl font-bold uppercase select-none transition-colors duration-300",
        "rounded-xl", 
        bgClass,
        glowClass,
        flipped && "animate-pop"
      )}
    >
      {letter}
    </div>
  );
}
