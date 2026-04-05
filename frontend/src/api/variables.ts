import { VariableProfileInfo, VariableProfilesResponse, VariablePreviewResponse } from '../types/variables';
import { API_URL } from '../config';

export const variablesApi = {
  /**
   * Mevcut variables profillerini listeler
   */
  async fetchProfiles(): Promise<VariableProfileInfo[]> {
    try {
      const response = await fetch(`${API_URL}/variables/profiles`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: VariableProfilesResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'Profil listesi alınamadı');
      }
      
      return data.data;
    } catch (error) {
      console.error('Variables profilleri yüklenirken hata:', error);
      throw error;
    }
  },

  /**
   * Belirtilen variables profilini önizleme için getirir
   */
  async fetchProfile(name: string): Promise<Record<string, string>> {
    try {
      const response = await fetch(`${API_URL}/variables/profiles/${encodeURIComponent(name)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: VariablePreviewResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'Profil yüklenemedi');
      }
      
      return data.data;
    } catch (error) {
      console.error(`Variables profil yüklenirken hata (${name}):`, error);
      throw error;
    }
  },

  /**
   * Yeni variables profil yükler
   */
  async uploadProfile(file: File, name: string, format: 'txt' | 'json' | 'yaml'): Promise<void> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      formData.append('format', format);

      const response = await fetch(`${API_URL}/variables/profiles/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Variables profil yüklenirken hata:', error);
      throw error;
    }
  },

  /**
   * Variables profilini siler
   */
  async deleteProfile(name: string): Promise<void> {
    try {
      const response = await fetch(`${API_URL}/variables/profiles/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error(`Variables profil silinirken hata (${name}):`, error);
      throw error;
    }
  },

  /**
   * Variables profillerini senkronize eder
   */
  async syncProfiles(): Promise<void> {
    try {
      const response = await fetch(`${API_URL}/variables/sync`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Variables profilleri senkronize edilirken hata:', error);
      throw error;
    }
  }
};
