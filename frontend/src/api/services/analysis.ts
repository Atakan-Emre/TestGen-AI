import { client } from '../client';
import { ApiResponse } from '../types';

export const analysisService = {
    analyze: async (data: any) => {
        const response = await client.post<ApiResponse<any>>('/analysis', data);
        return response.data;
    },
    
    getResults: async () => {
        const response = await client.get<ApiResponse<any[]>>('/analysis/results');
        return response.data;
    }
}; 