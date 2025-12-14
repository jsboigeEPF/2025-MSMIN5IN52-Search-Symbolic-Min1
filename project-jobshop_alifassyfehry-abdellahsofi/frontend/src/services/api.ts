import axios from 'axios';
import type { Instance, InstanceDetails, SolveRequest, SolutionResponse, VisualizationData } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Get all instances
  async getInstances(): Promise<{ instances: Instance[]; total: number }> {
    const response = await api.get('/instances');
    return response.data;
  },

  // Get instance details
  async getInstanceDetails(instanceName: string): Promise<InstanceDetails> {
    const response = await api.get(`/instances/${instanceName}`);
    return response.data;
  },

  // Solve instance
  async solveInstance(request: SolveRequest): Promise<SolutionResponse> {
    const response = await api.post('/solve', request);
    return response.data;
  },

  // Get visualization data
  async getVisualizationData(instanceName: string): Promise<VisualizationData> {
    const response = await api.get(`/visualization/${instanceName}`);
    return response.data;
  },

  // Custom Instance Management
  async createCustomInstance(instance: any): Promise<{ success: boolean; instance_id: number; name: string }> {
    const response = await api.post('/instances/custom', instance);
    return response.data;
  },

  async updateCustomInstance(instanceName: string, instance: any): Promise<{ success: boolean; instance_id: number }> {
    const response = await api.put(`/instances/custom/${instanceName}`, instance);
    return response.data;
  },

  async deleteCustomInstance(instanceName: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/instances/custom/${instanceName}`);
    return response.data;
  },

  async getCustomInstances(): Promise<{ instances: any[]; total: number }> {
    const response = await api.get('/instances/custom');
    return response.data;
  },

  async importFromCsv(csvContent: string): Promise<{ success: boolean; jobs: any; machines: string[]; preview: string }> {
    const response = await api.post('/instances/import-csv', { csv_content: csvContent });
    return response.data;
  },

  // Solution History
  async getSolutionHistory(instanceName: string, limit: number = 10): Promise<{ history: any[]; total: number }> {
    const response = await api.get(`/solutions/history/${instanceName}`, { params: { limit } });
    return response.data;
  },

  // Batch Processing
  async batchSolve(instanceNames: string[], timeLimit?: number, numWorkers: number = 8): Promise<{ results: any[]; total: number }> {
    const response = await api.post('/batch-solve', { instance_names: instanceNames, time_limit: timeLimit, num_workers: numWorkers });
    return response.data;
  },

  // Webhooks
  async registerWebhook(url: string, event: string): Promise<{ success: boolean; webhook_id: number }> {
    const response = await api.post('/webhooks', { url, event });
    return response.data;
  },

  async getWebhooks(): Promise<{ webhooks: any[]; total: number }> {
    const response = await api.get('/webhooks');
    return response.data;
  },

  // Notifications
  async getNotifications(unreadOnly: boolean = false, limit: number = 50): Promise<{ notifications: any[]; total: number }> {
    const response = await api.get('/notifications', { params: { unread_only: unreadOnly, limit } });
    return response.data;
  },

  async markNotificationRead(notificationId: number): Promise<{ success: boolean }> {
    const response = await api.put(`/notifications/${notificationId}/read`);
    return response.data;
  },

  // Analytics
  async analyzeBottlenecks(instanceName: string): Promise<any> {
    const response = await api.get(`/analytics/bottlenecks/${instanceName}`);
    return response.data;
  },

  async compareInstances(instanceNames: string): Promise<{ comparisons: any[]; total: number }> {
    const response = await api.get('/analytics/comparison', { params: { instance_names: instanceNames } });
    return response.data;
  },
};

// WebSocket connection
export const createWebSocketConnection = (onMessage: (message: any) => void): WebSocket => {
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      onMessage(message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket connection closed');
  };

  return ws;
};
