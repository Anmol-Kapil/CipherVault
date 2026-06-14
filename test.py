from crypto import *

msg = b"Hello Anmol"

enc = encrypt_data(msg)

print(enc)

dec = decrypt_data(
    enc["nonce"],
    enc["tag"],
    enc["ciphertext"]
)

print(dec)