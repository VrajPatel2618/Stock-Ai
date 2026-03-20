import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf


class LSTMModel(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=32, output_dim=1, num_layers=1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])


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
    torch.manual_seed(42)
    np.random.seed(42)

    df = df.copy()
    df['Volume'] = df['Volume'].fillna(df['Volume'].mean())
    df['Returns'] = df['Close'].pct_change()
    df['Sentiment'] = df['Returns'].rolling(5).mean() * 10
    df['Sentiment'] = df['Sentiment'].fillna(0).clip(-1, 1)

    if live_sentiment != 0.0:
        df.iloc[-1, df.columns.get_loc('Sentiment')] = live_sentiment

    data = df[['Close', 'Volume', 'Sentiment']].values
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)

    prediction_days = 60
    train_slice = scaled[-500:] if len(scaled) > 500 else scaled
    x_train, y_train = [], []
    for i in range(prediction_days, len(train_slice)):
        x_train.append(train_slice[i - prediction_days:i])
        y_train.append(train_slice[i, 0])

    x_t = torch.tensor(np.array(x_train), dtype=torch.float32)
    y_t = torch.tensor(np.array(y_train), dtype=torch.float32)

    model = LSTMModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    model.train()
    for _ in range(60):
        out = model(x_t)
        loss = criterion(out, y_t.view(-1, 1))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    current_batch = torch.tensor(scaled[-prediction_days:].reshape(1, prediction_days, 3), dtype=torch.float32)
    preds = []
    for _ in range(days):
        with torch.no_grad():
            pred = model(current_batch).item()
            preds.append(pred)
            next_vol = current_batch[0, :, 1].mean().item()
            next_sent = current_batch[0, :, 2].mean().item() * 0.95
            new_val = torch.tensor([[[pred, next_vol, next_sent]]], dtype=torch.float32)
            current_batch = torch.cat((current_batch[:, 1:, :], new_val), dim=1)

    dummy = np.zeros((len(preds), 3))
    dummy[:, 0] = preds
    flat = scaler.inverse_transform(dummy)[:, 0]
    current_price = float(df['Close'].iloc[-1])
    return flat, current_price


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
