"""Single-user, loopback-only file vault. Run from the repository root."""
from datetime import datetime, timezone
from urllib.parse import quote
import secrets
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from passlib.hash import bcrypt
from pydantic import BaseModel, Field
from backend.database import DATA_DIR, Base, SessionLocal, engine
from backend.models import FileMetadata
from backend.encryption.crypto import encrypt_data, decrypt_data

app = FastAPI(title='CipherVault Local', version='2.0.0')
Base.metadata.create_all(bind=engine)
BLOBS = DATA_DIR / 'blobs'
BLOBS.mkdir(exist_ok=True)
MAX_SIZE = 25 * 1024 * 1024

class Credentials(BaseModel):
    access_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=72)

def verify_password(password, stored_hash):
    if len(password.encode()) > 72 or not bcrypt.verify(password, stored_hash):
        raise HTTPException(401, 'Incorrect password. Try again.')

@app.get('/')
def health():
    return {'status': 'ok', 'storage': 'local', 'max_file_size': MAX_SIZE}

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
    blob = BLOBS / f'{access_id}.bin'
    blob.write_bytes(encrypt_data(data))
    try:
        with SessionLocal() as db:
            entry = FileMetadata(access_id=access_id, username=username,
                filename=(file.filename or 'download').replace('\\', '/').split('/')[-1],
                mime_type=file.content_type or 'application/octet-stream', size=len(data),
                password_hash=bcrypt.hash(password), upload_date=datetime.now(timezone.utc).isoformat())
            db.add(entry)
            db.commit()
            file_id = entry.id
    except Exception:
        blob.unlink(missing_ok=True)
        raise
    return {'message': 'File encrypted and saved locally.', 'access_id': access_id, 'file_id': file_id}

@app.get('/files')
@app.get('/user-files/{username}')
def list_files(username: str | None = None):
    with SessionLocal() as db:
        query = db.query(FileMetadata)
        if username:
            query = query.filter(FileMetadata.username == username)
        return [{key: getattr(item, key) for key in ('id', 'username', 'filename', 'mime_type', 'size', 'upload_date')}
                for item in query.order_by(FileMetadata.id.desc()).all()]

@app.post('/download')
def download(credentials: Credentials):
    with SessionLocal() as db:
        entry = db.query(FileMetadata).filter_by(access_id=credentials.access_id.strip()).first()
        if not entry:
            raise HTTPException(404, 'No file matches that access ID.')
        verify_password(credentials.password, entry.password_hash)
        try:
            data = decrypt_data((BLOBS / f'{entry.access_id}.bin').read_bytes())
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
        (BLOBS / f'{entry.access_id}.bin').unlink(missing_ok=True)
        db.delete(entry)
        db.commit()
    return {'message': 'File permanently deleted.'}
