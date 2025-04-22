import React from 'react';

const PositionsList = ({ positions, onSelectStock }) => {
  const calculateTotalValue = (position) => {
    return position.quantity * position.stock.last_price;
  };
  
  const calculateProfitLoss = (position) => {
    const currentValue = position.quantity * position.stock.last_price;
    const costBasis = position.quantity * position.entry_price;
    return currentValue - costBasis;
  };
  
  const calculateProfitLossPercent = (position) => {
    const profitLoss = calculateProfitLoss(position);
    const costBasis = position.quantity * position.entry_price;
    return (profitLoss / costBasis) * 100;
  };
  
  return (
    <div className="positions-container">
      <h3>My Positions</h3>
      
      {positions.length === 0 ? (
        <p className="empty-positions">You don't have any open positions.</p>
      ) : (
        <div className="positions-table-container">
          <table className="positions-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Avg. Price</th>
                <th>Current</th>
                <th>Value</th>
                <th>P/L</th>
              </tr>
            </thead>
            <tbody>
              {positions.map(position => (
                <tr 
                  key={position.id} 
                  className="position-row"
                  onClick={() => onSelectStock(position.stock)}
                >
                  <td className="position-symbol">{position.stock.symbol}</td>
                  <td>{position.quantity}</td>
                  <td>${position.entry_price.toFixed(2)}</td>
                  <td>${position.stock.last_price.toFixed(2)}</td>
                  <td>${calculateTotalValue(position).toFixed(2)}</td>
                  <td className={`profit-loss ${calculateProfitLoss(position) >= 0 ? 'positive' : 'negative'}`}>
                    ${Math.abs(calculateProfitLoss(position)).toFixed(2)}
                    <span className="percent">
                      ({calculateProfitLossPercent(position) >= 0 ? '+' : '-'}
                      {Math.abs(calculateProfitLossPercent(position)).toFixed(2)}%)
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PositionsList;