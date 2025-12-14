import { useEffect } from 'react';
import { useStore } from '../store/useStore';
import { apiService } from '../services/api';
import { ChevronDown } from 'lucide-react';
import { cn } from '../lib/utils';

export default function InstanceSelector() {
  const {
    instances,
    selectedInstance,
    setSelectedInstance,
    setInstanceDetails,
    setSolution,
    setError,
  } = useStore();

      const scenarioLabels: Record<string, string> = {
    scenario_normal: 'Scenario normal (flux nominal + commande flash)',
    scenario_maintenance: 'Scenario normal + maintenance',
    scenario_rush_150: 'Scenario rush 150 commandes',
    scenario_rush_300: 'Scenario rush 300 commandes',
    scenario_rush_450: 'Scenario rush 450 commandes',
  };

  useEffect(() => {
    if (selectedInstance) {
      loadInstanceDetails(selectedInstance);
    }
  }, [selectedInstance]);

  const loadInstanceDetails = async (name: string) => {
    try {
      const details = await apiService.getInstanceDetails(name);
      setInstanceDetails(details);
      setSolution(null); // Clear previous solution
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load instance details');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedInstance(e.target.value);
  };

  return (
    <div className="card-hover p-0">
      <div className="relative">
        <select
          value={selectedInstance || ''}
          onChange={handleChange}
          className={cn(
            "input-field appearance-none cursor-pointer pr-10 w-full"
          )}
          style={{ colorScheme: 'dark' }}
        >
          <option value="" className="bg-slate-800 text-white">Selectionner un scenario de production...</option>
          {instances.map((instance) => (
            <option key={instance.name} value={instance.name} className="bg-slate-800 text-white">
              {scenarioLabels[instance.name] || instance.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50 pointer-events-none" />
      </div>
    </div>
  );
}
