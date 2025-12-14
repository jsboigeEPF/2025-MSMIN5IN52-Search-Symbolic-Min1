import { useEffect, useState } from 'react';
import { useStore } from './store/useStore';
import { apiService, createWebSocketConnection } from './services/api';
import StatsOverview from './components/StatsOverview';
import Sidebar from './components/Sidebar';
import Welcome from './components/Welcome';
import SolutionMetrics from './components/SolutionMetrics';
import GanttChart from './components/GanttChart';
import InstanceDetails from './components/InstanceDetails';
import SolverProgress from './components/SolverProgress';
import SuccessToast from './components/SuccessToast';
import { CustomInstanceBuilder } from './components/CustomInstanceBuilder';
import { NotificationCenter } from './components/NotificationCenter';
import { BottleneckAnalyzer } from './components/BottleneckAnalyzer';
import { WhatIfAnalysis } from './components/WhatIfAnalysis';
import { ThemeToggle } from './components/ThemeToggle';
import { AlertCircle, Loader2, Wrench, GitCompare, TrendingUp, Activity } from 'lucide-react';

type TabView = 'solver' | 'builder' | 'comparison' | 'analytics';

function App() {
  const {
    instances,
    selectedInstance,
    solution,
    loading,
    error,
    solving,
    setInstances,
    setError,
    setSolving,
  } = useStore();

  const [wsConnected, setWsConnected] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [prevSolving, setPrevSolving] = useState(false);
  const [currentTab, setCurrentTab] = useState<TabView>('solver');

  // Detect when solving completes successfully
  useEffect(() => {
    if (prevSolving && !solving && solution) {
      setShowSuccess(true);
    }
    setPrevSolving(solving);
  }, [solving, solution, prevSolving]);

  useEffect(() => {
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.classList.add(savedTheme === 'dark' ? 'dark-theme' : 'light-theme');

    // Load instances
    const loadInstances = async () => {
      try {
        const data = await apiService.getInstances();
        setInstances(data.instances);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load instances');
      }
    };

    loadInstances();

    // Setup WebSocket
    const ws = createWebSocketConnection((message) => {
      console.log('WebSocket message:', message);
      
      if (message.type === 'solving_started') {
        setSolving(true);
      } else if (message.type === 'solving_completed') {
        setSolving(false);
      } else if (message.type === 'solving_error') {
        setSolving(false);
        setError(message.error || 'Solver error');
      }
    });

    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [setInstances, setError, setSolving]);

  const tabs: { id: TabView; label: string; icon: any }[] = [
    { id: 'solver', label: 'Solver', icon: Activity },
    { id: 'builder', label: 'Custom Builder', icon: Wrench },
    { id: 'comparison', label: 'What-If Analysis', icon: GitCompare },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Enhanced Header */}
      <header className="glass-panel border-b border-white/20 shadow-2xl sticky top-0 z-50">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-red-500 to-orange-500 p-3 rounded-2xl shadow-lg shadow-red-500/50 transform hover:scale-110 transition-transform duration-300">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold gradient-text animate-fade-in">
                  Job-Shop Scheduler
                </h1>
                <p className="text-sm text-white/70 font-medium flex items-center gap-2">
                  <span className={`inline-block w-2 h-2 rounded-full animate-pulse ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`}></span>
                  {wsConnected ? 'Connected' : 'Disconnected'} • Advanced Scheduling Platform
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <NotificationCenter />
            </div>
          </div>
          
          {/* Tab Navigation */}
          <div className="flex gap-2 pb-4 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setCurrentTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-300 whitespace-nowrap ${
                    currentTab === tab.id
                      ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white shadow-lg'
                      : 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </header>
      
      <main className="flex-1 max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Error Display */}
        {error && (
          <div className="glass-panel border-red-500/50 p-6 flex items-start gap-3 animate-pulse mb-8">
            <div className="bg-red-500 p-2 rounded-xl shadow-lg">
              <AlertCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-white text-lg">Error</h3>
              <p className="text-white/80 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="glass-panel p-8 flex items-center gap-4">
              <Loader2 className="w-10 h-10 animate-spin text-red-400" />
              <span className="text-white text-lg font-semibold">Loading instances...</span>
            </div>
          </div>
        )}

        {/* Tab Content */}
        {!loading && (
          <>
            {currentTab === 'solver' && instances.length > 0 && (
              <div className="flex flex-col lg:flex-row gap-8 h-full">
                <Sidebar />
                
                <div className="flex-1 flex flex-col gap-8">
                  <StatsOverview />
                  
                  {solution ? (
                    <div className="space-y-8 animate-slide-up">
                      <InstanceDetails />
                      <SolutionMetrics />
                      <GanttChart />
                      {selectedInstance && (
                        <BottleneckAnalyzer instanceName={selectedInstance} />
                      )}
                    </div>
                  ) : (
                    <Welcome />
                  )}
                </div>
              </div>
            )}

            {currentTab === 'builder' && (
              <CustomInstanceBuilder onInstanceCreated={() => {
                // Reload instances
                apiService.getInstances().then(data => setInstances(data.instances));
              }} />
            )}

            {currentTab === 'comparison' && (
              <WhatIfAnalysis />
            )}

            {currentTab === 'analytics' && selectedInstance && (
              <div className="max-w-6xl mx-auto">
                <BottleneckAnalyzer instanceName={selectedInstance} />
              </div>
            )}
          </>
        )}
      </main>

      {/* Solver Progress Modal */}
      <SolverProgress isActive={solving} />
      
      {/* Success Toast */}
      <SuccessToast show={showSuccess} onClose={() => setShowSuccess(false)} />
    </div>
  );
}

export default App;
