// API Types
export interface Instance {
  name: string;
  description: string;
  num_jobs: number;
  num_machines: number;
  num_operations: number;
  horizon: number;
  machines: string[];
  has_maintenance: boolean;
}

export interface InstanceDetails {
  name: string;
  description: string;
  machines: string[];
  jobs: Job[];
  maintenance: MaintenanceWindow[];
  horizon: number;
}

export interface Job {
  job_id: string;
  operations: Operation[];
}

export interface Operation {
  op_id: number;
  machine: string;
  duration: number;
  label: string;
}

export interface MaintenanceWindow {
  machine: string;
  start: number;
  duration: number;
  label: string;
}

export interface SolveRequest {
  instance_name: string;
  time_limit?: number;
  num_workers: number;
}

export interface SolutionResponse {
  status: string;
  makespan: number | null;
  operations: ScheduledOperation[];
  solver_statistics: SolverStatistics;
}

export interface ScheduledOperation {
  job_id: string;
  op_id: number;
  machine: string;
  start: number;
  end: number;
  duration: number;
  label: string;
}

export interface SolverStatistics {
  wall_time: number;
  best_bound?: number;
  conflicts?: number;
  branches?: number;
  error?: string;
}

export interface VisualizationData {
  data: GanttItem[];
  makespan: number | null;
  status: string;
  machines: string[];
}

export interface GanttItem {
  job: string;
  operation: number | string;
  etape: string;
  machine: string;
  start: number;
  end: number;
  duration: number;
  label: string;
  type: 'operation' | 'maintenance';
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'solving_started' | 'solving_completed' | 'solving_error' | 'instance_created' | 'instance_updated' | 'instance_deleted';
  instance?: string;
  instance_name?: string;
  status?: string;
  makespan?: number;
  error?: string;
}

// Custom Instance Types
export interface CustomJob {
  job_id: string;
  operations: CustomOperation[];
  priority?: number;
  deadline?: number;
  release_time?: number;
}

export interface CustomOperation {
  machine: string;
  duration: number;
  label: string;
  setup_time?: number;
}

export interface CustomInstance {
  name: string;
  description: string;
  jobs: CustomJob[];
  machines: string[];
  maintenance?: MaintenanceWindow[];
}

// Notification Types
export interface Notification {
  id: number;
  type: string;
  message: string;
  data?: any;
  read: boolean;
  created_at: string;
}

// Bottleneck Analysis
export interface Bottleneck {
  machine: string;
  busy_time: number;
  utilization_percent: number;
  is_bottleneck: boolean;
}

export interface BottleneckAnalysis {
  instance_name: string;
  makespan: number | null;
  bottlenecks: Bottleneck[];
  recommendations: string[];
}

// Comparison
export interface InstanceComparison {
  name: string;
  makespan: number | null;
  status: string;
  num_jobs: number;
  num_machines: number;
  wall_time: number;
}

// Solution History
export interface SolutionHistoryItem {
  id: number;
  status: string;
  makespan: number | null;
  created_at: string;
}

// Theme
export type Theme = 'dark' | 'light';
