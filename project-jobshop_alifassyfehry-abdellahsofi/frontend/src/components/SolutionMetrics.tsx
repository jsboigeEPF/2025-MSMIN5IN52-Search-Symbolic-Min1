import { useStore } from '../store/useStore';
import { Clock, TrendingUp, GitBranch, Zap, CheckCircle2, XCircle } from 'lucide-react';
import { formatDuration, formatNumber } from '../lib/utils';

export default function SolutionMetrics() {
  const { solution } = useStore();

  if (!solution) return null;

  const isSuccess = solution.status === 'OPTIMAL' || solution.status === 'FEASIBLE';

  return (
    <div className="space-y-4">
      {/* Status Banner */}
      <div
        className={`card ${
          isSuccess
            ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-400/30'
            : 'bg-gradient-to-r from-red-500/20 to-rose-500/20 border-red-400/30'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl shadow-lg ${isSuccess ? 'bg-green-500' : 'bg-red-500'}`}>
            {isSuccess ? (
              <CheckCircle2 className="w-6 h-6 text-white" />
            ) : (
              <XCircle className="w-6 h-6 text-white" />
            )}
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              Solution Status: {solution.status}
            </h3>
            <p className="text-sm text-white/70 font-medium">
              {isSuccess
                ? 'Successfully found a solution'
                : 'No solution found or solver error'}
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      {solution.makespan !== null && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Makespan */}
          <div className="metric-card hover:shadow-xl hover:shadow-green-500/20 transition-all duration-300">
            <div className="flex items-center gap-2 mb-2">
              <div className="bg-green-500 p-1.5 rounded-lg shadow-lg">
                <Clock className="w-4 h-4 text-white" />
              </div>
              <h4 className="text-sm font-semibold text-white/80">Makespan</h4>
            </div>
            <p className="text-3xl font-bold text-white">{solution.makespan}</p>
            <p className="text-xs text-white/60 mt-1">time units</p>
          </div>

          {/* Solve Time */}
          <div className="metric-card hover:shadow-xl hover:shadow-amber-500/20 transition-all duration-300">
            <div className="flex items-center gap-2 mb-2">
              <div className="bg-amber-500 p-1.5 rounded-lg shadow-lg">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <h4 className="text-sm font-semibold text-white/80">Solve Time</h4>
            </div>
            <p className="text-3xl font-bold text-white">
              {formatDuration(solution.solver_statistics.wall_time)}
            </p>
            <p className="text-xs text-white/60 mt-1">wall time</p>
          </div>

          {/* Conflicts */}
          {solution.solver_statistics.conflicts !== undefined && (
            <div className="metric-card hover:shadow-xl hover:shadow-rose-500/20 transition-all duration-300">
              <div className="flex items-center gap-2 mb-2">
                <div className="bg-rose-500 p-1.5 rounded-lg shadow-lg">
                  <TrendingUp className="w-4 h-4 text-white" />
                </div>
                <h4 className="text-sm font-semibold text-white/80">Conflicts</h4>
              </div>
              <p className="text-3xl font-bold text-white">
                {formatNumber(solution.solver_statistics.conflicts)}
              </p>
              <p className="text-xs text-white/60 mt-1">search conflicts</p>
            </div>
          )}

          {/* Branches */}
          {solution.solver_statistics.branches !== undefined && (
            <div className="metric-card hover:shadow-xl hover:shadow-purple-500/20 transition-all duration-300">
              <div className="flex items-center gap-2 mb-2">
                <div className="bg-purple-500 p-1.5 rounded-lg shadow-lg">
                  <GitBranch className="w-4 h-4 text-white" />
                </div>
                <h4 className="text-sm font-semibold text-white/80">Branches</h4>
              </div>
              <p className="text-3xl font-bold text-white">
                {formatNumber(solution.solver_statistics.branches)}
              </p>
              <p className="text-xs text-white/60 mt-1">search branches</p>
            </div>
          )}
        </div>
      )}

      {/* Operations Count */}
      <div className="card bg-gradient-to-br from-orange-500/20 to-yellow-500/20 border-orange-400/30 hover:shadow-xl hover:shadow-orange-500/30 transition-all duration-300">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-white/80">Scheduled Operations</h4>
            <p className="text-4xl font-bold text-white mt-1">
              {solution.operations.length}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-white/70 font-medium">Best Bound</p>
            <p className="text-2xl font-bold text-white">
              {solution.solver_statistics.best_bound?.toFixed(2) || 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
