"""Configuration for a locally run app backed by the user's Google Drive."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')

def root_path(value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path

DATA_DIR = root_path(os.getenv('CIPHERVAULT_DATA_DIR', '.local-data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_BACKEND = os.getenv('CIPHERVAULT_STORAGE', 'drive').strip().lower()
if STORAGE_BACKEND not in {'drive', 'local'}:
    raise RuntimeError('CIPHERVAULT_STORAGE must be drive or local.')
CREDENTIALS_PATH = root_path(os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'))
TOKEN_PATH = root_path(os.getenv('GOOGLE_TOKEN_FILE', 'token.json'))
FOLDER_ID = os.getenv('GOOGLE_FOLDER_ID', '').strip()
SCOPES = ['https://www.googleapis.com/auth/drive.file']
