import axios from 'axios';
import { API_URL } from '../config';

/**
 * Ortak axios instance'ı.
 * Eski kod `client` adını beklediği için geriye dönük uyumluluk sağlıyoruz.
 */
export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Legacy isim kullanan modüller için alias bırakıyoruz.
export const client = apiClient;

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
