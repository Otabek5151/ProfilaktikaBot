import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(credentials)

SPREADSHEET_ID = "1zZx1wvGn50nn4-yFiH0V-ix4DfQyghvP5Ew57M5VkaM"

spreadsheet = client.open_by_key(SPREADSHEET_ID)

print("Google Sheets bilan ulanish muvaffaqiyatli!")
print("Fayl nomi:", spreadsheet.title)

print("\nVaraqlar:")
for worksheet in spreadsheet.worksheets():
    print("-", worksheet.title)