export const getWatchlist = async () => {
    const response = await authApi.get(`${API_URL}/watchlist/`);
    return response.data;
  };
  
  export const addToWatchlist = async (stockId) => {
    const response = await authApi.post(`${API_URL}/watchlist/`, {
      stock: stockId,
    });
    return response.data;
  };
  
  export const removeFromWatchlist = async (watchlistItemId) => {
    const response = await authApi.delete(`${API_URL}/watchlist/${watchlistItemId}/`);
    return response.data;
  };