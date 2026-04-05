import { apiClient } from '../client';

export interface BusinessRule {
  id: number;
  name: string;
  content: string;
  source: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface BusinessRuleCreate {
  name: string;
  content: string;
  source?: string;
  is_active?: boolean;
}

export interface BusinessRuleUpdate {
  name?: string;
  content?: string;
  is_active?: boolean;
}

export const businessRuleService = {
  // Tüm iş kurallarını listele
  getBusinessRules: async (): Promise<BusinessRule[]> => {
    const response = await apiClient.get('/business-rules/');
    return response.data;
  },

  // Belirli bir iş kuralını getir
  getBusinessRule: async (id: number): Promise<BusinessRule> => {
    const response = await apiClient.get(`/business-rules/${id}`);
    return response.data;
  },

  // Yeni iş kuralı oluştur
  createBusinessRule: async (rule: BusinessRuleCreate): Promise<BusinessRule> => {
    const response = await apiClient.post('/business-rules/', rule);
    return response.data;
  },

  // İş kuralını güncelle
  updateBusinessRule: async (id: number, rule: BusinessRuleUpdate): Promise<BusinessRule> => {
    const response = await apiClient.put(`/business-rules/${id}`, rule);
    return response.data;
  },

  // İş kuralını sil
  deleteBusinessRule: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/business-rules/${id}`);
    return response.data;
  },

  // Tüm iş kurallarını sil
  deleteAllBusinessRules: async (): Promise<{ message: string }> => {
    const response = await apiClient.delete('/business-rules/');
    return response.data;
  },

  // Dosya yönetimi endpoint'leri
  getBusinessRuleFiles: async (): Promise<{ files: any[] }> => {
    const response = await apiClient.get('/business-rules/files');
    return response.data;
  },

  getBusinessRuleFileContent: async (filename: string): Promise<any> => {
    const response = await apiClient.get(`/business-rules/files/${filename}`);
    return response.data;
  },

  deleteBusinessRuleFile: async (filename: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/business-rules/files/${filename}`);
    return response.data;
  },

  renameBusinessRuleFile: async (filename: string, newName: string): Promise<{ message: string }> => {
    const response = await apiClient.put(`/business-rules/files/${filename}`, { new_name: newName });
    return response.data;
  },

  deleteAllBusinessRuleFiles: async (): Promise<{ message: string }> => {
    const response = await apiClient.delete('/business-rules/files');
    return response.data;
  }
};
