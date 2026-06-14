from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import (
    MediaFileUpload,
    MediaIoBaseDownload
)

from dotenv import load_dotenv

import io
import os

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]

# Your Secure Cloud Storage folder
FOLDER_ID = "1Ey9Rvr1Ot_27SrsQmI1QWsSWMQIEZhMh"


def get_drive_service():

    creds = Credentials.from_authorized_user_file(
        "token.json",
        SCOPES
    )

    service = build(
        "drive",
        "v3",
        credentials=creds
    )

    return service


def upload_to_drive(filepath):

    service = get_drive_service()

    metadata = {
        "name": os.path.basename(filepath),
        "parents": [FOLDER_ID]
    }

    media = MediaFileUpload(
        filepath,
        mimetype="application/octet-stream"
    )

    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name"
    ).execute()

    return uploaded["id"]


def download_from_drive(file_id):

    service = get_drive_service()

    request = service.files().get_media(
        fileId=file_id
    )

    file_stream = io.BytesIO()

    downloader = MediaIoBaseDownload(
        file_stream,
        request
    )

    done = False

    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)

    return file_stream.read()


def delete_from_drive(file_id):

    service = get_drive_service()

    service.files().delete(
        fileId=file_id
    ).execute()

    return True