"""Regression tests use a temporary vault, never your personal local data."""
import importlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import tempfile
import unittest

_temp = tempfile.TemporaryDirectory()
os.environ['CIPHERVAULT_DATA_DIR'] = _temp.name
os.environ['CIPHERVAULT_STORAGE'] = 'local'
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import DATA_DIR
from backend.encryption import crypto

class VaultTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.password = 'test-password-2026'

    def tearDown(self):
        self.client.close()

    def upload(self, data=b'private original content', filename='hello.txt'):
        response = self.client.post('/upload', files={'file': (filename, data, 'text/plain')}, data={'username': 'test-owner', 'password': self.password})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['access_id']

    def test_round_trip_restart_and_metadata(self):
        original = b'confidential round trip\x00\xff'
        access_id = self.upload(original, 'notes \u00e9.txt')
        blob = (DATA_DIR / 'blobs' / f'{access_id}.bin').read_bytes()
        self.assertNotIn(original, blob)
        key = crypto.KEY
        importlib.reload(crypto)
        self.assertEqual(key, crypto.KEY)
        restarted = subprocess.run([sys.executable, '-c',
            "from backend.encryption.crypto import decrypt_data; from backend.database import DATA_DIR; import sys; "
            "sys.stdout.buffer.write(decrypt_data((DATA_DIR / 'blobs' / (sys.argv[1] + '.bin')).read_bytes()))",
            access_id], check=True, capture_output=True)
        self.assertEqual(restarted.stdout, original)
        response = self.client.post('/download', json={'access_id': access_id, 'password': self.password})
        self.assertEqual(response.content, original)
        self.assertIn("filename*=UTF-8''notes%20%C3%A9.txt", response.headers['content-disposition'])
        metadata = self.client.get('/user-files/test-owner').json()
        self.assertTrue(any(row['size'] == len(original) for row in metadata))
        self.assertNotIn('access_id', metadata[0])
        self.assertNotIn('password_hash', metadata[0])
        self.assertEqual(self.client.get('/user-files/no-such-owner').json(), [])

    def test_credentials_deletion_and_missing_file(self):
        access_id = self.upload()
        bad = {'access_id': access_id, 'password': 'wrong-password'}
        self.assertEqual(self.client.post('/download', json=bad).status_code, 401)
        row = self.client.get('/files').json()[0]
        url = f"/files/{row['id']}"
        self.assertEqual(self.client.request('DELETE', url, json={'password': 'wrong-password'}).status_code, 401)
        self.assertEqual(self.client.request('DELETE', url, json={'password': self.password}).status_code, 200)
        self.assertFalse((DATA_DIR / 'blobs' / f'{access_id}.bin').exists())
        self.assertEqual(self.client.post('/download', json={'access_id': access_id, 'password': self.password}).status_code, 404)
        self.assertEqual(self.client.request('DELETE', url, json={'password': self.password}).status_code, 404)

    def test_integrity_failure(self):
        access_id = self.upload()
        blob = DATA_DIR / 'blobs' / f'{access_id}.bin'
        import json
        payload = json.loads(blob.read_bytes())
        payload['tag'] = 'AAAAAAAAAAAAAAAAAAAAAA=='
        blob.write_text(json.dumps(payload))
        response = self.client.post('/download', json={'access_id': access_id, 'password': self.password})
        self.assertEqual(response.status_code, 409)

    def test_input_validation_and_limit(self):
        for username, password in [(' ', self.password), ('owner', 'short'), ('owner', '\u00e9' * 40)]:
            response = self.client.post('/upload', files={'file': ('test.txt', b'hi')}, data={'username': username, 'password': password})
            self.assertEqual(response.status_code, 422)
        response = self.client.post('/upload', files={'file': ('large.bin', b'x' * (25 * 1024 * 1024 + 1))}, data={'username': 'owner', 'password': self.password})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.client.post('/download', json={}).status_code, 422)



