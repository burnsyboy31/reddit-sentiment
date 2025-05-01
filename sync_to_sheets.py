import gspread
import pandas as pd
import json
import os

# Load Google service account credentials from environment variable
credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
if credentials_json is None:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not found")

credentials = json.loads(credentials_json)

# Authenticate with Google Sheets
gc = gspread.service_account_from_dict(credentials)

# Open the Google Sheet by name
# Make sure the service account has Editor access to this sheet!
spreadsheet_name = 'labeled_data'  # <<< REPLACE WITH YOUR SHEET NAME
worksheet_name = 'Sheet1'                 # <<< REPLACE WITH YOUR SHEET TAB NAME

spreadsheet = gc.open(spreadsheet_name)
worksheet = spreadsheet.worksheet(worksheet_name)

# Load full CSV data
csv_path = 'data/labeled_comments.csv'
df = pd.read_csv(csv_path)

# Convert DataFrame to list of lists (including headers)
data_to_upload = [df.columns.tolist()] + df.values.tolist()

# Clear the worksheet before uploading
worksheet.clear()

# Update worksheet with full data
worksheet.update(data_to_upload)

print(f"✅ Uploaded {len(df)} rows (plus header) to Google Sheet '{spreadsheet_name}' → tab '{worksheet_name}'")
