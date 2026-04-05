import { apiClient } from '../client';
import { Category, CategoryCreate, CategoryUpdate } from '../types';

export const categoryService = {
  getCategories: () => apiClient.get('/categories'),
  createCategory: async (data: CategoryCreate): Promise<Category> => {
    const response = await apiClient.post('/categories', data);
    return response.data;
  },
  updateCategory: async (id: number, data: CategoryUpdate): Promise<Category> => {
    const response = await apiClient.put(`/categories/${id}`, data);
    return response.data;
  },
  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`);
  }
};