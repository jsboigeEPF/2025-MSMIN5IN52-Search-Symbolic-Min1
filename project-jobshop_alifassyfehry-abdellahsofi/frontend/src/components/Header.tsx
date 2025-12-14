import { Package, WifiOff, Wifi } from 'lucide-react';

interface HeaderProps {
  wsConnected: boolean;
}

export default function Header({ wsConnected }: HeaderProps) {
  return (
    <header className="glass-panel border-b border-white/20 shadow-2xl sticky top-0 z-50 mb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-gradient-to-br from-red-500 to-orange-500 p-3 rounded-2xl shadow-lg shadow-red-500/50 transform hover:scale-110 transition-transform duration-300">
              <Package className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold gradient-text animate-fade-in">
                Job-Shop Scheduler
              </h1>
              <p className="text-sm text-white/70 font-medium flex items-center gap-2">
                <span className="inline-block w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                Constraint Programming with OR-Tools CP-SAT
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full border border-white/20">
            {wsConnected ? (
              <div className="flex items-center gap-2 text-green-400">
                <Wifi className="w-5 h-5" />
                <span className="text-sm font-semibold hidden sm:inline">Connected</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-400">
                <WifiOff className="w-5 h-5" />
                <span className="text-sm font-semibold hidden sm:inline">Disconnected</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
