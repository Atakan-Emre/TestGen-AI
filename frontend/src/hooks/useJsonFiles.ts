import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API_URL, IS_DEMO_MODE } from '../config';
import {
  DEMO_MUTATION_MESSAGE,
  demoJsonFiles,
  getDemoJsonFileById,
} from '../demo/demoData';

export interface JsonFile {
  id: number;
  name: string;
  content: unknown;
  size: number;
  created_at: string;
  updated_at: string | null;
  type: string;
  source?: string;
}

export const useJsonFiles = () => {
  const [jsonFiles, setJsonFiles] = useState<JsonFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<JsonFile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJsonFiles = useCallback(async () => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setJsonFiles(demoJsonFiles);
        setError(null);
        return;
      }
      const response = await axios.get<JsonFile[]>(`${API_URL}/json`);
      setJsonFiles(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'JSON dosyaları yüklenirken hata oluştu');
      console.error('JSON dosyaları yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const syncJsonFiles = useCallback(async () => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setJsonFiles(demoJsonFiles);
        setError(null);
        return;
      }
      await axios.post(`${API_URL}/json/sync`);
      await fetchJsonFiles();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'JSON dosyaları senkronize edilirken hata oluştu');
      console.error('JSON dosyaları senkronize edilirken hata:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchJsonFiles]);

  const uploadJsonFile = useCallback(async (file: File) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${API_URL}/json/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      await fetchJsonFiles();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'JSON dosyası yüklenirken hata oluştu');
      console.error('JSON dosyası yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchJsonFiles]);

  const deleteJsonFile = useCallback(async (fileId: number) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      await axios.delete(`${API_URL}/json/${fileId}`);
      await fetchJsonFiles();
      if (selectedFile?.id === fileId) {
        setSelectedFile(null);
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'JSON dosyası silinirken hata oluştu');
      console.error('JSON dosyası silinirken hata:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchJsonFiles, selectedFile?.id]);

  const viewJsonFile = useCallback(async (fileId: number) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setSelectedFile(getDemoJsonFileById(fileId));
        setError(null);
        return;
      }
      // Tüm dosyalar artık veritabanında, normal endpoint'i kullan
      const response = await axios.get<JsonFile>(`${API_URL}/json/${fileId}`);
      setSelectedFile(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'JSON dosyası görüntülenirken hata oluştu');
      console.error('JSON dosyası görüntülenirken hata:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJsonFiles();
  }, [fetchJsonFiles]);

  return {
    jsonFiles,
    selectedFile,
    loading,
    error,
    fetchJsonFiles,
    syncJsonFiles,
    uploadJsonFile,
    deleteJsonFile,
    viewJsonFile,
  };
}; 
