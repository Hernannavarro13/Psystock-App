export const getPortfolio = async () => {
    const response = await authApi.get(`${API_URL}/trading/portfolio/`);
    return response.data;
  };
  
  export const getPositions = async () => {
    const response = await authApi.get(`${API_URL}/trading/positions/`);
    return response.data;
  };
  
  export const getTrades = async () => {
    const response = await authApi.get(`${API_URL}/trading/trades/`);
    return response.data;
  };
  
  export const executeTrade = async (tradeData) => {
    const response = await authApi.post(`${API_URL}/trading/trades/`, tradeData);
    return response.data;
  };