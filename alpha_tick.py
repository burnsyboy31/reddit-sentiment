import requests
import pandas as pd
import gspread
import json
import os
import time
from datetime import datetime

API_KEY = os.getenv('ALPHA_API_KEY')  # <<< Replace with your key

# Define symbols and Alpha Vantage types
symbols = {
    'SPY': 'TIME_SERIES_DAILY',    # S&P 500 ETF
    'DIA': 'TIME_SERIES_DAILY',    # Dow ETF
    'QQQ': 'TIME_SERIES_DAILY',    # Nasdaq ETF
    'XAUUSD': 'FX_DAILY',          # Gold spot
    'IEF': 'TIME_SERIES_DAILY'     # 7–10Y Treasury ETF
}

# Fetch data
all_data = {}

for symbol, function in symbols.items():
    print(f"Fetching {symbol}...")
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY}&outputsize=full'
    response = requests.get(url)
    time.sleep(12)  # Respect free tier limits

    if response.status_code == 200:
        data = response.json()
        print(data)
        if function == 'FX_DAILY':
            timeseries = data.get('Time Series FX (Daily)', {})
        else:
            timeseries = data.get('Time Series (Daily)', {})
        
        df = pd.DataFrame.from_dict(timeseries, orient='index')
        df = df.rename(columns={
            '1. open': 'Open',
            '4. close': 'Close'
        })
        df = df[['Open', 'Close']].astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        all_data[symbol] = df
    else:
        print(f"❌ Failed to fetch {symbol}")

# Combine all into full calendar DataFrame
combined_df = pd.DataFrame(index=pd.date_range(start='2025-04-01', end=pd.Timestamp.today(), freq='D'))

for symbol, df in all_data.items():
    combined_df[f'{symbol}_Open'] = df['Open']
    combined_df[f'{symbol}_Close'] = df['Close']

# Forward-fill weekends
combined_df.ffill(inplace=True)
combined_df.reset_index(inplace=True)
combined_df.rename(columns={'index': 'Date'}, inplace=True)
combined_df['Date'] = combined_df['Date'].astype(str)

# Load Google Sheets credentials
credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
if credentials_json is None:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not found")

credentials = json.loads(credentials_json)
gc = gspread.service_account_from_dict(credentials)

# Open target Google Sheet
spreadsheet_name = 'labeled_data'  # <<< UPDATE
worksheet_name = 'Sheet2'                         # <<< UPDATE
spreadsheet = gc.open(spreadsheet_name)
worksheet = spreadsheet.worksheet(worksheet_name)

# Clear and update sheet
worksheet.clear()
worksheet.update([combined_df.columns.tolist()] + combined_df.values.tolist())

print(f"✅ Uploaded {len(combined_df)} rows to Google Sheet '{spreadsheet_name}' → tab '{worksheet_name}'")
