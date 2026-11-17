"""Regression tests use a temporary vault, never your personal local data."""
import importlib
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

_temp = tempfile.TemporaryDirectory()
os.environ['CIPHERVAULT_DATA_DIR'] = _temp.name
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
        access_id = self.upload(original, 'notes é.txt')
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
        for username, password in [(' ', self.password), ('owner', 'short'), ('owner', 'é' * 40)]:
            response = self.client.post('/upload', files={'file': ('test.txt', b'hi')}, data={'username': username, 'password': password})
            self.assertEqual(response.status_code, 422)
        response = self.client.post('/upload', files={'file': ('large.bin', b'x' * (25 * 1024 * 1024 + 1))}, data={'username': 'owner', 'password': self.password})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.client.post('/download', json={}).status_code, 422)

if __name__ == '__main__':
    unittest.main()

def tearDownModule():
    from backend.database import engine
    engine.dispose()
    _temp.cleanup()


if __name__ == '__main__':
    unittest.main()
