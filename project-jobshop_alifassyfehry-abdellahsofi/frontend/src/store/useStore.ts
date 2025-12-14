import { create } from 'zustand';
import type { Instance, SolutionResponse, InstanceDetails } from '../types';

interface AppState {
  instances: Instance[];
  selectedInstance: string | null;
  instanceDetails: InstanceDetails | null;
  solution: SolutionResponse | null;
  loading: boolean;
  error: string | null;
  solving: boolean;
  
  setInstances: (instances: Instance[]) => void;
  setSelectedInstance: (name: string) => void;
  setInstanceDetails: (details: InstanceDetails | null) => void;
  setSolution: (solution: SolutionResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSolving: (solving: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  instances: [],
  selectedInstance: null,
  instanceDetails: null,
  solution: null,
  loading: false,
  error: null,
  solving: false,
  
  setInstances: (instances) => set({ instances }),
  setSelectedInstance: (name) => set({ selectedInstance: name }),
  setInstanceDetails: (details) => set({ instanceDetails: details }),
  setSolution: (solution) => set({ solution }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setSolving: (solving) => set({ solving }),
}));
