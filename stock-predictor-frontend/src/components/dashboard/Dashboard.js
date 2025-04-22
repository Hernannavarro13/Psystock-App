// src/components/dashboard/Dashboard.js
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getPortfolio } from '../../api/trading';
import { getWatchlist } from '../../api/watchlist';
import StockChart from '../charts/StockChart';
import WatchlistComponent from '../watchlist/Watchlist';
import PositionsList from '../trading/PositionsList';
import TradeForm from '../trading/TradeForm';
import StockSearch from '../stocks/StockSearch';
import StockPrediction from '../stocks/StockPrediction';

const Dashboard = () => {
  const { currentUser } = useAuth();
  const [portfolio, setPortfolio] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const portfolioData = await getPortfolio();
        const watchlistData = await getWatchlist();
        
        setPortfolio(portfolioData);
        setWatchlist(watchlistData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const handleStockSelect = (stock) => {
    setSelectedStock(stock);
  };
  
  const refreshData = async () => {
    try {
      const portfolioData = await getPortfolio();
      const watchlistData = await getWatchlist();
      
      setPortfolio(portfolioData);
      setWatchlist(watchlistData);
    } catch (error) {
      console.error('Error refreshing data:', error);
    }
  };
  
  if (loading) {
    return <div>Loading dashboard...</div>;
  }
  
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome, {currentUser.username}</h1>
        <div className="portfolio-summary">
          <div className="balance">
            <h3>Portfolio Balance</h3>
            <p className="balance-amount">${portfolio?.current_balance.toFixed(2)}</p>
          </div>
        </div>
      </div>
      
      <div className="dashboard-content">
        <div className="left-panel">
          <WatchlistComponent 
            watchlist={watchlist} 
            onSelectStock={handleStockSelect} 
            onUpdateWatchlist={refreshData} 
          />
          <PositionsList 
            positions={portfolio?.positions || []} 
            onSelectStock={handleStockSelect} 
          />
        </div>
        
        <div className="main-content">
          <StockSearch onSelectStock={handleStockSelect} />
          
          {selectedStock ? (
            <>
              <div className="stock-info-header">
                <h2>{selectedStock.name} ({selectedStock.symbol})</h2>
                <p className={`stock-price ${selectedStock.change_percent >= 0 ? 'positive' : 'negative'}`}>
                  ${selectedStock.last_price}
                  <span className="change-percent">
                    {selectedStock.change_percent >= 0 ? '+' : ''}{selectedStock.change_percent}%
                  </span>
                </p>
              </div>
              
              <StockChart stockSymbol={selectedStock.symbol} />
              
              <div className="trading-prediction-container">
                <div className="trading-panel">
                  <h3>Paper Trading</h3>
                  <TradeForm 
                    stock={selectedStock} 
                    availableBalance={portfolio?.current_balance || 0} 
                    onTradeComplete={refreshData}
                  />
                </div>
                
                <div className="prediction-panel">
                  <h3>Price Prediction</h3>
                  <StockPrediction stockSymbol={selectedStock.symbol} />
                </div>
              </div>
            </>
          ) : (
            <div className="no-stock-selected">
              <h2>Select a stock to view details</h2>
              <p>Use the search bar above or select from your watchlist</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;