import { apiClient } from '../client';
import { ApiResponse } from '../types';

export const getFiles = async (type: 'csv' | 'json'): Promise<string[]> => {
  const response = await apiClient.get<ApiResponse<string[]>>(`/files/${type}`);
  return response.data.files;
};

export const uploadFile = async (file: File, type: 'csv' | 'json'): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);

  await apiClient.post(`/files/${type}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const deleteFile = async (filename: string, type: 'csv' | 'json'): Promise<void> => {
  await apiClient.delete(`/files/${type}/${encodeURIComponent(filename)}`);
};

export const filesService = {
    uploadFile: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post('/files/upload', formData);
    },
    // ... diğer metodlar
}; 