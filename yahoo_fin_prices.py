import yfinance as yf
import pandas as pd
import gspread
import json
import os
import time
from datetime import datetime

# Disable cache to avoid lock issues
yf.cache_dir = None

# Define tickers
tickers = ['^IXIC', '^GSPC', '^DJI', 'GC=F', '^TNX']

# Define date range
start_date = '2025-04-01'
end_date = datetime.today().strftime('%Y-%m-%d')

# Initialize combined DataFrame
combined_df = pd.DataFrame()

for ticker in tickers:
    try:
        print(f"Fetching {ticker}...")
        df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)['Close']
        df = df.rename(ticker)
        combined_df = pd.concat([combined_df, df], axis=1)
        time.sleep(2)  # pause between requests to avoid rate limit
    except Exception as e:
        print(f"❌ Failed to fetch {ticker}: {e}")

# Reset index to include dates as a column
combined_df.reset_index(inplace=True)
combined_df['Date'] = combined_df['Date'].astype(str)

# Load Google Sheets credentials
credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
if credentials_json is None:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not found")
credentials = json.loads(credentials_json)

# Authenticate with Google Sheets
gc = gspread.service_account_from_dict(credentials)

# Open Google Sheet
spreadsheet_name = 'labeled_data'    # <<< UPDATE IF NEEDED
worksheet_name = 'Sheet2'            # <<< UPDATE IF NEEDED
spreadsheet = gc.open(spreadsheet_name)
worksheet = spreadsheet.worksheet(worksheet_name)

# Clear worksheet before updating
worksheet.clear()

# Upload data (if any)
if not combined_df.empty:
    data_to_upload = [combined_df.columns.tolist()] + combined_df.values.tolist()
    worksheet.update(data_to_upload)
    print(f"✅ Uploaded {len(combined_df)} rows to Google Sheet '{spreadsheet_name}' → tab '{worksheet_name}'")
else:
    print("⚠ No data to upload — all ticker fetches failed or were empty.")
