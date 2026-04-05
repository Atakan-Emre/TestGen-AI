import { useState, useEffect } from 'react';
import { businessRuleService, BusinessRule, BusinessRuleCreate, BusinessRuleUpdate } from '../api/services/businessRules';
import { App } from 'antd';

export const useBusinessRules = () => {
  const { message } = App.useApp();
  const [rules, setRules] = useState<BusinessRule[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // İş kurallarını yükle
  const loadRules = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const response = await businessRuleService.getBusinessRules();
      setRules(response);
    } catch (err) {
      setError('İş kuralları yüklenemedi');
      message.error('İş kuralları yüklenemedi');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  // İş kuralı oluştur
  const createRule = async (rule: BusinessRuleCreate) => {
    try {
      setLoading(true);
      setError(null);
      const newRule = await businessRuleService.createBusinessRule(rule);
      setRules(prev => [newRule, ...prev]);
      message.success('İş kuralı başarıyla oluşturuldu');
      return newRule;
    } catch (err) {
      setError('İş kuralı oluşturulamadı');
      message.error('İş kuralı oluşturulamadı');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // İş kuralını güncelle
  const updateRule = async (id: number, rule: BusinessRuleUpdate) => {
    try {
      setLoading(true);
      setError(null);
      const updatedRule = await businessRuleService.updateBusinessRule(id, rule);
      setRules(prev => prev.map(r => r.id === id ? updatedRule : r));
      message.success('İş kuralı başarıyla güncellendi');
      return updatedRule;
    } catch (err) {
      setError('İş kuralı güncellenemedi');
      message.error('İş kuralı güncellenemedi');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // İş kuralını sil
  const deleteRule = async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      await businessRuleService.deleteBusinessRule(id);
      setRules(prev => prev.filter(r => r.id !== id));
      message.success('İş kuralı başarıyla silindi');
    } catch (err) {
      setError('İş kuralı silinemedi');
      message.error('İş kuralı silinemedi');
    } finally {
      setLoading(false);
    }
  };

  // Tüm iş kurallarını sil
  const deleteAllRules = async () => {
    try {
      setLoading(true);
      setError(null);
      await businessRuleService.deleteAllBusinessRules();
      setRules([]);
      message.success('Tüm iş kuralları başarıyla silindi');
    } catch (err) {
      setError('İş kuralları silinemedi');
      message.error('İş kuralları silinemedi');
    } finally {
      setLoading(false);
    }
  };

  // Dosya yönetimi fonksiyonları
  const loadFiles = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const response = await businessRuleService.getBusinessRuleFiles();
      setFiles(response.files);
    } catch (err) {
      setError('Dosyalar yüklenemedi');
      message.error('Dosyalar yüklenemedi');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const getFileContent = async (filename: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await businessRuleService.getBusinessRuleFileContent(filename);
      return response;
    } catch (err) {
      setError('Dosya içeriği alınamadı');
      message.error('Dosya içeriği alınamadı');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteFile = async (filename: string) => {
    try {
      setLoading(true);
      setError(null);
      await businessRuleService.deleteBusinessRuleFile(filename);
      message.success('Dosya başarıyla silindi');
      await loadFiles(false);
    } catch (err) {
      setError('Dosya silinemedi');
      message.error('Dosya silinemedi');
    } finally {
      setLoading(false);
    }
  };

  const renameFile = async (filename: string, newName: string) => {
    try {
      setLoading(true);
      setError(null);
      await businessRuleService.renameBusinessRuleFile(filename, newName);
      message.success('Dosya adı başarıyla değiştirildi');
      await loadFiles(false);
    } catch (err) {
      setError('Dosya adı değiştirilemedi');
      message.error('Dosya adı değiştirilemedi');
    } finally {
      setLoading(false);
    }
  };

  const deleteAllFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      await businessRuleService.deleteAllBusinessRuleFiles();
      setFiles([]);
      message.success('Tüm dosyalar başarıyla silindi');
    } catch (err) {
      setError('Dosyalar silinemedi');
      message.error('Dosyalar silinemedi');
    } finally {
      setLoading(false);
    }
  };

  // Tarihi formatla
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('tr-TR');
  };

  // Dosya boyutunu formatla
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  useEffect(() => {
    loadRules();
    loadFiles();
  }, []);

  return {
    rules,
    files,
    loading,
    error,
    loadRules,
    loadFiles,
    createRule,
    updateRule,
    deleteRule,
    deleteAllRules,
    getFileContent,
    deleteFile,
    renameFile,
    deleteAllFiles,
    formatDate,
    formatFileSize
  };
};
