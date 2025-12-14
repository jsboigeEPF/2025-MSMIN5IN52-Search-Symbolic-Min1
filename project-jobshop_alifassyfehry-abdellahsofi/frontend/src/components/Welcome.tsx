import { ArrowRight, BarChart3, CheckCircle2, SlidersHorizontal } from 'lucide-react';

export default function Welcome() {
  const steps = [
    {
      icon: CheckCircle2,
      title: 'Selectionner un scenario de production',
      description: 'Choisissez un scenario predefini dans le panneau gauche.',
      color: 'text-red-400',
    },
    {
      icon: SlidersHorizontal,
      title: 'Configurer le solveur',
      description: 'Ajustez le temps maximal et le nombre de threads CP-SAT.',
      color: 'text-orange-400',
    },
    {
      icon: ArrowRight,
      title: 'Lancer la resolution',
      description: 'Cliquez sur \"Lancer le scenario\" pour demarrer le solveur.',
      color: 'text-yellow-400',
    },
    {
      icon: BarChart3,
      title: 'Analyze Results',
      description: 'View the solution metrics and interactive Gantt chart.',
      color: 'text-green-400',
    },
  ];

  return (
    <div className="flex-1 flex items-center justify-center h-full">
      <div className="text-center glass-panel p-12 max-w-3xl w-full animate-scale-in">
        <h2 className="text-4xl font-bold gradient-text mb-4">
          Welcome to the Job-Shop Scheduler
        </h2>
        <p className="text-lg text-white/70 mb-12 max-w-2xl mx-auto">
          An advanced constraint programming tool using Google OR-Tools to solve complex scheduling problems.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <div 
              key={step.title} 
              className="flex flex-col items-center"
              style={{ animation: `slideUp 0.5s ease-out ${index * 0.15}s forwards`, opacity: 0 }}
            >
              <div className={`p-4 bg-white/10 rounded-full border-2 border-white/20 mb-4 ${step.color}`}>
                <step.icon className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-white mb-2">{step.title}</h3>
              <p className="text-sm text-white/60">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
