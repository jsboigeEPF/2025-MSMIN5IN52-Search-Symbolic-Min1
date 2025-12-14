import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Clock, Activity } from 'lucide-react';
import { apiService } from '../services/api';
import type { BottleneckAnalysis } from '../types';

interface BottleneckAnalyzerProps {
  instanceName: string;
}

export const BottleneckAnalyzer: React.FC<BottleneckAnalyzerProps> = ({ instanceName }) => {
  const [analysis, setAnalysis] = useState<BottleneckAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (instanceName) {
      loadAnalysis();
    }
  }, [instanceName]);

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const data = await apiService.analyzeBottlenecks(instanceName);
      setAnalysis(data);
    } catch (error) {
      console.error('Error loading bottleneck analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-panel p-6 animate-pulse">
        <div className="h-8 bg-white/10 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-white/5 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  const getUtilizationColor = (percent: number) => {
    if (percent >= 90) return 'text-red-400';
    if (percent >= 75) return 'text-orange-400';
    if (percent >= 50) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getUtilizationBg = (percent: number) => {
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 75) return 'bg-orange-500';
    if (percent >= 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="glass-panel p-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <Activity className="text-red-400" size={28} />
        <h2 className="text-2xl font-bold">Bottleneck Analysis</h2>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="metric-card">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="text-blue-400" size={20} />
            <span className="text-sm text-white/70">Makespan</span>
          </div>
          <p className="text-3xl font-bold">{analysis.makespan}</p>
          <p className="text-xs text-white/50 mt-1">time units</p>
        </div>

        <div className="metric-card">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="text-orange-400" size={20} />
            <span className="text-sm text-white/70">Bottlenecks</span>
          </div>
          <p className="text-3xl font-bold text-orange-400">
            {analysis.bottlenecks.filter(b => b.is_bottleneck).length}
          </p>
          <p className="text-xs text-white/50 mt-1">machines over 80%</p>
        </div>

        <div className="metric-card">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="text-green-400" size={20} />
            <span className="text-sm text-white/70">Avg Utilization</span>
          </div>
          <p className="text-3xl font-bold">
            {(analysis.bottlenecks.reduce((sum, b) => sum + b.utilization_percent, 0) / analysis.bottlenecks.length).toFixed(1)}%
          </p>
          <p className="text-xs text-white/50 mt-1">across all machines</p>
        </div>
      </div>

      {/* Machine Utilization */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">Machine Utilization</h3>
        <div className="space-y-3">
          {analysis.bottlenecks.map((bottleneck, index) => (
            <div
              key={index}
              className={`bg-white/5 p-4 rounded-xl border ${
                bottleneck.is_bottleneck ? 'border-red-500/50' : 'border-white/10'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="font-semibold">{bottleneck.machine}</span>
                  {bottleneck.is_bottleneck && (
                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded-full flex items-center gap-1">
                      <AlertTriangle size={12} />
                      Bottleneck
                    </span>
                  )}
                </div>
                <span className={`text-lg font-bold ${getUtilizationColor(bottleneck.utilization_percent)}`}>
                  {bottleneck.utilization_percent.toFixed(1)}%
                </span>
              </div>

              <div className="mb-2">
                <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getUtilizationBg(bottleneck.utilization_percent)} transition-all duration-500`}
                    style={{ width: `${bottleneck.utilization_percent}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm text-white/60">
                <span>Busy: {bottleneck.busy_time} units</span>
                <span>Idle: {(analysis.makespan || 0) - bottleneck.busy_time} units</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {analysis.recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-xl p-4">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="text-orange-400" size={20} />
            Optimization Recommendations
          </h3>
          <ul className="space-y-2">
            {analysis.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-orange-400 font-bold">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
