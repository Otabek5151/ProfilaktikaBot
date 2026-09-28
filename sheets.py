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

bazalar_sheet = spreadsheet.worksheet("Bazalar")


def get_base_by_id(base_id: str):
    """
    Baza ID orqali Bazalar varag‘idan
    baza nomini topadi.
    """

    base_id = str(base_id).strip().upper()

    records = bazalar_sheet.get_all_records()

    for row in records:
        row_id = str(row.get("ID", "")).strip().upper()

        if row_id == base_id:
            faol = str(row.get("Faol", "")).strip().lower()

            if faol not in ["ha", "true", "1", "active"]:
                return None

            return {
                "id": row_id,
                "name": str(row.get("Baza nomi", "")).strip(),
            }

    return None

xodimlar_sheet = spreadsheet.worksheet("Xodimlar")


def get_active_employees():
    """
    Faol xodimlar ro‘yxatini qaytaradi.
    """

    records = xodimlar_sheet.get_all_records()

    employees = []

    for row in records:
        status = str(row.get("Status", "")).strip().lower()

        if status == "faol":
            employees.append({
                "telegram_id": str(row.get("Telegram ID", "")).strip(),
                "name": str(row.get("F.I.Sh.", "")).strip(),
                "position": str(row.get("Lavozim", "")).strip(),
            })

    return employees
def save_profilaktika(
    base_id,
    base_name,
    date_text,
    time_text,
    employee_names,
    comment,
    period
):
    """
    Profilaktika ma'lumotlarini Google Sheets'ning
    Profilaktika varag'iga saqlaydi.
    """

    profilaktika_sheet = spreadsheet.worksheet("Profilaktika")

    # Sana va vaqtni bitta qiymat qilamiz
    date_time_text = f"{date_text} {time_text}"

    # Bir nechta xodim nomini bitta katakka yozamiz
    employees_text = "; ".join(employee_names)

    row = [
        base_id,
        base_name,
        date_time_text,
        employees_text,
        comment,
        period
    ]

    profilaktika_sheet.append_row(
        row,
        value_input_option="USER_ENTERED"
    )

    return base_id

def get_profilaktika_records():
    """
    Profilaktika varag'idagi barcha yozuvlarni qaytaradi.
    """
    profilaktika_sheet = spreadsheet.worksheet("Profilaktika")

    return profilaktika_sheet.get_all_records()