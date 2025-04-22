// stock-predictor-frontend/src/services/api.js
import axios from 'axios';

// Create axios instance with base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for token refresh
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is 401 and not already retrying
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          // No refresh token, logout user
          authService.logout();
          return Promise.reject(error);
        }
        
        const response = await axios.post(`${API_URL}/token/refresh/`, {
          refresh: refreshToken
        });
        
        const { access } = response.data;
        
        // Save the new access token
        localStorage.setItem('access_token', access);
        
        // Update the original request with the new token
        originalRequest.headers['Authorization'] = `Bearer ${access}`;
        
        // Retry the original request
        return api(originalRequest);
      } catch (err) {
        // If refresh token is expired or invalid, logout user
        authService.logout();
        return Promise.reject(err);
      }
    }
    
    return Promise.reject(error);
  }
);

// Authentication service
const authService = {
  login: async (email, password) => {
    const response = await api.post('/token/', { email, password });
    const { access, refresh, user } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(user));
    
    return user;
  },
  
  register: async (userData) => {
    const response = await api.post('/accounts/register/', userData);
    const { access, refresh, user } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(user));
    
    return user;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  },
  
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      return JSON.parse(userStr);
    }
    return null;
  },
  
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
  
  updateProfile: async (userData) => {
    const response = await api.put('/accounts/profile/', userData);
    const updatedUser = response.data;
    localStorage.setItem('user', JSON.stringify(updatedUser));
    return updatedUser;
  },
  
  resetPasswordRequest: async (email) => {
    return await api.post('/accounts/reset-password/', { email });
  },
  
  resetPasswordConfirm: async (uid, token, password) => {
    return await api.post('/accounts/reset-password-confirm/', { uid, token, password });
  },
};

// Stocks service
const stocksService = {
  getStocks: async (query = '', page = 1) => {
    const response = await api.get('/stocks/', { 
      params: { 
        search: query,
        page
      } 
    });
    return response.data;
  },
  
  getStockDetail: async (ticker) => {
    const response = await api.get(`/stocks/${ticker}/`);
    return response.data;
  },
  
  getStockHistory: async (ticker, period = '1y') => {
    const response = await api.get(`/stocks/${ticker}/history/`, {
      params: { period }
    });
    return response.data;
  },
  
  searchStocks: async (query) => {
    const response = await api.get('/stocks/search/', {
      params: { query }
    });
    return response.data;
  },
};

// Predictions service
const predictionsService = {
  getPrediction: async (ticker, model = 'lstm', days = 30) => {
    const response = await api.get(`/predictions/${ticker}/`, {
      params: { model, days }
    });
    return response.data;
  },
  
  getAvailableModels: async () => {
    const response = await api.get('/predictions/models/');
    return response.data;
  },
};

// Trading service
const tradingService = {
  getPortfolio: async () => {
    const response = await api.get('/trading/portfolio/');
    return response.data;
  },
  
  getPositions: async () => {
    const response = await api.get('/trading/positions/');
    return response.data;
  },
  
  getTransactions: async (page = 1) => {
    const response = await api.get('/trading/transactions/', {
      params: { page }
    });
    return response.data;
  },
  
  executeMarketOrder: async (ticker, side, quantity) => {
    const response = await api.post('/trading/orders/market/', {
      ticker,
      side,
      quantity
    });
    return response.data;
  },
  
  placeLimitOrder: async (ticker, side, quantity, limitPrice, expirationDays = 30) => {
    const response = await api.post('/trading/orders/limit/', {
      ticker,
      side,
      quantity,
      limit_price: limitPrice,
      expiration_days: expirationDays
    });
    return response.data;
  },
  
  getOrders: async (status = '', page = 1) => {
    const response = await api.get('/trading/orders/', {
      params: { status, page }
    });
    return response.data;
  },
  
  cancelOrder: async (orderId) => {
    const response = await api.post(`/trading/orders/${orderId}/cancel/`);
    return response.data;
  },
};

// Watchlist service
const watchlistService = {
  getWatchlist: async () => {
    const response = await api.get('/watchlist/');
    return response.data;
  },
  
  addToWatchlist: async (ticker) => {
    const response = await api.post('/watchlist/add/', { ticker });
    return response.data;
  },
  
  removeFromWatchlist: async (watchlistItemId) => {
    const response = await api.delete(`/watchlist/${watchlistItemId}/`);
    return response.data;
  },
};

export {
  api,
  authService,
  stocksService,
  predictionsService,
  tradingService,
  watchlistService
};