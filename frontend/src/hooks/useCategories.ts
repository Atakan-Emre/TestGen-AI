import { useState, useEffect } from 'react';
import { categoryService } from '../api/services/category';
import type { Category, CategoryCreate, CategoryUpdate } from '../api/types';

export const useCategories = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await categoryService.getCategories();
      setCategories(response.data || []);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching categories:', err);
      setError(err.response?.data?.detail || 'Kategoriler yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const createCategory = async (data: CategoryCreate): Promise<Category | null> => {
    try {
      setLoading(true);
      const category = await categoryService.createCategory(data);
      await fetchCategories();
      setError(null);
      return category;
    } catch (err: any) {
      console.error('Error creating category:', err);
      setError(err.response?.data?.detail || 'Kategori oluşturulurken bir hata oluştu');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const updateCategory = async (id: number, data: CategoryUpdate): Promise<Category | null> => {
    try {
      setLoading(true);
      const category = await categoryService.updateCategory(id, data);
      await fetchCategories();
      setError(null);
      return category;
    } catch (err: any) {
      console.error('Error updating category:', err);
      setError(err.response?.data?.detail || 'Kategori güncellenirken bir hata oluştu');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const deleteCategory = async (id: number): Promise<boolean> => {
    try {
      setLoading(true);
      await categoryService.deleteCategory(id);
      await fetchCategories();
      setError(null);
      return true;
    } catch (err: any) {
      console.error('Error deleting category:', err);
      setError(err.response?.data?.detail || 'Kategori silinirken bir hata oluştu');
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  return {
    categories,
    loading,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  };
};
