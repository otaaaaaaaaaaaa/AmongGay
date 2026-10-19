import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open(
    "SchoolAmongUs"
).worksheet("players")


def add_player(name, user_id):
    sheet.append_row([
        name,
        user_id,
        ""
    ])


def get_players():
    return sheet.get_all_records()
