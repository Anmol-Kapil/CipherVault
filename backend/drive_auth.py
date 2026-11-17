"""Connect your own Google account. No browser authentication occurs at import."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from backend.config import CREDENTIALS_PATH, TOKEN_PATH, SCOPES

class DriveAuthError(RuntimeError):
    pass

def save_token(credentials):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=TOKEN_PATH.parent,
                prefix=TOKEN_PATH.name + '.', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(credentials.to_json())
        os.replace(temporary, TOKEN_PATH)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def get_credentials():
    if not TOKEN_PATH.is_file():
        raise DriveAuthError('Google Drive is not connected. Follow the README and run python -m backend.drive_auth with your own OAuth credentials.')
    try:
        credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if not credentials.has_scopes(SCOPES):
            raise DriveAuthError('Drive permission is missing. Reconnect with python -m backend.drive_auth.')
        if not credentials.valid:
            if not credentials.refresh_token:
                raise DriveAuthError('Google authorization has expired. Reconnect with python -m backend.drive_auth.')
            credentials.refresh(Request())
            save_token(credentials)
        return credentials
    except (RefreshError, TransportError) as error:
        raise DriveAuthError('Could not refresh Google authorization. Check your internet connection or reconnect with python -m backend.drive_auth.') from error
    except (ValueError, OSError) as error:
        raise DriveAuthError('Cannot read Google authorization. Check GOOGLE_TOKEN_FILE or reconnect with python -m backend.drive_auth.') from error

def connect():
    if not CREDENTIALS_PATH.is_file():
        raise DriveAuthError('Missing credentials.json. Download your own Desktop app OAuth client from Google Cloud; see the README Google Drive setup.')
    try:
        config = json.loads(CREDENTIALS_PATH.read_text(encoding='utf-8-sig'))
        if 'installed' not in config:
            raise DriveAuthError('Use a Desktop app OAuth client JSON, not an API key, service account, or Web application client.')
        flow = InstalledAppFlow.from_client_config(config, SCOPES)
        credentials = flow.run_local_server(host='127.0.0.1', port=0, access_type='offline', prompt='consent')
        save_token(credentials)
    except (ValueError, OSError) as error:
        raise DriveAuthError('Could not load Desktop app OAuth credentials. Download a fresh credentials.json from your Google Cloud project.') from error
    print('Google Drive authorization saved. Keep token.json private. Start or refresh CipherVault, then check the Drive connection.')

def main():
    parser = argparse.ArgumentParser(description='Connect your own Google Drive to CipherVault.')
    parser.add_argument('--check', action='store_true', help='Check existing authorization without opening a login flow.')
    args = parser.parse_args()
    try:
        if args.check:
            from backend.drive_service import check_connection
            check_connection()
            print('Google Drive connection verified.')
        else:
            connect()
    except (DriveAuthError, RuntimeError) as error:
        parser.exit(1, f'{error}\n')

if __name__ == '__main__':
    main()
