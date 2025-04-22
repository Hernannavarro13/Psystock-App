import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { getStockHistory } from '../../api/stocks';
import 'chart.js/auto';

const StockChart = ({ stockSymbol }) => {
  const [chartData, setChartData] = useState(null);
  const [period, setPeriod] = useState('1m');
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (stockSymbol) {
      fetchChartData();
    }
  }, [stockSymbol, period]);
  
  const fetchChartData = async () => {
    setLoading(true);
    try {
      const data = await getStockHistory(stockSymbol, period);
      
      // Format data for Chart.js
      const labels = data.map(item => new Date(item.date).toLocaleDateString());
      const prices = data.map(item => item.close);
      
      setChartData({
        labels,
        datasets: [
          {
            label: stockSymbol,
            data: prices,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
            pointRadius: 0,
            pointHitRadius: 10,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: 'rgb(75, 192, 192)',
          },
        ],
      });
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const periodOptions = [
    { value: '1m', label: '1M' },
    { value: '3m', label: '3M' },
    { value: '6m', label: '6M' },
    { value: '1y', label: '1Y' },
    { value: '5y', label: '5Y' },
  ];
  
  return (
    <div className="stock-chart">
      <div className="period-selector">
        {periodOptions.map(option => (
          <button
            key={option.value}
            className={`period-btn ${period === option.value ? 'active' : ''}`}
            onClick={() => setPeriod(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
      
      {loading ? (
        <div className="chart-loading">Loading chart...</div>
      ) : chartData ? (
        <div className="chart-container">
          <Line
            data={chartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: false,
                },
                tooltip: {
                  mode: 'index',
                  intersect: false,
                  callbacks: {
                    label: function(context) {
                      return `$${context.raw.toFixed(2)}`;
                    }
                  }
                },
              },
              scales: {
                x: {
                  grid: {
                    display: false,
                  },
                  ticks: {
                    maxTicksLimit: 10,
                  }
                },
                y: {
                  ticks: {
                    callback: function(value) {
                      return '$' + value.toFixed(2);
                    }
                  }
                }
              },
              interaction: {
                intersect: false,
                mode: 'index',
              },
            }}
            height={300}
          />
        </div>
      ) : (
        <div className="no-chart-data">No chart data available</div>
      )}
    </div>
  );
};

export default StockChart;