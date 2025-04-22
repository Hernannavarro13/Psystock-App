# stock_predictor_backend/predictions/ml_models/model_trainer.py
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from prophet import Prophet
import pickle
import matplotlib.pyplot as plt
import yfinance as yf

class ModelTrainer:
    """Class for training stock prediction models."""
    
    def __init__(self, save_path=None):
        """Initialize the model trainer."""
        if save_path is None:
            self.save_path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.save_path = save_path
        
        # Create directory if it doesn't exist
        os.makedirs(self.save_path, exist_ok=True)
    
    def get_stock_data(self, ticker, period='2y'):
        """Fetch historical stock data from Yahoo Finance."""
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            # Reset index to have date as a column
            df = df.reset_index()
            
            # Format date and select required columns
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def train_lstm_model(self, ticker, feature='Close', look_back=60, epochs=50, batch_size=32):
        """Train an LSTM model for stock price prediction."""
        try:
            # Get historical data
            df = self.get_stock_data(ticker)
            if df is None or len(df) < look_back + 30:  # Ensure enough data
                print(f"Not enough data for {ticker}")
                return None
            
            # Select the feature to predict
            data = df[feature].values.reshape(-1, 1)
            
            # Normalize the data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)
            
            # Create dataset with lookback window
            X = []
            y = []
            
            for i in range(look_back, len(scaled_data)):
                X.append(scaled_data[i-look_back:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            
            # Reshape for LSTM [samples, time steps, features]
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))
            
            # Split data into train and test sets
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Create LSTM model
            model = Sequential()
            model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
            model.add(Dropout(0.2))
            model.add(LSTM(units=50, return_sequences=False))
            model.add(Dropout(0.2))
            model.add(Dense(units=25))
            model.add(Dense(units=1))
            
            # Compile model
            model.compile(optimizer='adam', loss='mean_squared_error')
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_test, y_test),
                verbose=1
            )
            
            # Plot training history
            plt.figure(figsize=(10, 6))
            plt.plot(history.history['loss'], label='Train Loss')
            plt.plot(history.history['val_loss'], label='Validation Loss')
            plt.title(f'LSTM Model Loss for {ticker}')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.legend()
            plt.savefig(os.path.join(self.save_path, f"{ticker}_lstm_training.png"))
            
            # Save model and scaler
            model_path = os.path.join(self.save_path, f"{ticker}_lstm_model.h5")
            scaler_path = os.path.join(self.save_path, f"{ticker}_scaler.pkl")
            
            model.save(model_path)
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            print(f"LSTM model for {ticker} saved to {model_path}")
            return model, scaler
            
        except Exception as e:
            print(f"Error training LSTM model for {ticker}: {e}")
            return None
    
    def train_prophet_model(self, ticker):
        """Train a Prophet model for stock price prediction."""
        try:
            # Get historical data
            df = self.get_stock_data(ticker)
            if df is None:
                return None
            
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            prophet_df = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
            
            # Initialize and fit Prophet model
            model = Prophet(daily_seasonality=True, yearly_seasonality=True, weekly_seasonality=True)
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            model.fit(prophet_df)
            
            # Create future dataframe for visualization
            future = model.make_future_dataframe(periods=60)
            forecast = model.predict(future)
            
            # Plot forecast
            fig = model.plot(forecast)
            fig.savefig(os.path.join(self.save_path, f"{ticker}_prophet_forecast.png"))
            
            # Plot components
            fig_components = model.plot_components(forecast)
            fig_components.savefig(os.path.join(self.save_path, f"{ticker}_prophet_components.png"))
            
            # Save model
            model_path = os.path.join(self.save_path, f"{ticker}_prophet_model.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            print(f"Prophet model for {ticker} saved to {model_path}")
            return model
            
        except Exception as e:
            print(f"Error training Prophet model for {ticker}: {e}")
            return None

if __name__ == "__main__":
    # Example usage
    trainer = ModelTrainer()
    
    # Train models for popular stocks
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    
    for ticker in tickers:
        print(f"\nTraining models for {ticker}...")
        # Train LSTM model
        trainer.train_lstm_model(ticker)
        
        # Train Prophet model
        trainer.train_prophet_model(ticker)