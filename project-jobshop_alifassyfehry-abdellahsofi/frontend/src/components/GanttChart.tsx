import { useStore } from '../store/useStore';
import { BarChart3 } from 'lucide-react';
import { getJobColor, MAINTENANCE_COLOR } from '../lib/utils';
import { useMemo, useState } from 'react';

export default function GanttChart() {
  const { solution, instanceDetails } = useStore();
  const [hoveredJob, setHoveredJob] = useState<string | null>(null);

  const { jobColors, maxTime, machines } = useMemo(() => {
    if (!solution || !instanceDetails) {
      return { jobColors: {}, maxTime: 0, machines: [] };
    }

    // Create color mapping for jobs
    const uniqueJobs = Array.from(new Set(solution.operations.map((op) => op.job_id)));
    const colors: Record<string, string> = {};
    uniqueJobs.forEach((job, idx) => {
      colors[job] = getJobColor(job, idx);
    });

    // Calculate max time for x-axis
    const operationEnds = solution.operations.map((op) => op.end);
    const maintenanceEnds = (instanceDetails.maintenance || []).map(
      (m) => m.start + m.duration
    );
    const max = Math.max(...operationEnds, ...maintenanceEnds, solution.makespan || 0);

    return {
      jobColors: colors,
      maxTime: Math.ceil(max * 1.2), // Add 20% padding
      machines: instanceDetails.machines,
    };
  }, [solution, instanceDetails]);

  if (!solution || !instanceDetails) return null;

  // Group operations by machine
  const machineOperations = useMemo(() => {
    const grouped: Record<string, typeof solution.operations> = {};
    
    machines.forEach((machine) => {
      grouped[machine] = solution.operations.filter((op) => op.machine === machine);
    });
    
    return grouped;
  }, [solution.operations, machines]);

  // Calculate scale
  const pixelsPerUnit = 800 / maxTime;
  const rowHeight = 60;
  const chartHeight = machines.length * (rowHeight + 10) + 40;

  return (
    <div className="card-hover">
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-2 rounded-xl shadow-lg">
          <BarChart3 className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Gantt Chart</h2>
      </div>

      {/* Legend */}
      <div className="mb-6 flex flex-wrap gap-3">
        {Object.entries(jobColors).map(([job, color]) => (
          <div key={job} className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
            <div
              className="w-4 h-4 rounded-full shadow-lg"
              style={{ backgroundColor: color }}
            />
            <span className="text-sm font-semibold text-white">{job}</span>
          </div>
        ))}
        {instanceDetails.maintenance.length > 0 && (
          <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
            <div
              className="w-4 h-4 rounded-full shadow-lg"
              style={{ backgroundColor: MAINTENANCE_COLOR }}
            />
            <span className="text-sm font-semibold text-white">Maintenance</span>
          </div>
        )}
      </div>

      {/* Chart Container */}
      <div className="overflow-x-auto bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
        <svg width="900" height={chartHeight} className="font-sans">
          {/* Y-axis labels (machines) */}
          {machines.map((machine, idx) => (
            <text
              key={machine}
              x="10"
              y={idx * (rowHeight + 10) + rowHeight / 2 + 5}
              className="text-sm font-bold fill-white"
            >
              {machine}
            </text>
          ))}

          {/* Operations */}
          {machines.map((machine, machineIdx) => {
            const operations = machineOperations[machine] || [];
            const y = machineIdx * (rowHeight + 10);

            return (
              <g key={machine}>
                {/* Machine row background */}
                <rect
                  x="150"
                  y={y}
                  width="800"
                  height={rowHeight}
                  fill="rgba(255,255,255,0.03)"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="1.5"
                  rx="8"
                />

                {/* Maintenance windows for this machine */}
                {instanceDetails.maintenance
                  .filter((m) => m.machine === machine)
                  .map((maint, idx) => {
                    const x = 150 + maint.start * pixelsPerUnit;
                    const width = maint.duration * pixelsPerUnit;

                    return (
                      <g key={`maint-${idx}`}>
                        <rect
                          x={x}
                          y={y + 5}
                          width={width}
                          height={rowHeight - 10}
                          fill={MAINTENANCE_COLOR}
                          opacity="0.8"
                          stroke="rgba(255,255,255,0.3)"
                          strokeWidth="2"
                          rx="8"
                          style={{ filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))' }}
                        />
                        <text
                          x={x + width / 2}
                          y={y + rowHeight / 2 + 5}
                          className="text-xs fill-white font-bold"
                          textAnchor="middle"
                          style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
                        >
                          {maint.label}
                        </text>
                      </g>
                    );
                  })}

                {/* Operations */}
                {operations.map((op) => {
                  const x = 150 + op.start * pixelsPerUnit;
                  const width = op.duration * pixelsPerUnit;
                  const color = jobColors[op.job_id];

                  const isHovered = hoveredJob === op.job_id;
                  const isDimmed = hoveredJob !== null && !isHovered;

                  return (
                    <g 
                      key={`${op.job_id}-${op.op_id}`}
                      onMouseEnter={() => setHoveredJob(op.job_id)}
                      onMouseLeave={() => setHoveredJob(null)}
                    >
                      <rect
                        x={x}
                        y={y + 5}
                        width={width}
                        height={rowHeight - 10}
                        fill={color}
                        stroke="rgba(255,255,255,0.3)"
                        strokeWidth={isHovered ? 3 : 2}
                        rx="8"
                        className="cursor-pointer transition-all duration-200"
                        style={{ 
                          filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.4))',
                          opacity: isDimmed ? 0.3 : 1,
                        }}
                      >
                        <title>
                          {op.job_id} - {op.label}
                          {'\n'}Start: {op.start}, End: {op.end}
                          {'\n'}Duration: {op.duration}
                        </title>
                      </rect>
                      <text
                        x={x + width / 2}
                        y={y + rowHeight / 2 - 5}
                        className="text-xs fill-white font-bold pointer-events-none"
                        textAnchor="middle"
                        style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)', opacity: isDimmed ? 0.5 : 1 }}
                      >
                        {op.label.length > 15 ? op.label.substring(0, 12) + '...' : op.label}
                      </text>
                      <text
                        x={x + width / 2}
                        y={y + rowHeight / 2 + 10}
                        className="text-xs fill-white opacity-90 font-semibold pointer-events-none"
                        textAnchor="middle"
                        style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)', opacity: isDimmed ? 0.5 : 1 }}
                      >
                        {op.start} → {op.end}
                      </text>
                    </g>
                  );
                })}
              </g>
            );
          })}

          {/* X-axis */}
          <line
            x1="150"
            y1={chartHeight - 30}
            x2="950"
            y2={chartHeight - 30}
            stroke="rgba(255,255,255,0.3)"
            strokeWidth="2"
          />

          {/* X-axis labels */}
          {Array.from({ length: Math.ceil(maxTime / 5) + 1 }).map((_, i) => {
            const time = i * 5;
            const x = 150 + time * pixelsPerUnit;
            return (
              <g key={time}>
                <line
                  x1={x}
                  y1={chartHeight - 35}
                  x2={x}
                  y2={chartHeight - 25}
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="1.5"
                />
                <text
                  x={x}
                  y={chartHeight - 10}
                  className="text-xs fill-white/70 font-semibold"
                  textAnchor="middle"
                >
                  {time}
                </text>
              </g>
            );
          })}

          {/* Makespan line */}
          {solution.makespan && (
            <g>
              <line
                x1={150 + solution.makespan * pixelsPerUnit}
                y1="0"
                x2={150 + solution.makespan * pixelsPerUnit}
                y2={chartHeight - 30}
                stroke="#f59e0b"
                strokeWidth="3"
                strokeDasharray="8,4"
                opacity="0.8"
              />
              <rect
                x={150 + solution.makespan * pixelsPerUnit - 60}
                y="5"
                width="120"
                height="24"
                fill="rgba(245, 158, 11, 0.2)"
                stroke="rgba(245, 158, 11, 0.5)"
                strokeWidth="2"
                rx="6"
              />
              <text
                x={150 + solution.makespan * pixelsPerUnit}
                y="20"
                className="text-sm fill-amber-400 font-bold"
                textAnchor="middle"
                style={{ textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}
              >
                Makespan: {solution.makespan}
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Time axis label */}
      <div className="text-center mt-4 text-sm text-white/70 font-semibold">
        Temps (unites)
      </div>
    </div>
  );
}
