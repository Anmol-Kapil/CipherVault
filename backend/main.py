"""Locally run file vault backed by the user's own Google Drive. Run from the repository root."""
from datetime import datetime, timezone
from urllib.parse import quote
import secrets
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, JSONResponse
from passlib.hash import bcrypt
from pydantic import BaseModel, Field
from backend.database import SessionLocal, initialize_database
from backend.models import FileMetadata
from backend.encryption.crypto import encrypt_data, decrypt_data
from backend import storage_service as storage

app = FastAPI(title='CipherVault Drive', version='2.1.0')
initialize_database()
MAX_SIZE = 25 * 1024 * 1024

class Credentials(BaseModel):
    access_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=72)

def verify_password(password, stored_hash):
    if len(password.encode()) > 72 or not bcrypt.verify(password, stored_hash):
        raise HTTPException(401, 'Incorrect password. Try again.')

@app.get('/')
def health():
    return {'status': 'ok', 'storage': storage.storage_status(), 'max_file_size': MAX_SIZE}

@app.exception_handler(storage.StorageError)
async def storage_error_handler(request, error):
    return JSONResponse(status_code=503, content={'detail': str(error)})

@app.post('/storage/check')
def check_storage():
    return storage.check()

@app.post('/upload', status_code=201)
async def upload(file: UploadFile = File(...), username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    if not 1 <= len(username) <= 80:
        raise HTTPException(422, 'Use a username between 1 and 80 characters.')
    if not 8 <= len(password.encode()) <= 72:
        raise HTTPException(422, 'Use a password between 8 and 72 bytes.')
    data = await file.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise HTTPException(413, 'Files must be 25 MB or smaller.')
    access_id = secrets.token_urlsafe(18)
    storage_backend, storage_id = storage.save(encrypt_data(data), access_id)
    try:
        with SessionLocal() as db:
            entry = FileMetadata(access_id=access_id, username=username,
                filename=(file.filename or 'download').replace('\\', '/').split('/')[-1],
                mime_type=file.content_type or 'application/octet-stream', size=len(data),
                password_hash=bcrypt.hash(password), upload_date=datetime.now(timezone.utc).isoformat(),
                storage_backend=storage_backend, storage_id=storage_id)
            db.add(entry)
            db.flush()
            file_id = entry.id
            db.commit()
    except Exception:
        # Roll back the uploaded object if metadata persistence fails.
        try:
            from types import SimpleNamespace
            storage.remove(SimpleNamespace(storage_backend=storage_backend, storage_id=storage_id, access_id=access_id))
        except storage.StorageError:
            pass
        raise
    return {'message': 'File encrypted and saved.', 'access_id': access_id, 'file_id': file_id, 'storage_backend': storage_backend}

@app.get('/files')
@app.get('/user-files/{username}')
def list_files(username: str | None = None):
    with SessionLocal() as db:
        query = db.query(FileMetadata)
        if username:
            query = query.filter(FileMetadata.username == username)
        return [{key: getattr(item, key) for key in ('id', 'username', 'filename', 'mime_type', 'size', 'upload_date', 'storage_backend')}
                for item in query.order_by(FileMetadata.id.desc()).all()]

@app.post('/download')
def download(credentials: Credentials):
    with SessionLocal() as db:
        entry = db.query(FileMetadata).filter_by(access_id=credentials.access_id.strip()).first()
        if not entry:
            raise HTTPException(404, 'No file matches that access ID.')
        verify_password(credentials.password, entry.password_hash)
        try:
            data = decrypt_data(storage.load(entry))
        except FileNotFoundError:
            raise HTTPException(404, 'The encrypted file is missing from local storage.')
        except ValueError:
            raise HTTPException(409, 'File integrity check failed. Restore your file and key backup.')
        return Response(data, media_type='application/octet-stream', headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{quote(entry.filename, safe='')}",
            'X-Content-Type-Options': 'nosniff'})

class DeleteCredentials(BaseModel):
    password: str = Field(min_length=1, max_length=72)

@app.delete('/files/{file_id}')
def delete(file_id: int, credentials: DeleteCredentials):
    with SessionLocal() as db:
        entry = db.get(FileMetadata, file_id)
        if not entry:
            raise HTTPException(404, 'File not found.')
        verify_password(credentials.password, entry.password_hash)
        storage.remove(entry)
        db.delete(entry)
        db.commit()
    return {'message': 'File permanently deleted from its storage.'}
