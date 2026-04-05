const DEFAULT_DEV_API_URL = 'http://localhost:8000/api';
const DEFAULT_PROD_API_URL = '/api';
const runtimeHostname = typeof window !== 'undefined' ? window.location.hostname : '';
const hasExplicitApiUrl = Boolean(import.meta.env.VITE_API_URL?.trim());
const isGitHubPagesHost = runtimeHostname.endsWith('github.io');
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
export const IS_DEMO_MODE = import.meta.env.PROD && isGitHubPagesHost && !hasExplicitApiUrl;
