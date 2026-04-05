import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL, IS_DEMO_MODE } from '../config';
import type { Scenario, ScenarioMetadata } from '../api/types';
import {
  DEMO_MUTATION_MESSAGE,
  demoScenarios,
  getDemoScenarioDetail,
} from '../demo/demoData';

interface ScenarioDetailResponse {
  content: string;
  metadata?: ScenarioMetadata | null;
}

export const useScenarios = () => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchScenarios = async () => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setScenarios(demoScenarios);
        setError(null);
        return;
      }
      const response = await axios.get(`${API_URL}/scenarios`);
      
      if (!response.data) {
        throw new Error('Veri alınamadı');
      }

      const transformedScenarios = response.data.map((scenario: Scenario) => ({
        ...scenario,
        full_name: `/app/data/output/test_scenarios/${scenario.filename || `${scenario.name}_${scenario.date}.txt`}`
      }));
      
      setScenarios(transformedScenarios);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching scenarios:', err);
      setError(err.response?.data?.detail || 'Senaryolar yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const syncScenarios = async () => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setScenarios(demoScenarios);
        setError(null);
        return;
      }
      await axios.post(`${API_URL}/scenarios/sync`);
      await fetchScenarios();
      setError(null);
    } catch (err: any) {
      console.error('Error syncing scenarios:', err);
      setError(err.response?.data?.detail || 'Senaryolar senkronize edilirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const uploadScenario = async (file: File) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${API_URL}/scenarios/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      await fetchScenarios();
      setError(null);
    } catch (err: any) {
      console.error('Error uploading scenario:', err);
      setError(err.response?.data?.detail || 'Senaryo yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const deleteScenario = async (id: number | string) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      const scenario = scenarios.find((s) => String(s.id) === String(id));
      if (!scenario) {
        throw new Error('Senaryo bulunamadı');
      }
      await axios.delete(`${API_URL}/scenarios/${scenario.filename}`);
      await fetchScenarios();
      setError(null);
    } catch (err: any) {
      console.error('Error deleting scenario:', err);
      setError(err.response?.data?.detail || 'Senaryo silinirken bir hata oluştu');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getScenarioDetail = async (filename: string): Promise<ScenarioDetailResponse> => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        setError(null);
        return getDemoScenarioDetail(filename);
      }
      const response = await axios.get<ScenarioDetailResponse>(`${API_URL}/scenarios/${filename}`);
      setError(null);
      return {
        content: response.data.content || '',
        metadata: response.data.metadata || null,
      };
    } catch (err: any) {
      console.error('Error fetching scenario content:', err);
      setError(err.response?.data?.detail || 'Senaryo içeriği alınırken bir hata oluştu');
      return { content: '', metadata: null };
    } finally {
      setLoading(false);
    }
  };

  const getScenarioContent = async (filename: string): Promise<string> => {
    const detail = await getScenarioDetail(filename);
    return detail.content;
  };

  const viewScenario = async (id: number | string) => {
    try {
      setLoading(true);
      const scenario = scenarios.find((s) => String(s.id) === String(id));
      if (!scenario) {
        throw new Error('Senaryo bulunamadı');
      }
      
      // İçeriği al
      const detail = await getScenarioDetail(scenario.filename || scenario.name);
      
      // selectedScenario'yu güncelle
      setSelectedScenario({
        ...scenario,
        content: detail.content,
        metadata: detail.metadata || scenario.metadata || null,
      });
      
      setError(null);
    } catch (err: any) {
      console.error('Error viewing scenario:', err);
      setError(err.response?.data?.detail || 'Senaryo görüntülenirken bir hata oluştu');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createScenario = async (data: any) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      await axios.post(`${API_URL}/scenarios`, data);
      await fetchScenarios();
      setError(null);
    } catch (err: any) {
      console.error('Error creating scenario:', err);
      setError(err.response?.data?.detail || 'Senaryo oluşturulurken bir hata oluştu');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateScenario = async (id: number | string, data: any) => {
    try {
      setLoading(true);
      if (IS_DEMO_MODE) {
        throw new Error(DEMO_MUTATION_MESSAGE);
      }
      await axios.put(`${API_URL}/scenarios/${id}`, data);
      await fetchScenarios();
      setError(null);
    } catch (err: any) {
      console.error('Error updating scenario:', err);
      setError(err.response?.data?.detail || 'Senaryo güncellenirken bir hata oluştu');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  return {
    scenarios,
    selectedScenario,
    loading,
    error,
    fetchScenarios,
    syncScenarios,
    uploadScenario,
    deleteScenario,
    getScenarioDetail,
    getScenarioContent,
    viewScenario,
    createScenario,
    updateScenario,
  };
};
