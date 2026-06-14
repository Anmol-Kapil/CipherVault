from Crypto.Cipher import AES
import base64

# 32-byte AES key (temporary for development)
AES_KEY=12345678901234567890123456789012

def encrypt_data(data: bytes):

    cipher = AES.new(KEY, AES.MODE_GCM)

    ciphertext, tag = cipher.encrypt_and_digest(data)

    return {
        "nonce": base64.b64encode(cipher.nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode()
    }


def decrypt_data(nonce, tag, ciphertext):

    nonce = base64.b64decode(nonce)
    tag = base64.b64decode(tag)
    ciphertext = base64.b64decode(ciphertext)

    cipher = AES.new(KEY, AES.MODE_GCM, nonce=nonce)

    plaintext = cipher.decrypt_and_verify(ciphertext, tag)

    return plaintext