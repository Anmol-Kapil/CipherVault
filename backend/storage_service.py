"""Storage routing preserves existing local records while new uploads default to Drive."""
from backend import drive_service
from backend.config import DATA_DIR, STORAGE_BACKEND, TOKEN_PATH

BLOBS = DATA_DIR / 'blobs'

class StorageError(RuntimeError):
    pass

def storage_status():
    configured = STORAGE_BACKEND == 'local' or TOKEN_PATH.is_file()
    return {'backend': STORAGE_BACKEND, 'configured': configured,
            'verified': False, 'message': 'Offline demo uses local storage.' if STORAGE_BACKEND == 'local'
            else 'OAuth credentials found. Use Check Drive connection to verify access.' if configured
            else 'Connect your Google Drive using your own Desktop app OAuth credentials. See the README Google Drive setup.'}

def save(data: bytes, access_id: str):
    if STORAGE_BACKEND == 'drive':
        try:
            return 'drive', drive_service.upload_to_drive(data, f'{access_id}.bin')
        except drive_service.DriveStorageError as error:
            raise StorageError(str(error)) from error
    BLOBS.mkdir(exist_ok=True)
    (BLOBS / f'{access_id}.bin').write_bytes(data)
    return 'local', access_id

def load(entry) -> bytes:
    if entry.storage_backend == 'drive':
        try:
            return drive_service.download_from_drive(entry.storage_id)
        except drive_service.DriveStorageError as error:
            raise StorageError(str(error)) from error
    return (BLOBS / f'{entry.access_id}.bin').read_bytes()

def remove(entry):
    if entry.storage_backend == 'drive':
        try:
            drive_service.delete_from_drive(entry.storage_id)
        except drive_service.DriveStorageError as error:
            raise StorageError(str(error)) from error
    else:
        (BLOBS / f'{entry.access_id}.bin').unlink(missing_ok=True)

def check():
    if STORAGE_BACKEND == 'local':
        return {**storage_status(), 'verified': True}
    try:
        drive_service.check_connection()
    except drive_service.DriveStorageError as error:
        raise StorageError(str(error)) from error
    return {'backend': 'drive', 'configured': True, 'verified': True, 'message': 'Google Drive connection verified.'}
