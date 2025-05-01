import yfinance as yf
import pandas as pd
import gspread
import json
import os
from datetime import datetime

# Disable yfinance cache to avoid lock issues
yf.cache_dir = None

# Define tickers
tickers = ['^IXIC', '^GSPC', '^DJI', 'GC=F', '^TNX']

# Define date range: April 1, 2025 to today
start_date = '2025-04-11'
end_date = datetime.today().strftime('%Y-%m-%d')

# Download daily price data
data = yf.download(tickers, start=start_date, end=end_date, interval='1d')

# Keep only closing prices
close_prices = data['Close']

# Convert index to string (dates) for Google Sheets compatibility
close_prices.reset_index(inplace=True)
close_prices['Date'] = close_prices['Date'].astype(str)

# Load Google Sheets credentials
credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
if credentials_json is None:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not found")
credentials = json.loads(credentials_json)

# Authenticate with Google Sheets
gc = gspread.service_account_from_dict(credentials)

# Open Google Sheet
spreadsheet_name = 'Your Sheet Name Here'   # <<< CHANGE THIS
worksheet_name = 'Sheet2'                   # <<< CHANGE THIS
spreadsheet = gc.open(spreadsheet_name)
worksheet = spreadsheet.worksheet(worksheet_name)

# Clear worksheet before updating
worksheet.clear()

# Prepare data for upload (header + rows)
data_to_upload = [close_prices.columns.tolist()] + close_prices.values.tolist()

# Update Google Sheet
worksheet.update(data_to_upload)

print(f"✅ Uploaded {len(close_prices)} rows to Google Sheet '{spreadsheet_name}' → tab '{worksheet_name}'")
