import { client } from '../client';
import { ApiResponse } from '../types';

export const csvService = {
    uploadCsv: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await client.post<ApiResponse<string>>('/files/csv/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
    
    getCsvFiles: async () => {
        const response = await client.get<ApiResponse<string[]>>('/files/csv');
        return response.data;
    }
}; 