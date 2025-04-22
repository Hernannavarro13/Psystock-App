import React, { useState } from 'react';
import { searchStocks } from '../../api/stocks';
import { addToWatchlist } from '../../api/watchlist';

const StockSearch = ({ onSelectStock }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  
  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const data = await searchStocks(query);
      setResults(data);
      setShowResults(true);
    } catch (error) {
      console.error('Error searching stocks:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSelectStock = (stock) => {
    onSelectStock(stock);
    setShowResults(false);
    setQuery('');
  };
  
  const handleAddToWatchlist = async (e, stockId) => {
    e.stopPropagation();
    
    try {
      await addToWatchlist(stockId);
      // Show success indicator
      const updatedResults = results.map(stock => 
        stock.id === stockId ? { ...stock, addedToWatchlist: true } : stock
      );
      setResults(updatedResults);
      
      // Reset indicator after 2 seconds
      setTimeout(() => {
        const resetResults = results.map(stock => 
          stock.id === stockId ? { ...stock, addedToWatchlist: false } : stock
        );
        setResults(resetResults);
      }, 2000);
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };
  
  return (
    <div className="stock-search">
      <form onSubmit={handleSearch}>
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search stocks by symbol or name..."
            className="search-input"
          />
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>
      
      {showResults && (
        <div className="search-results">
          {results.length === 0 ? (
            <p className="no-results">No stocks found</p>
          ) : (
            <ul className="results-list">
              {results.map(stock => (
                <li 
                  key={stock.id} 
                  className="result-item"
                  onClick={() => handleSelectStock(stock)}
                >
                  <div className="result-info">
                    <span className="result-symbol">{stock.symbol}</span>
                    <span className="result-name">{stock.name}</span>
                  </div>
                  <div className="result-actions">
                    <button
                      className={`watchlist-btn ${stock.addedToWatchlist ? 'added' : ''}`}
                      onClick={(e) => handleAddToWatchlist(e, stock.id)}
                    >
                      {stock.addedToWatchlist ? 'Added ✓' : '+ Watchlist'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default StockSearch;