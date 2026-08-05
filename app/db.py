import os

from dotenv import load_dotenv
from libsql_client import create_client_sync


load_dotenv()

TURSO_DATABASE_URL = (
    os.getenv("TURSO_DATABASE_URL")
    .replace("libsql://", "https://")
)

TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

db = create_client_sync(
    url=TURSO_DATABASE_URL,
    auth_token=TURSO_AUTH_TOKEN
)