class DriveTests(unittest.TestCase):
    def setUp(self):
        from backend import storage_service
        self.storage = storage_service
        self.mode = patch.object(self.storage, 'STORAGE_BACKEND', 'drive')
        self.mode.start()
        self.client = TestClient(app)
        self.password = 'drive-test-password'
        self.blobs = {}

    def tearDown(self):
        self.client.close()
        self.mode.stop()

    def test_encrypted_drive_round_trip_and_delete(self):
        from backend import drive_service
        def save(data, name):
            self.blobs[name] = data
            return name
        with patch.object(drive_service, 'upload_to_drive', side_effect=save) as upload, \
             patch.object(drive_service, 'download_from_drive', side_effect=lambda key: self.blobs[key]), \
             patch.object(drive_service, 'delete_from_drive', side_effect=lambda key: self.blobs.pop(key)) as delete:
            original = b'private Drive content'
            response = self.client.post('/upload', files={'file': ('drive.txt', original)}, data={'username': 'drive-owner', 'password': self.password})
            self.assertEqual(response.status_code, 201, response.text)
            item = response.json()
            self.assertEqual(item['storage_backend'], 'drive')
            encrypted, opaque_name = upload.call_args.args
            self.assertNotIn(original, encrypted)
            self.assertNotIn('drive.txt', opaque_name)
            self.assertFalse((DATA_DIR / 'blobs' / f"{item['access_id']}.bin").exists())
            credentials = {'access_id': item['access_id'], 'password': self.password}
            self.assertEqual(self.client.post('/download', json=credentials).content, original)
            url = f"/files/{item['file_id']}"
            self.assertEqual(self.client.request('DELETE', url, json={'password': 'wrong-password'}).status_code, 401)
            delete.assert_not_called()
            self.assertEqual(self.client.request('DELETE', url, json={'password': self.password}).status_code, 200)
            self.assertEqual(self.blobs, {})
            self.assertEqual(self.client.post('/download', json=credentials).status_code, 404)

    def test_missing_authorization_and_network_error_do_not_fall_back(self):
        from backend import drive_service, drive_auth
        missing = DATA_DIR / 'no-token.json'
        with patch.object(drive_auth, 'TOKEN_PATH', missing):
            health = self.client.get('/').json()
            self.assertEqual(health['storage']['backend'], 'drive')
            response = self.client.post('/upload', files={'file': ('no.txt', b'no')}, data={'username': 'drive-owner', 'password': self.password})
            self.assertEqual(response.status_code, 503)
            self.assertIn('not connected', response.json()['detail'])
        with patch.object(drive_service, 'get_drive_service', side_effect=OSError('network unavailable')):
            response = self.client.post('/storage/check')
            self.assertEqual(response.status_code, 503)
            self.assertIn('internet', response.json()['detail'])

    def test_default_folder_and_opaque_upload(self):
        from backend import drive_service
        service = MagicMock()
        files = service.files.return_value
        files.list.return_value.execute.return_value = {'files': []}
        files.create.return_value.execute.side_effect = [{'id': 'folder'}, {'id': 'blob'}]
        with patch.object(drive_service, 'get_drive_service', return_value=service), patch.object(drive_service, 'FOLDER_ID', ''):
            self.assertEqual(drive_service.upload_to_drive(b'encrypted bytes', 'opaque.bin'), 'blob')
        calls = files.create.call_args_list
        self.assertEqual(calls[0].kwargs['body']['mimeType'], 'application/vnd.google-apps.folder')
        self.assertEqual(calls[1].kwargs['body'], {'name': 'opaque.bin', 'parents': ['folder']})
        self.assertEqual(calls[1].kwargs['media_body'].getbytes(0, 100), b'encrypted bytes')

    def test_drive_adapter_download_delete_and_permission_errors(self):
        from backend import drive_service
        from googleapiclient.errors import HttpError
        from httplib2 import HttpLib2Error
        service = MagicMock()
        def downloader(output, request):
            output.write(b'encrypted response')
            result = MagicMock()
            result.next_chunk.return_value = (None, True)
            return result
        with patch.object(drive_service, 'get_drive_service', return_value=service), \
             patch.object(drive_service, 'MediaIoBaseDownload', side_effect=downloader):
            self.assertEqual(drive_service.download_from_drive('drive-id'), b'encrypted response')
            service.files.return_value.get_media.assert_called_once_with(fileId='drive-id')
            drive_service.delete_from_drive('drive-id')
            service.files.return_value.delete.assert_called_once_with(fileId='drive-id')
        error = HttpError(SimpleNamespace(status=403, reason='Forbidden'), b'{}')
        with patch.object(drive_service, 'get_drive_service', side_effect=error):
            with self.assertRaisesRegex(drive_service.DriveStorageError, 'denied access'):
                drive_service.check_connection()
        with patch.object(drive_service, 'get_drive_service', side_effect=HttpLib2Error()):
            with self.assertRaisesRegex(drive_service.DriveStorageError, 'internet'):
                drive_service.check_connection()

    def test_token_refresh_persists_without_exposing_values(self):
        from backend import drive_auth
        token = DATA_DIR / 'refresh-token.json'
        credentials = MagicMock()
        credentials.valid = False
        credentials.refresh_token = 'synthetic-test-token'
        credentials.to_json.return_value = '{"token": "synthetic-updated-token"}'
        token.write_text('{}')
        with patch.object(drive_auth, 'TOKEN_PATH', token), \
             patch.object(drive_auth.Credentials, 'from_authorized_user_file', return_value=credentials):
            self.assertIs(drive_auth.get_credentials(), credentials)
        credentials.refresh.assert_called_once()
        self.assertEqual(token.read_text(), credentials.to_json.return_value)
        self.assertFalse(token.with_suffix('.json.tmp').exists())

    def test_legacy_local_metadata_migration(self):
        from sqlalchemy import create_engine, text, inspect
        from backend import database
        migration_engine = create_engine(f"sqlite:///{(DATA_DIR / 'legacy.db').as_posix()}")
        with migration_engine.begin() as connection:
            connection.execute(text('CREATE TABLE files (id INTEGER PRIMARY KEY, filename VARCHAR)'))
            connection.execute(text("INSERT INTO files (filename) VALUES ('keep-me.txt')"))
        with patch.object(database, 'engine', migration_engine):
            database.initialize_database()
        with migration_engine.connect() as connection:
            row = connection.execute(text('SELECT filename, storage_backend FROM files')).first()
            self.assertEqual(tuple(row), ('keep-me.txt', 'local'))
        migration_engine.dispose()


def tearDownModule():
    from backend.database import engine
    engine.dispose()
    _temp.cleanup()





if __name__ == '__main__':
    unittest.main()
