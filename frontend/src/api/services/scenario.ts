import { apiClient } from '../client';
import { Scenario, ScenarioCreate, ScenarioUpdate } from '../types';

export const scenarioService = {
    getAll: () => apiClient.get<Scenario[]>('/scenarios'),
    getById: (id: number) => apiClient.get<Scenario>(`/scenarios/${id}`),
    getByCategory: (categoryId: number) => apiClient.get<Scenario[]>(`/scenarios/category/${categoryId}`),
    create: (data: ScenarioCreate) => apiClient.post<Scenario>('/scenarios', data),
    update: (id: number, data: ScenarioUpdate) => apiClient.put<Scenario>(`/scenarios/${id}`, data),
    delete: (id: number) => apiClient.delete(`/scenarios/${id}`),
    generate: (categoryType: string, inputData: any) => apiClient.post(`/generator/${categoryType}`, inputData),
}; 