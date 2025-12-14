import { useEffect, useState } from 'react';
import { Loader2, Sparkles } from 'lucide-react';

interface SolverProgressProps {
  isActive: boolean;
}

export default function SolverProgress({ isActive }: SolverProgressProps) {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('Initializing');

  useEffect(() => {
    if (!isActive) {
      setProgress(0);
      setStage('Initializing');
      return;
    }

    const stages = [
      { name: 'Initializing solver...', duration: 500 },
      { name: 'Building constraints...', duration: 800 },
      { name: 'Searching for solutions...', duration: 1000 },
      { name: 'Optimizing schedule...', duration: 2000 },
    ];

    let currentStage = 0;
    let currentProgress = 0;

    const updateProgress = () => {
      if (currentStage >= stages.length) {
        setProgress(95);
        setStage('Finalizing solution...');
        return;
      }

      const stage = stages[currentStage];
      setStage(stage.name);

      const increment = (100 / stages.length) / (stage.duration / 100);
      const interval = setInterval(() => {
        currentProgress += increment;
        if (currentProgress >= (currentStage + 1) * (100 / stages.length)) {
          clearInterval(interval);
          currentStage++;
          if (currentStage < stages.length) {
            updateProgress();
          } else {
            setProgress(95);
            setStage('Finalizing solution...');
          }
        } else {
          setProgress(Math.min(currentProgress, 95));
        }
      }, 100);
    };

    updateProgress();
  }, [isActive]);

  if (!isActive) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in">
      <div className="glass-panel max-w-md w-full mx-4 p-8 animate-scale-in">
        <div className="flex items-center justify-center mb-6">
          <div className="relative">
            <Loader2 className="w-16 h-16 text-red-400 animate-spin" />
            <Sparkles className="w-8 h-8 text-amber-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
          </div>
        </div>

        <h3 className="text-2xl font-bold text-white text-center mb-2">
          Solving in Progress
        </h3>
        <p className="text-white/70 text-center mb-6 font-medium">{stage}</p>

        <div className="relative h-3 bg-white/10 rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-red-500 via-orange-500 to-amber-500 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute inset-0 bg-white/20 animate-pulse" />
          </div>
        </div>

        <div className="flex justify-between mt-2 text-sm">
          <span className="text-white/60 font-semibold">Progress</span>
          <span className="text-white font-bold">{Math.round(progress)}%</span>
        </div>

        <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
          <p className="text-xs text-white/60 text-center font-medium">
            Using Google OR-Tools CP-SAT constraint programming solver
          </p>
        </div>
      </div>
    </div>
  );
}
