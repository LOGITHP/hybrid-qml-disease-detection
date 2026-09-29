/// <reference types="vite/client" />
import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('hybrid_qml_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to format errors and handle 401s
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string | { message?: string; code?: string }; message?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('hybrid_qml_token');
      localStorage.removeItem('hybrid_qml_user');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }

    let errorMessage = 'An unexpected network error occurred. Please verify backend connectivity.';
    
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        errorMessage = error.response.data.detail.map((err: any) => `${err.loc?.join('.')} ${err.msg}`).join(', ');
      } else if (typeof error.response.data.detail === 'string') {
        errorMessage = error.response.data.detail;
      } else if (typeof error.response.data.detail === 'object' && error.response.data.detail.message) {
        errorMessage = error.response.data.detail.message;
      }
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }

    return Promise.reject(new Error(errorMessage));
  }
);
