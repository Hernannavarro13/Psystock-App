import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from prophet import Prophet
import joblib
import os

class PredictionService:
    """Service for stock price predictions using various ML models"""
    
    def __init__(self):
        self.models_path = os.path.join(os.path.dirname(__file__), 'ml_models')
        os.makedirs(self.models_path, exist_ok=True)
        
    def get_stock_data(self, ticker, period='1y'):
        """Fetch historical stock data using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def prepare_data_for_linear_model(self, df):
        """Prepare data for linear regression model"""
        if df is None or df.empty:
            return None, None
        
        # Create features
        df['Date'] = df.index
        df['Day'] = df['Date'].dt.day
        df['Month'] = df['Date'].dt.month
        df['Year'] = df['Date'].dt.year
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        
        # Use last 30 days for prediction
        df_train = df[:-30].copy()
        df_test = df[-30:].copy()
        
        # Select features and target
        features = ['Day', 'Month', 'Year', 'DayOfWeek', 'Open', 'High', 'Low', 'Volume']
        X_train = df_train[features]
        y_train = df_train['Close']
        X_test = df_test[features]
        
        return X_train, y_train, X_test, df_test
    
    def linear_regression_prediction(self, ticker):
        """Linear regression model for stock prediction"""
        # Get data
        df = self.get_stock_data(ticker)
        if df is None or df.empty:
            return None
        
        # Prepare data
        X_train, y_train, X_test, df_test = self.prepare_data_for_linear_model(df)
        if X_train is None:
            return None
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Make predictions
        predictions = model.predict(X_test)
        
        # Save predictions
        result_df = df_test.copy()
        result_df['Predicted_Close'] = predictions
        
        # Save the model
        model_path = os.path.join(self.models_path, f"{ticker}_linear.joblib")
        joblib.dump(model, model_path)
        
        return {
            'ticker': ticker,
            'last_close': float(df['Close'].iloc[-1]),
            'dates': result_df.index.strftime('%Y-%m-%d').tolist(),
            'actual': result_df['Close'].tolist(),
            'predicted': result_df['Predicted_Close'].tolist(),
            'model_type': 'linear_regression'
        }
    
    def prophet_prediction(self, ticker, days_to_predict=30):
        """Prophet model for stock prediction"""
        # Get data
        df = self.get_stock_data(ticker)
        if df is None or df.empty:
            return None
        
        # Prepare data for Prophet
        prophet_df = df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
        
        # Train model
        model = Prophet(daily_seasonality=True)
        model.fit(prophet_df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=days_to_predict)
        forecast = model.predict(future)
        
        # Save the model
        model_path = os.path.join(self.models_path, f"{ticker}_prophet.joblib")
        model.serialize_model(model_path)
        
        # Get historical and predicted data
        historical = prophet_df.merge(
            forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], 
            on='ds', how='left'
        )
        
        future_predictions = forecast[forecast['ds'] > prophet_df['ds'].max()]
        
        return {
            'ticker': ticker,
            'last_close': float(df['Close'].iloc[-1]),
            'historical_dates': historical['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'historical_actual': historical['y'].tolist(),
            'historical_predicted': historical['yhat'].tolist(),
            'future_dates': future_predictions['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'future_predicted': future_predictions['yhat'].tolist(),
            'future_lower': future_predictions['yhat_lower'].tolist(),
            'future_upper': future_predictions['yhat_upper'].tolist(),
            'model_type': 'prophet'
        }
    
    def get_prediction(self, ticker, model_type='prophet'):
        """Get prediction based on model type"""
        if model_type == 'linear':
            return self.linear_regression_prediction(ticker)
        elif model_type == 'prophet':
            return self.prophet_prediction(ticker)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def get_model_performance(self, ticker, model_type='prophet'):
        """Calculate model performance metrics"""
        if model_type == 'linear':
            prediction_data = self.linear_regression_prediction(ticker)
            if prediction_data is None:
                return None
                
            actual = prediction_data['actual']
            predicted = prediction_data['predicted']
            
        elif model_type == 'prophet':
            prediction_data = self.prophet_prediction(ticker)
            if prediction_data is None:
                return None
                
            # Use historical data for evaluation
            actual = prediction_data['historical_actual']
            predicted = prediction_data['historical_predicted']
            
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Filter out None values
        valid_pairs = [(a, p) for a, p in zip(actual, predicted) if a is not None and p is not None]
        if not valid_pairs:
            return None
            
        actual_valid, predicted_valid = zip(*valid_pairs)
        
        # Calculate metrics
        mse = np.mean([(a - p) ** 2 for a, p in zip(actual_valid, predicted_valid)])
        rmse = np.sqrt(mse)
        mae = np.mean([abs(a - p) for a, p in zip(actual_valid, predicted_valid)])
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean([abs((a - p) / a) * 100 for a, p in zip(actual_valid, predicted_valid) if a != 0])
        
        return {
            'ticker': ticker,
            'model_type': model_type,
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'mape': mape
        }