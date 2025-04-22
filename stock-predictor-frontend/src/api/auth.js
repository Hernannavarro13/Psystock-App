import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with auth token
export const authApi = axios.create({
  baseURL: API_URL,
});

// Add auth token to requests
authApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh
authApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried to refresh the token yet
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        
        localStorage.setItem('accessToken', response.data.access);
        
        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        return authApi(originalRequest);
      } catch (refreshError) {
        // If refresh fails, logout user
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export const register = async (username, email, password) => {
  const response = await axios.post(`${API_URL}/auth/register/`, {
    username,
    email,
    password,
  });
  return response.data;
};

export const login = async (email, password) => {
  const response = await axios.post(`${API_URL}/auth/login/`, {
    email,
    password,
  });
  return response.data;
};

export const getProfile = async () => {
  const response = await authApi.get(`${API_URL}/auth/me/`);
  return response.data;
};