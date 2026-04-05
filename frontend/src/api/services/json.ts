import { client } from '../client';
import { ApiResponse } from '../types';

export const jsonService = {
    uploadJson: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await client.post<ApiResponse<string>>('/files/json/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
    
    getJsonFiles: async () => {
        const response = await client.get<ApiResponse<string[]>>('/files/json');
        return response.data;
    }
}; 