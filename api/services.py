import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import yfinance as yf

def get_stock_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5y")
        if len(df) < 60:
            return None
        info = stock.info
        return stock, df, info
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def run_forecast(df, live_sentiment=0.0, days=365):
    np.random.seed(42)

    df = df.copy()
    df['Volume'] = df['Volume'].fillna(df['Volume'].mean())
    df['Returns'] = df['Close'].pct_change()
    df['Sentiment'] = df['Returns'].rolling(5).mean() * 10
    df['Sentiment'] = df['Sentiment'].fillna(0).clip(-1, 1)

    if live_sentiment != 0.0:
        df.iloc[-1, df.columns.get_loc('Sentiment')] = live_sentiment
        
    # Create lag features for Random Forest
    for i in range(1, 6):
        df[f'Close_Lag_{i}'] = df['Close'].shift(i)
    
    df = df.dropna()

    features = ['Volume', 'Sentiment'] + [f'Close_Lag_{i}' for i in range(1, 6)]
    X = df[features].values
    y = df['Close'].values

    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

    model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=1)
    model.fit(X_scaled, y_scaled)

    # Feature Importance
    importances = model.feature_importances_
    # group lag features into 'Price'
    price_imp = sum(importances[2:])
    vol_imp = importances[0]
    sent_imp = importances[1]
    
    total = price_imp + vol_imp + sent_imp
    if total == 0:
        feature_importance = {'Price': 33.3, 'Volume': 33.3, 'Sentiment': 33.4}
    else:
        feature_importance = {
            'Price': round((price_imp / total) * 100, 1),
            'Volume': round((vol_imp / total) * 100, 1),
            'Sentiment': round((sent_imp / total) * 100, 1)
        }

    preds = []
    # Auto-regressive forecasting
    current_features = X[-1].copy()
    
    for _ in range(days):
        curr_scaled = scaler_X.transform([current_features])
        pred_scaled = model.predict(curr_scaled)[0]
        pred = scaler_y.inverse_transform([[pred_scaled]])[0][0]
        preds.append(pred)
        
        # Shift lags
        for i in range(4, 0, -1):
            current_features[2+i] = current_features[2+i-1] # Shift lags
        current_features[2] = pred # Close_Lag_1 becomes the new prediction
        
        # Keep volume/sentiment roughly constant or mean reverting
        current_features[0] = current_features[0] # Volume
        current_features[1] = current_features[1] * 0.95 # Decay sentiment

    current_price = float(df['Close'].iloc[-1])
    return np.array(preds), current_price, feature_importance


def calculate_ranges(current_price, preds):
    def r(p, margin):
        return {'low': float(p * (1 - margin)), 'high': float(p * (1 + margin)),
                'change': float((p - current_price) / current_price * 100), 'target': float(p)}

    return {
        'todayRange': r(preds[0], 0.015),
        'weekRange': r(preds[6] if len(preds) > 6 else preds[-1], 0.02),
        'monthRange': r(preds[29] if len(preds) > 29 else preds[-1], 0.03),
        'sixMonthRange': r(preds[179] if len(preds) > 179 else preds[-1], 0.08),
        'yearRange': r(preds[364] if len(preds) > 364 else preds[-1], 0.15),
    }

def get_feature_importance(model, current_batch, scaler):
    # This was a PyTorch specific function. 
    # It's now calculated directly in run_forecast for sklearn.
    pass

def run_backtest(df, days_back=30, forecast_window=30):
    if len(df) < 100 + days_back + forecast_window:
        return None
        
    np.random.seed(42)

    df = df.copy()
    df['Volume'] = df['Volume'].fillna(df['Volume'].mean())
    df['Returns'] = df['Close'].pct_change()
    df['Sentiment'] = df['Returns'].rolling(5).mean() * 10
    df['Sentiment'] = df['Sentiment'].fillna(0).clip(-1, 1)

    for i in range(1, 6):
        df[f'Close_Lag_{i}'] = df['Close'].shift(i)
    
    df = df.dropna()

    features = ['Volume', 'Sentiment'] + [f'Close_Lag_{i}' for i in range(1, 6)]
    X = df[features].values
    y = df['Close'].values

    # Split data at the backtest point
    cutoff_idx = len(X) - days_back
    X_train = X[:cutoff_idx]
    y_train = y[:cutoff_idx]
    
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_train_scaled = scaler_X.fit_transform(X_train)
    y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
    
    model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=1)
    model.fit(X_train_scaled, y_train_scaled)

    # Forecast
    current_features = X_train[-1].copy()
    preds = []
    
    for _ in range(forecast_window):
        curr_scaled = scaler_X.transform([current_features])
        pred_scaled = model.predict(curr_scaled)[0]
        pred = scaler_y.inverse_transform([[pred_scaled]])[0][0]
        preds.append(pred)
        
        # Shift lags
        for i in range(4, 0, -1):
            current_features[2+i] = current_features[2+i-1]
        current_features[2] = pred
        current_features[1] = current_features[1] * 0.95 
        
    actual_data = y[cutoff_idx:cutoff_idx + forecast_window]
    
    if len(actual_data) < forecast_window:
        preds = preds[:len(actual_data)]
    
    rmse = float(np.sqrt(np.mean((np.array(preds) - actual_data) ** 2)))
    mape = np.mean(np.abs((actual_data - np.array(preds)) / actual_data))
    accuracy = max(0.0, min(100.0, (1 - mape) * 100))
    
    dates = df.index[cutoff_idx:cutoff_idx + len(actual_data)].strftime('%Y-%m-%d').tolist()
    
    return {
        'dates': dates,
        'predicted': preds,
        'actual': actual_data.tolist(),
        'rmse': round(rmse, 2),
        'accuracy': round(accuracy, 1)
    }
