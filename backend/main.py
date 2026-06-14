from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from passlib.hash import bcrypt
from fastapi import Form
from fastapi import HTTPException
import secrets
from encryption.crypto import (
    encrypt_data,
    decrypt_data
)

from database import (
    SessionLocal,
    engine,
    Base
)

from models import (
    FileMetadata
)
from drive_service import (
    upload_to_drive,
    download_from_drive,
    delete_from_drive
)

from datetime import datetime

import json
import uuid
import os
import base64

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)


@app.get("/")
def home():
    return {
        "message": "Secure Cloud Storage Running"
    }


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    filename = file.filename
    mime_type = file.content_type
    file_bytes = await file.read()
    access_id = secrets.token_urlsafe(12)    
    password_hash = bcrypt.hash(password)
    payload = {
        "filename": filename,
        "mime_type": mime_type,
        "file_data": base64.b64encode(file_bytes).decode()
    }

    encrypted = encrypt_data(
        json.dumps(payload).encode()
    )

    os.makedirs(
        "temp",
        exist_ok=True
    )

    temp_file = f"temp/{uuid.uuid4()}.bin"

    nonce = encrypted["nonce"].encode()
    tag = encrypted["tag"].encode()
    ciphertext = encrypted["ciphertext"].encode()

    with open(temp_file, "wb") as f:

        f.write(
            len(nonce).to_bytes(
                4,
                "big"
            )
        )

        f.write(nonce)

        f.write(
            len(tag).to_bytes(
                4,
                "big"
            )
        )

        f.write(tag)

        f.write(ciphertext)

    drive_file_id = upload_to_drive(
        temp_file
    )

    db = SessionLocal()

    new_file = FileMetadata(
        access_id=access_id,
        filename=filename,
        mime_type=mime_type,
        drive_file_id=drive_file_id,
        password_hash=password_hash,
        upload_date=str(
            datetime.now()
        )
    )

    db.add(new_file)
    db.commit()
    db.close()

    os.remove(temp_file)

    return {
        "message": "Encrypted file uploaded successfully",
        "access_id": access_id
    }


@app.post("/download")
def download_file(
    access_id: str,
    password: str
):
    db = SessionLocal()

    file = db.query(
        FileMetadata
    ).filter(
        FileMetadata.access_id == access_id
    ).first()

    if not file:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Invalid Access ID"
        )

    if not bcrypt.verify(
        password,
        file.password_hash
    ):

        db.close()

        raise HTTPException(
            status_code=401,
            detail="Invalid Password"
        )

    drive_file_id = file.drive_file_id

    db.close()

    downloaded_data = download_from_drive(
        drive_file_id
    )

    offset = 0

    nonce_len = int.from_bytes(
        downloaded_data[
            offset:offset + 4
        ],
        "big"
    )

    offset += 4

    nonce = downloaded_data[
        offset:offset + nonce_len
    ].decode()

    offset += nonce_len

    tag_len = int.from_bytes(
        downloaded_data[
            offset:offset + 4
        ],
        "big"
    )

    offset += 4

    tag = downloaded_data[
        offset:offset + tag_len
    ].decode()

    offset += tag_len

    ciphertext = downloaded_data[
        offset:
    ].decode()

    decrypted_payload = decrypt_data(
        nonce,
        tag,
        ciphertext
    )

    payload = json.loads(
        decrypted_payload.decode()
    )

    filename = payload["filename"]
    mime_type = payload["mime_type"]

    file_bytes = base64.b64decode(
        payload["file_data"]
    )

    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition":
            f'attachment; filename="{filename}"'
        }
    )


@app.get("/files")
def get_files():

    db = SessionLocal()

    files = db.query(
        FileMetadata
    ).all()

    result = []

    for file in files:

        result.append({
            "id": file.id,
            "filename": file.filename,
            "mime_type": file.mime_type,
            "drive_file_id": file.drive_file_id,
            "upload_date": file.upload_date
        })

    db.close()

    return result


@app.delete("/files/{file_id}")
def delete_file(file_id: int):

    db = SessionLocal()

    file = db.query(
        FileMetadata
    ).filter(
        FileMetadata.id == file_id
    ).first()

    if not file:

        db.close()

        return {
            "message":
            "File not found"
        }

    delete_from_drive(
        file.drive_file_id
    )

    db.delete(file)

    db.commit()

    db.close()

    return {
        "message":
        "File deleted successfully"
    }