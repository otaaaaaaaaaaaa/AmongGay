import os

from dotenv import load_dotenv


load_dotenv()


CHANNEL_ACCESS_TOKEN = os.getenv(
    "CHANNEL_ACCESS_TOKEN"
)

CHANNEL_SECRET = os.getenv(
    "CHANNEL_SECRET"
)

SPREADSHEET_NAME = os.getenv(
    "SPREADSHEET_NAME"
)

ADMIN_ID = os.getenv(
    "ADMIN_ID"
)
