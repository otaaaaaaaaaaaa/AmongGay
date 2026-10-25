import gspread

from oauth2client.service_account import (
    ServiceAccountCredentials
)

from config.settings import SPREADSHEET_NAME


scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "/etc/secrets/credentials.json",
    scope,
)

client = gspread.authorize(creds)
spreadsheet = client.open(SPREADSHEET_NAME)

users_sheet = spreadsheet.worksheet("users")
tasks_sheet = spreadsheet.worksheet("tasks")
game_state_sheet = spreadsheet.worksheet("game_state")
players_sheet = spreadsheet.worksheet("players")
