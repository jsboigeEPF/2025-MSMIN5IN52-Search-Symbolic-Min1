import React, { useMemo, useState } from 'react';
import { GitCompare, Play, BarChart3, TrendingUp } from 'lucide-react';
import { apiService } from '../services/api';
import type { InstanceComparison, SolutionResponse } from '../types';
import { useStore } from '../store/useStore';

export const WhatIfAnalysis: React.FC = () => {
  const { instances } = useStore();
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
  const [comparisons, setComparisons] = useState<InstanceComparison[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeLimit, setTimeLimit] = useState<number>(8);
  const [numWorkers, setNumWorkers] = useState<number>(8);

  const labels = useMemo(
    () => ({
      scenario_normal: 'Scenario normal (flux nominal + commande flash)',
      scenario_maintenance: 'Scenario normal + maintenance',
      scenario_rush_150: 'Scenario rush 150 commandes',
      scenario_rush_300: 'Scenario rush 300 commandes',
      scenario_rush_450: 'Scenario rush 450 commandes',
    }),
    []
  );

  const toggleScenario = (scenario: string) => {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario]
    );
  };

  const runComparison = async () => {
    if (selectedScenarios.length < 2) {
      alert('Selectionnez au moins 2 scenarios a comparer');
      return;
    }
    setLoading(true);
    try {
      const results: InstanceComparison[] = [];
      for (const name of selectedScenarios) {
        const solution: SolutionResponse = await apiService.solveInstance({
          instance_name: name,
          time_limit: timeLimit > 0 ? timeLimit : undefined,
          num_workers: numWorkers,
        });
        const jobs = new Set(solution.operations.map((op) => op.job_id));
        const machines = new Set(solution.operations.map((op) => op.machine));
        results.push({
          name,
          status: solution.status,
          makespan: solution.makespan,
          num_jobs: jobs.size,
          num_machines: machines.size,
          wall_time: solution.solver_statistics.wall_time || 0,
        });
      }
      setComparisons(results);
    } catch (error) {
      console.error('Error running comparison:', error);
      alert('Failed to run comparison');
    } finally {
      setLoading(false);
    }
  };

  const getBestMakespan = () => {
    if (comparisons.length === 0) return null;
    return Math.min(...comparisons.map(c => c.makespan || Infinity));
  };

  const getWorstMakespan = () => {
    if (comparisons.length === 0) return null;
    return Math.max(...comparisons.filter(c => c.makespan).map(c => c.makespan || 0));
  };

  return (
    <div className="glass-panel p-8 max-w-6xl mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <GitCompare className="text-purple-400" size={32} />
        <h2 className="text-3xl font-bold gradient-text">Analyse What-If</h2>
      </div>

      <p className="text-white/70 mb-6">
        Comparez plusieurs scenarios de production avec des parametres de solveur pour analyser l'impact du temps max et des threads CP-SAT.
      </p>

      {/* Scenario Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Selectionner des scenarios de production a comparer</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {instances.map((inst) => (
            <button
              key={inst.name}
              onClick={() => toggleScenario(inst.name)}
              className={`p-4 rounded-xl border-2 transition-all duration-300 text-left ${
                selectedScenarios.includes(inst.name)
                  ? 'border-purple-500 bg-purple-500/20'
                  : 'border-white/20 bg-white/5 hover:bg-white/10'
              }`}
            >
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedScenarios.includes(inst.name)}
                  onChange={() => toggleScenario(inst.name)}
                  className="w-4 h-4"
                />
                <span className="font-medium">{labels[inst.name as keyof typeof labels] || inst.name}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Solver parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-semibold text-white mb-2">
            Temps maximal du solveur (secondes)
          </label>
          <input
            type="number"
            min={0}
            max={120}
            step={0.5}
            value={timeLimit}
            onChange={(e) => setTimeLimit(parseFloat(e.target.value))}
            className="input-field"
          />
          <p className="text-xs text-white/60 mt-1">0 = illimite. S'applique a tous les scenarios compares.</p>
        </div>
        <div>
          <label className="block text-sm font-semibold text-white mb-2">
            Threads CP-SAT (workers)
          </label>
          <input
            type="number"
            min={1}
            max={16}
            value={numWorkers}
            onChange={(e) => setNumWorkers(parseInt(e.target.value))}
            className="input-field"
          />
          <p className="text-xs text-white/60 mt-1">Min 1, max 16. Threads de recherche CP-SAT (puissance de calcul).</p>
        </div>
      </div>

      {/* Run Comparison Button */}
      <button
        onClick={runComparison}
        disabled={loading || selectedScenarios.length < 2}
        className="btn-primary w-full flex items-center justify-center gap-2 py-4 mb-8 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            <span>Comparaison en cours...</span>
          </>
        ) : (
          <>
            <Play size={24} />
              <span>Comparer les scenarios selectionnes ({selectedScenarios.length})</span>
          </>
        )}
      </button>

      {/* Comparison Results */}
      {comparisons.length > 0 && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="metric-card">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="text-green-400" size={20} />
                <span className="text-sm text-white/70">Best Makespan</span>
              </div>
              <p className="text-3xl font-bold text-green-400">{getBestMakespan()}</p>
              <p className="text-xs text-white/50 mt-1">time units</p>
            </div>

            <div className="metric-card">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="text-red-400 rotate-180" size={20} />
                <span className="text-sm text-white/70">Worst Makespan</span>
              </div>
              <p className="text-3xl font-bold text-red-400">{getWorstMakespan()}</p>
              <p className="text-xs text-white/50 mt-1">time units</p>
            </div>

            <div className="metric-card">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="text-blue-400" size={20} />
                <span className="text-sm text-white/70">Improvement</span>
              </div>
              <p className="text-3xl font-bold text-blue-400">
                {getWorstMakespan() && getBestMakespan()
                  ? (((getWorstMakespan()! - getBestMakespan()!) / getWorstMakespan()!) * 100).toFixed(1)
                  : 0}%
              </p>
              <p className="text-xs text-white/50 mt-1">best vs worst</p>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <table className="w-full">
              <thead className="bg-white/10">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Scenario</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Status</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Makespan</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Jobs</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Machines</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Solve Time</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold">Performance</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((comp, index) => {
                  const isBest = comp.makespan === getBestMakespan();
                  const isWorst = comp.makespan === getWorstMakespan();
                  
                  return (
                    <tr
                      key={index}
                      className={`border-t border-white/10 hover:bg-white/5 transition-colors ${
                        isBest ? 'bg-green-500/10' : isWorst ? 'bg-red-500/10' : ''
                      }`}
                    >
                      <td className="px-6 py-4 font-medium">{comp.name}</td>
                      <td className="px-6 py-4 text-center">
                        <span className={`px-3 py-1 rounded-full text-xs ${
                          comp.status === 'OPTIMAL' ? 'bg-green-500/20 text-green-400' :
                          comp.status === 'FEASIBLE' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {comp.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`text-lg font-bold ${
                          isBest ? 'text-green-400' : isWorst ? 'text-red-400' : ''
                        }`}>
                          {comp.makespan || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center text-white/70">{comp.num_jobs}</td>
                      <td className="px-6 py-4 text-center text-white/70">{comp.num_machines}</td>
                      <td className="px-6 py-4 text-center text-white/70">
                        {comp.wall_time.toFixed(2)}s
                      </td>
                      <td className="px-6 py-4 text-center">
                        {isBest && (
                          <span className="text-green-400 font-semibold">⭐ Best</span>
                        )}
                        {isWorst && !isBest && (
                          <span className="text-red-400">Worst</span>
                        )}
                        {!isBest && !isWorst && comp.makespan && getBestMakespan() && (
                          <span className="text-white/50">
                            +{((comp.makespan - getBestMakespan()!) / getBestMakespan()! * 100).toFixed(1)}%
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Visual Comparison Chart */}
          <div className="bg-white/5 rounded-xl border border-white/10 p-6">
            <h3 className="text-lg font-semibold mb-4">Makespan Comparison</h3>
            <div className="space-y-3">
              {comparisons.filter(c => c.makespan).map((comp, index) => {
                const maxMakespan = Math.max(...comparisons.filter(c => c.makespan).map(c => c.makespan || 0));
                const widthPercent = comp.makespan ? (comp.makespan / maxMakespan) * 100 : 0;
                
                return (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{comp.name}</span>
                      <span className="text-sm text-white/70">{comp.makespan}</span>
                    </div>
                    <div className="h-8 bg-white/10 rounded-lg overflow-hidden">
                      <div
                        className={`h-full flex items-center justify-end px-3 text-sm font-semibold transition-all duration-700 ${
                          comp.makespan === getBestMakespan()
                            ? 'bg-green-500'
                            : comp.makespan === getWorstMakespan()
                            ? 'bg-red-500'
                            : 'bg-blue-500'
                        }`}
                        style={{ width: `${widthPercent}%` }}
                      >
                        {comp.makespan === getBestMakespan() && '⭐'}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
