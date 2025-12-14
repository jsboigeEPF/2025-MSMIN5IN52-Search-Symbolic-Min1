import { useStore } from '../store/useStore';
import { Activity, Zap, Target, TrendingUp } from 'lucide-react';

export default function StatsOverview() {
  const { instances, solution, solving } = useStore();

  const stats = [
    {
      icon: Activity,
      label: 'Scenarios disponibles',
      value: instances.length,
      color: 'from-blue-500 to-cyan-500',
      glow: 'shadow-blue-500/50',
    },
    {
      icon: Target,
      label: 'Optimization Status',
      value: solving ? 'Running' : solution ? 'Complete' : 'Ready',
      color: 'from-green-500 to-emerald-500',
      glow: 'shadow-green-500/50',
    },
    {
      icon: Zap,
      label: 'Solver Engine',
      value: 'CP-SAT',
      color: 'from-amber-500 to-orange-500',
      glow: 'shadow-amber-500/50',
    },
    {
      icon: TrendingUp,
      label: 'Performance',
      value: solution ? 'Optimal' : 'Pending',
      color: 'from-purple-500 to-pink-500',
      glow: 'shadow-purple-500/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 animate-slide-up">
      {stats.map((stat, index) => (
        <div
          key={stat.label}
          className="card-hover"
          style={{ animationDelay: `${index * 0.1}s` }}
        >
          <div className="flex items-center gap-3">
            <div className={`bg-gradient-to-br ${stat.color} p-3 rounded-xl shadow-lg ${stat.glow}`}>
              <stat.icon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-white/60 font-semibold uppercase tracking-wide">
                {stat.label}
              </p>
              <p className="text-2xl font-bold text-white mt-0.5">{stat.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
