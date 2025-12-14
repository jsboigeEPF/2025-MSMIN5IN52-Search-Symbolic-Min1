import InstanceSelector from './InstanceSelector';
import SolverControls from './SolverControls';
import { SlidersHorizontal, Database } from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className="glass-panel p-6 space-y-8 w-full lg:w-96 lg:h-full lg:overflow-y-auto scrollbar-hide animate-slide-up">
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-gradient-to-br from-red-500 to-orange-500 p-2 rounded-xl shadow-lg">
            <Database className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-white">1. Selectionner un scenario de production</h2>
        </div>
        <InstanceSelector />
      </div>
      
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-gradient-to-br from-orange-500 to-yellow-500 p-2 rounded-xl shadow-lg">
            <SlidersHorizontal className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-white">2. Configurer le solveur</h2>
        </div>
        <SolverControls />
      </div>
    </aside>
  );
}
