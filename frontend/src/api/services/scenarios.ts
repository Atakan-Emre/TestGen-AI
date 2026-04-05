import { apiClient } from '../client';

export const scenariosService = {
    getScenarios: () => apiClient.get('/scenarios'),
    deleteScenario: (filename: string) => apiClient.delete(`/scenarios/${filename}`),
    generateScenarios: (data: any) => apiClient.post('/generate-scenarios', data)
}; 