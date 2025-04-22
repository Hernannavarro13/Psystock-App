export const getStockPrediction = async (symbol, timeframe = '1W') => {
    const response = await authApi.get(`${API_URL}/predictions/predict/`, {
      params: { symbol, timeframe },
    });
    return response.data;
  };