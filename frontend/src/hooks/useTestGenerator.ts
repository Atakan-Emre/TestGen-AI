import { useState, useEffect } from 'react';
import axios from 'axios';
import { App } from 'antd';
import { API_URL } from '../config';
import {
  buildTestPayload,
  normalizeGeneratorResult,
  type GeneratorRunResult,
  type TestGeneratorRequest,
} from './testGenerator.utils';

export const useTestGenerator = () => {
  const { message } = App.useApp();
  const [variablesFiles, setVariablesFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingOperation, setLoadingOperation] = useState<'idle' | 'variables' | 'generation'>('idle');
  const [error, setError] = useState<string | null>(null);

  // Variables dosyalarını yükle
  const loadVariablesFiles = async () => {
    try {
      setLoading(true);
      setLoadingOperation('variables');
      setError(null);
      const response = await axios.get(`${API_URL}/files/variables`);
      setVariablesFiles(response.data.files || []);
    } catch (err) {
      setError('Variables dosyaları yüklenemedi');
      message.error('Variables dosyaları yüklenemedi');
    } finally {
      setLoading(false);
      setLoadingOperation('idle');
    }
  };

  // Test oluştur
  const runGenerator = async (
    generatorType: string,
    request: TestGeneratorRequest
  ): Promise<GeneratorRunResult> => {
    const endpoint = `${API_URL}/tests/${generatorType}/generate`;
    const payload = buildTestPayload(generatorType, request);
    const response = await axios.post(endpoint, payload);
    return normalizeGeneratorResult(generatorType, response.data, request.selected_variables);
  };

  const generateTest = async (request: TestGeneratorRequest) => {
    try {
      setLoading(true);
      setLoadingOperation('generation');
      setError(null);
      const result = await runGenerator(request.test_type, request);
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Test oluşturulamadı';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
      setLoadingOperation('idle');
    }
  };

  const generateTestsInParallel = async (
    request: TestGeneratorRequest,
    generatorTypes: string[]
  ) => {
    try {
      setLoading(true);
      setLoadingOperation('generation');
      setError(null);
      const settled = await Promise.all(
        generatorTypes.map(async (generatorType) => {
          try {
            return await runGenerator(generatorType, request);
          } catch (err: any) {
            const errorMessage =
              err.response?.data?.detail || err.message || 'Test oluşturulamadı';
            return {
              type: generatorType,
              success: false,
              message: errorMessage,
              error: errorMessage,
              generated_cases: [],
              generated_count: 0,
            } as GeneratorRunResult;
          }
        })
      );
      return settled;
    } catch (err) {
      setError('Test oluşturulamadı');
      throw err;
    } finally {
      setLoading(false);
      setLoadingOperation('idle');
    }
  };

  useEffect(() => {
    loadVariablesFiles();
  }, []);

  return {
    variablesFiles,
    loading,
    loadingOperation,
    isVariablesLoading: loadingOperation === 'variables',
    isGenerating: loadingOperation === 'generation',
    error,
    loadVariablesFiles,
    generateTest,
    generateTestsInParallel
  };
};
