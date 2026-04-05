const DEFAULT_DEV_API_URL = 'http://localhost:8000/api';
const DEFAULT_PROD_API_URL = '/api';
const rawApiUrl =
  import.meta.env.VITE_API_URL?.trim() ||
  (import.meta.env.DEV ? DEFAULT_DEV_API_URL : DEFAULT_PROD_API_URL);
const trimmedApiUrl = rawApiUrl.endsWith('/')
  ? rawApiUrl.slice(0, -1)
  : rawApiUrl;

export const API_URL = trimmedApiUrl.endsWith('/api')
  ? trimmedApiUrl
  : `${trimmedApiUrl}/api`;

export const API_ORIGIN = API_URL.replace(/\/api$/, '');
