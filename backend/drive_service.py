"""Only encrypted bytes and opaque names are sent to Google Drive."""
import io
from functools import wraps
from httplib2 import HttpLib2Error
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from backend.config import FOLDER_ID
from backend.drive_auth import get_credentials, DriveAuthError

class DriveStorageError(RuntimeError):
    pass

def get_drive_service():
    return build('drive', 'v3', credentials=get_credentials(), cache_discovery=False)

def drive_operation(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except DriveAuthError as error:
            raise DriveStorageError(str(error)) from error
        except HttpError as error:
            status = error.resp.status
            if status == 404:
                message = 'Drive file or folder was not found. Check the connected Google account, folder access, and whether the file was removed in Drive.'
            elif status in (401, 403):
                message = 'Google Drive denied access. Check OAuth authorization, Drive API access, folder permissions, and storage quota.'
            elif status == 429:
                message = 'Google Drive is busy. Wait a moment and try again.'
            else:
                message = 'Google Drive could not complete the request. Try again later.'
            raise DriveStorageError(message) from error
        except (OSError, HttpLib2Error) as error:
            raise DriveStorageError('Cannot reach Google Drive. Check your internet connection and try again.') from error
    return wrapped

@drive_operation
def check_connection():
    get_drive_service().files().list(pageSize=1, fields='files(id)').execute()

def get_folder_id(service):
    if FOLDER_ID:
        folder = service.files().get(fileId=FOLDER_ID, fields='id,mimeType,trashed').execute()
        if folder.get('trashed') or folder.get('mimeType') != 'application/vnd.google-apps.folder':
            raise DriveStorageError('GOOGLE_FOLDER_ID must identify an accessible, non-trashed Drive folder.')
        return FOLDER_ID
    # drive.file sees only app-accessible files; no access to unrelated Drive files is requested.
    folders = service.files().list(
        q="name = 'CipherVault' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        spaces='drive', pageSize=100, fields='files(id)').execute().get('files', [])
    if folders:
        return folders[0]['id']
    return service.files().create(body={'name': 'CipherVault', 'mimeType': 'application/vnd.google-apps.folder'}, fields='id').execute()['id']

@drive_operation
def upload_to_drive(data: bytes, name: str) -> str:
    service = get_drive_service()
    parent = get_folder_id(service)
    return service.files().create(body={'name': name, 'parents': [parent]},
        media_body=MediaIoBaseUpload(io.BytesIO(data), mimetype='application/octet-stream', resumable=True),
        fields='id').execute()['id']

@drive_operation
def download_from_drive(file_id: str) -> bytes:
    service = get_drive_service()
    output = io.BytesIO()
    downloader = MediaIoBaseDownload(output, service.files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return output.getvalue()

@drive_operation
def delete_from_drive(file_id: str):
    get_drive_service().files().delete(fileId=file_id).execute()
