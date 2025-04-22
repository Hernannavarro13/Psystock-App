export const searchStocks = async (query) => {
    const response = await authApi.get(`${API_URL}/stocks/search/`, {
      params: { q: query },
    });
    return response.data;
  };
  
  export const getStockDetails = async (symbol) => {
    const response = await authApi.get(`${API_URL}/stocks/${symbol}/`);
    return response.data;
  };
  
  export const getStockHistory = async (symbol, period = '1y') => {
    const response = await authApi.get(`${API_URL}/stocks/${symbol}/history/`, {
      params: { period },
    });
    return response.data;
  };