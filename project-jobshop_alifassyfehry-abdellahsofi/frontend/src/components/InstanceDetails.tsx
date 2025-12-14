import { useStore } from '../store/useStore';
import { Info } from 'lucide-react';

export default function InstanceDetails() {
  const { instanceDetails } = useStore();

  if (!instanceDetails) return null;

  return (
    <div className="card-hover">
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-gradient-to-br from-cyan-500 to-blue-500 p-2 rounded-xl shadow-lg">
          <Info className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-xl font-bold text-white">Details du scenario de production</h2>
      </div>

      <p className="text-white/80 mb-4 font-medium">{instanceDetails.description}</p>

      {/* Machines */}
      <div className="mb-4">
        <h3 className="text-sm font-bold text-white mb-3">Ressources / Machines</h3>
        <div className="flex flex-wrap gap-2">
          {instanceDetails.machines.map((machine) => (
            <span
              key={machine}
              className="px-4 py-2 bg-gradient-to-r from-red-500/20 to-orange-500/20 text-white border border-red-400/30 rounded-full text-sm font-semibold shadow-lg hover:scale-105 transition-transform duration-200"
            >
              {machine}
            </span>
          ))}
        </div>
      </div>

      {/* Jobs */}
      <div className="mb-4">
        <h3 className="text-sm font-bold text-white mb-3">
          Commandes ({instanceDetails.jobs.length})
        </h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {instanceDetails.jobs.map((job) => (
            <div key={job.job_id} className="p-3 bg-white/5 backdrop-blur-sm rounded-xl border border-white/10">
              <h4 className="font-bold text-white mb-2">{job.job_id}</h4>
              <div className="space-y-1">
                {job.operations.map((op) => (
                  <div
                    key={op.op_id}
                    className="text-xs text-white/70 flex items-center gap-2"
                  >
                    <span className="font-mono bg-white/10 px-2 py-0.5 rounded text-white font-semibold">
                      {op.op_id}
                    </span>
                    <span className="font-semibold text-white">{op.label}</span>
                    <span className="text-white/60">→ {op.machine}</span>
                    <span className="text-white/50">({op.duration} units)</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Maintenance Windows */}
      {instanceDetails.maintenance.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            Maintenance Windows ({instanceDetails.maintenance.length})
          </h3>
          <div className="space-y-2">
            {instanceDetails.maintenance.map((maint, idx) => (
              <div key={idx} className="p-3 bg-slate-100 rounded-lg text-sm">
                <span className="font-medium text-slate-900">{maint.label}</span>
                <span className="text-slate-600 mx-2">on</span>
                <span className="font-medium text-slate-900">{maint.machine}</span>
                <span className="text-slate-600 mx-2">from</span>
                <span className="font-mono text-slate-900">{maint.start}</span>
                <span className="text-slate-600 mx-2">for</span>
                <span className="font-mono text-slate-900">{maint.duration} units</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
