// src/components/stocks/StockPrediction.js - Fixed version
import React, { useState, useEffect } from 'react';
import { getStockPrediction } from '../../api/predictions';
import { getStockDetails } from '../../api/stocks';

const StockPrediction = ({ stockSymbol }) => {
  const [prediction, setPrediction] = useState(null);
  const [stockDetails, setStockDetails] = useState(null);
  const [timeframe, setTimeframe] = useState('1W');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  useEffect(() => {
    if (stockSymbol) {
      fetchPrediction();
      fetchStockDetails();
    }
  }, [stockSymbol, timeframe]);
  
  const fetchStockDetails = async () => {
    try {
      const data = await getStockDetails(stockSymbol);
      setStockDetails(data);
    } catch (error) {
      console.error('Error fetching stock details:', error);
    }
  };
  
  const fetchPrediction = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await getStockPrediction(stockSymbol, timeframe);
      setPrediction(data);
    } catch (error) {
      setError('Failed to fetch prediction');
      console.error('Error fetching prediction:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const timeframeOptions = [
    { value: '1D', label: '1 Day' },
    { value: '1W', label: '1 Week' },
    { value: '1M', label: '1 Month' },
    { value: '3M', label: '3 Months' },
  ];
  
  return (
    <div className="stock-prediction">
      <div className="timeframe-selector">
        {timeframeOptions.map(option => (
          <button
            key={option.value}
            className={`timeframe-btn ${timeframe === option.value ? 'active' : ''}`}
            onClick={() => setTimeframe(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
      
      {loading ? (
        <div className="loading">Loading prediction...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : prediction && stockDetails ? (
        <div className="prediction-result">
          <div className="prediction-header">
            <h4>Predicted Price ({timeframe})</h4>
            <span className="prediction-date">for {new Date(prediction.prediction_date).toLocaleDateString()}</span>
          </div>
          
          <div className="prediction-price">
            <span className="price-value">${prediction.predicted_price}</span>
            <span className="confidence">
              Confidence: {prediction.confidence_level}%
            </span>
          </div>
          
          <div className="prediction-diff">
            {prediction.predicted_price > stockDetails.last_price ? (
              <span className="positive">
                +${(prediction.predicted_price - stockDetails.last_price).toFixed(2)} 
                (+{((prediction.predicted_price / stockDetails.last_price - 1) * 100).toFixed(2)}%)
              </span>
            ) : (
              <span className="negative">
                -${(stockDetails.last_price - prediction.predicted_price).toFixed(2)} 
                (-{((1 - prediction.predicted_price / stockDetails.last_price) * 100).toFixed(2)}%)
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="no-prediction">No prediction available</div>
      )}
    </div>
  );
};

export default StockPrediction;