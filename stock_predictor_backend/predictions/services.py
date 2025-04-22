# stock_predictor_backend/predictions/services.py
import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from prophet import Prophet
from .models import StockPrediction

class PredictionService:
    def __init__(self):
        self.models_path = os.path.join(os.path.dirname(__file__), 'ml_models')
        # Ensure the model directory exists
        os.makedirs(self.models_path, exist_ok=True)
    
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
    
    def prepare_data_for_lstm(self, df, feature='Close', look_back=60):
        """Prepare data for LSTM model."""
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
        
        return X, y, scaler
    
    def train_lstm_model(self, ticker):
        """Train LSTM model for a specific ticker."""
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout
            
            # Get historical data
            df = self.get_stock_data(ticker)
            if df is None:
                return None
            
            # Prepare data
            X, y, scaler = self.prepare_data_for_lstm(df)
            
            # Split data into train and test sets
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Build LSTM model
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
            model.fit(X_train, y_train, batch_size=32, epochs=20, validation_data=(X_test, y_test), verbose=0)
            
            # Save model and scaler
            model_path = os.path.join(self.models_path, f"{ticker}_lstm_model.h5")
            scaler_path = os.path.join(self.models_path, f"{ticker}_scaler.pkl")
            
            model.save(model_path)
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            return model
            
        except Exception as e:
            print(f"Error training LSTM model for {ticker}: {e}")
            return None
    
    def predict_with_lstm(self, ticker, days=30):
        """Make predictions using LSTM model."""
        try:
            from tensorflow.keras.models import load_model
            
            model_path = os.path.join(self.models_path, f"{ticker}_lstm_model.h5")
            scaler_path = os.path.join(self.models_path, f"{ticker}_scaler.pkl")
            
            # Check if model exists, if not train it
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                print(f"Training new model for {ticker}")
                model = self.train_lstm_model(ticker)
                if model is None:
                    return None
            else:
                # Load model and scaler
                model = load_model(model_path)
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
            
            # Get most recent data for prediction
            df = self.get_stock_data(ticker, period='70d')  # Get enough days for lookback
            if df is None:
                return None
            
            # Prepare data
            data = df['Close'].values.reshape(-1, 1)
            scaled_data = scaler.transform(data)
            
            # Create prediction input (most recent 60 days)
            X_pred = []
            X_pred.append(scaled_data[-60:, 0])
            X_pred = np.array(X_pred)
            X_pred = np.reshape(X_pred, (X_pred.shape[0], X_pred.shape[1], 1))
            
            # Make predictions
            predictions = []
            last_sequence = X_pred[0].reshape(1, 60, 1)
            last_date = df['Date'].iloc[-1]
            
            for i in range(days):
                # Predict next value
                next_pred = model.predict(last_sequence)
                predictions.append(next_pred[0, 0])
                
                # Update sequence for next prediction
                last_sequence = np.append(last_sequence[:, 1:, :], next_pred.reshape(1, 1, 1), axis=1)
            
            # Inverse transform to get actual prices
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = scaler.inverse_transform(predictions)
            
            # Create DataFrame with dates and predictions
            pred_dates = [(last_date + timedelta(days=i+1)) for i in range(days)]
            predictions_df = pd.DataFrame({
                'Date': pred_dates,
                'Predicted_Close': predictions.flatten()
            })
            
            # Save predictions to database
            self._save_predictions(ticker, predictions_df)
            
            return predictions_df
            
        except Exception as e:
            print(f"Error predicting with LSTM for {ticker}: {e}")
            return None
    
    def predict_with_prophet(self, ticker, days=30):
        """Make predictions using Facebook Prophet."""
        try:
            # Get historical data
            df = self.get_stock_data(ticker)
            if df is None:
                return None
            
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            prophet_df = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
            
            # Initialize and fit Prophet model
            model = Prophet(daily_seasonality=True)
            model.fit(prophet_df)
            
            # Create future dataframe for prediction
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)
            
            # Extract prediction for future dates
            predictions_df = forecast[forecast['ds'] > prophet_df['ds'].max()][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
            predictions_df = predictions_df.rename(columns={
                'ds': 'Date', 
                'yhat': 'Predicted_Close',
                'yhat_lower': 'Lower_Bound',
                'yhat_upper': 'Upper_Bound'
            })
            
            # Save predictions to database
            self._save_predictions(ticker, predictions_df)
            
            # Save model
            model_path = os.path.join(self.models_path, f"{ticker}_prophet_model.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            return predictions_df
            
        except Exception as e:
            print(f"Error predicting with Prophet for {ticker}: {e}")
            return None
    
    def _save_predictions(self, ticker, predictions_df):
        """Save predictions to database."""
        try:
            # Delete old predictions for this ticker
            StockPrediction.objects.filter(ticker=ticker).delete()
            
            # Create new prediction records
            predictions = []
            for _, row in predictions_df.iterrows():
                prediction = StockPrediction(
                    ticker=ticker,
                    date=row['Date'],
                    predicted_price=row['Predicted_Close'],
                    lower_bound=row.get('Lower_Bound', None),
                    upper_bound=row.get('Upper_Bound', None)
                )
                predictions.append(prediction)
            
            # Bulk create predictions
            StockPrediction.objects.bulk_create(predictions)
            
        except Exception as e:
            print(f"Error saving predictions for {ticker}: {e}")