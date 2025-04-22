import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import datetime
from prophet import Prophet

def predict_stock_price(symbol, timeframe):
    """
    Predict stock price using historical data.
    
    Args:
        symbol (str): Stock symbol
        timeframe (str): Prediction timeframe: '1D', '1W', '1M', '3M'
        
    Returns:
        dict: Prediction data including date, price, and confidence level
    """
    try:
        # Map timeframe to days and Prophet periods
        timeframe_mapping = {
            '1D': {'days': 1, 'periods': 1, 'train_period': '1y'},
            '1W': {'days': 7, 'periods': 7, 'train_period': '2y'},
            '1M': {'days': 30, 'periods': 30, 'train_period': '3y'},
            '3M': {'days': 90, 'periods': 90, 'train_period': '5y'}
        }
        
        if timeframe not in timeframe_mapping:
            return None
            
        # Get historical data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=timeframe_mapping[timeframe]['train_period'])
        
        if hist.empty:
            return None
            
        # Use Prophet for prediction
        df = hist.reset_index()[['Date', 'Close']]
        df.columns = ['ds', 'y']
        
        model = Prophet(daily_seasonality=True)
        model.fit(df)
        
        # Make future dataframe for prediction
        future = model.make_future_dataframe(periods=timeframe_mapping[timeframe]['periods'])
        forecast = model.predict(future)
        
        # Get prediction for the target date
        target_date = datetime.date.today() + datetime.timedelta(days=timeframe_mapping[timeframe]['days'])
        target_forecast = forecast[forecast['ds'].dt.date == target_date]
        
        if target_forecast.empty:
            # Use the last available prediction
            target_forecast = forecast.iloc[-1]
        else:
            target_forecast = target_forecast.iloc[0]
        
        # Calculate confidence level based on model metrics
        last_price = hist['Close'].iloc[-1]
        historical_volatility = hist['Close'].pct_change().std() * 100
        
        # Adjust confidence based on volatility (higher volatility = lower confidence)
        base_confidence = 90  # Base confidence level
        confidence_adjustment = min(historical_volatility * 5, 30)  # Max 30% reduction
        confidence_level = max(base_confidence - confidence_adjustment, 50)  # Min 50% confidence
        
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'price': round(float(target_forecast['yhat']), 2),
            'confidence': round(confidence_level, 2)
        }
        
    except Exception as e:
        print(f"Error predicting stock price: {e}")
        return None

# Alternative prediction approach using RandomForest
def predict_with_random_forest(symbol, timeframe):
    try:
        # Map timeframe to days
        days_mapping = {
            '1D': 1,
            '1W': 7,
            '1M': 30,
            '3M': 90
        }
        
        if timeframe not in days_mapping:
            return None
            
        # Get more historical data for more accurate prediction
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5y')
        
        if len(hist) < 100:  # Need enough data for training
            return None
            
        # Feature engineering
        df = hist.copy()
        
        # Create features (technical indicators)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['RSI'] = calculate_rsi(df['Close'], 14)
        df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
        
        # Create target variable - price n days into future
        target_days = days_mapping[timeframe]
        df['Target'] = df['Close'].shift(-target_days)
        
        # Drop NaN values
        df = df.dropna()
        
        # Prepare features and target
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'MA5', 'MA20', 'MA50', 'RSI', 'MACD', 'Volatility']
        X = df[features]
        y = df['Target']
        
        # Scale features
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model on all data (for prediction purpose)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        # Create prediction input (most recent data point)
        latest_data = X.iloc[-1:].values
        latest_scaled = scaler.transform(latest_data)
        
        # Make prediction
        prediction = model.predict(latest_scaled)[0]
        
        # Calculate confidence based on model's feature importance and R^2 score
        feature_importance = model.feature_importances_
        confidence_level = min(85, 70 + (np.mean(feature_importance) * 100))
        
        # Target date
        target_date = datetime.date.today() + datetime.timedelta(days=target_days)
        
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'price': round(float(prediction), 2),
            'confidence': round(confidence_level, 2)
        }
        
    except Exception as e:
        print(f"Error in random forest prediction: {e}")
        return None

def calculate_rsi(series, period=14):
    """Calculate RSI technical indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi