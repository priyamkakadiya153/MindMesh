import axios from 'axios';
import { useAuthStore } from '../features/auth/auth-store';

const getApiBase = () => {
  const envUrl = (import.meta as any).env?.VITE_API_URL;
  if (!envUrl || envUrl === '/api/v1') return '/api/v1';
  const cleanUrl = envUrl.trim().replace(/\/+$/, '');
  return cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
};

const API_BASE = getApiBase();

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});


// Request interceptor to attach Bearer Token and X-Organization-ID
apiClient.interceptors.request.use(
  (config) => {
    const store = useAuthStore.getState();
    const token = store.token || localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (store.currentOrg?.id) {
      config.headers['X-Organization-ID'] = store.currentOrg.id;
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
      delete config.headers['content-type'];
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 and refresh tokens
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Prevent infinite loop if auth requests return 401
    const isAuthRoute = 
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/register') ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/firebase-login');

    if (error.response?.status === 401 && !isAuthRoute && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const store = useAuthStore.getState();
      const rToken = store.refreshToken || localStorage.getItem('refresh_token');

      try {
        // Call refresh endpoint
        const res = await axios.post(`${API_BASE}/auth/refresh`, 
          { refresh_token: rToken }, 
          { withCredentials: true }
        );
        
        const { access_token, refresh_token } = res.data;
        
        // Fetch current user details with the new token
        const meRes = await axios.get(`${API_BASE}/users/me`, {
          headers: { Authorization: `Bearer ${access_token}` }
        });
        
        store.setSession(access_token, refresh_token, meRes.data);
        
        processQueue(null, access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        isRefreshing = false;
        
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        
        // Refresh token invalid/revoked: logout
        store.clearSession();
        
        console.warn('Session has expired. Logging out.');
        return Promise.reject(new Error('Your session has expired. Please sign in again.'));
      }
    }
    
    return Promise.reject(error);
  }
);
