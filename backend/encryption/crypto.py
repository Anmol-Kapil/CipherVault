"""AES-256-GCM with a persistent, local installation key."""
import base64
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from backend.database import DATA_DIR

KEY_PATH = DATA_DIR / 'master.key'
if not KEY_PATH.exists():
    if (DATA_DIR / 'blobs').exists() and any((DATA_DIR / 'blobs').glob('*.bin')):
        raise RuntimeError('master.key is missing but encrypted files exist. Restore the original key from backup.')
    try:
        with KEY_PATH.open('xb') as key_file:
            key_file.write(get_random_bytes(32))
    except FileExistsError:
        pass
KEY = KEY_PATH.read_bytes()
if len(KEY) != 32:
    raise RuntimeError('Invalid master.key. Restore the original 32-byte key from backup.')

def encrypt_data(data: bytes) -> bytes:
    cipher = AES.new(KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return json.dumps({k: base64.b64encode(v).decode() for k, v in
        {'nonce': cipher.nonce, 'tag': tag, 'ciphertext': ciphertext}.items()}).encode()

def decrypt_data(data: bytes) -> bytes:
    payload = {k: base64.b64decode(v) for k, v in json.loads(data).items()}
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=payload['nonce'])
    return cipher.decrypt_and_verify(payload['ciphertext'], payload['tag'])
