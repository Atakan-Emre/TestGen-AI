import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL, IS_DEMO_MODE } from '../config';
import { DEMO_MUTATION_MESSAGE, demoCsvFiles } from '../demo/demoData';

export interface CsvFile {
  id: number;
  name: string;
  content: string;
  size: number;
  created_at: string;
  updated_at: string | null;
  source?: string;
}

export const useCsvFiles = () => {
  const [csvFiles, setCsvFiles] = useState<CsvFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<CsvFile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCsvFiles = async () => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setCsvFiles(demoCsvFiles);
        setError(null);
        return;
      }
      const response = await axios.get<CsvFile[]>(`${API_URL}/csv`);
      setCsvFiles(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'CSV dosyaları yüklenirken hata oluştu');
      console.error('CSV dosyaları yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const syncCsvFiles = async () => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setCsvFiles(demoCsvFiles);
        setError(null);
        return;
      }
      await axios.post(`${API_URL}/csv/sync`);
      await fetchCsvFiles();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'CSV dosyaları senkronize edilirken hata oluştu');
      console.error('CSV dosyaları senkronize edilirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const uploadCsvFile = async (file: File) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${API_URL}/csv/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      await fetchCsvFiles();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'CSV dosyası yüklenirken hata oluştu');
      console.error('CSV dosyası yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteCsvFile = async (fileId: number) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      await axios.delete(`${API_URL}/csv/${fileId}`);
      await fetchCsvFiles();
      if (selectedFile?.id === fileId) {
        setSelectedFile(null);
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'CSV dosyası silinirken hata oluştu');
      console.error('CSV dosyası silinirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewCsvFile = async (fileId: number) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        const file = demoCsvFiles.find((item) => item.id === fileId) || null;
        setSelectedFile(file);
        setError(null);
        return;
      }
      // Tüm dosyalar artık veritabanında, normal endpoint'i kullan
      const response = await axios.get<CsvFile>(`${API_URL}/csv/${fileId}`);
      setSelectedFile(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'CSV dosyası görüntülenirken hata oluştu');
      console.error('CSV dosyası görüntülenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCsvFiles();
  }, []);

  return {
    csvFiles,
    selectedFile,
    loading,
    error,
    fetchCsvFiles,
    syncCsvFiles,
    uploadCsvFile,
    deleteCsvFile,
    viewCsvFile,
  };
}; 
