import os
import json
import hashlib
import uuid
import base64
from cryptography.fernet import Fernet

VAULT_FILE = 'vault.dat'

def get_master_key():
    mac = uuid.getnode()
    hash_obj = hashlib.sha256(str(mac).encode())
    key = base64.urlsafe_b64encode(hash_obj.digest())
    return key

def encrypt_data(data):
    key = get_master_key()
    f = Fernet(key)
    return f.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data):
    key = get_master_key()
    f = Fernet(key)
    return json.loads(f.decrypt(encrypted_data).decode())

def create_vault():
    vault = {}
    with open(VAULT_FILE, 'wb') as f:
        f.write(encrypt_data(vault))

def load_vault():
    if not os.path.exists(VAULT_FILE):
        create_vault()
    with open(VAULT_FILE, 'rb') as f:
        encrypted = f.read()
    return decrypt_data(encrypted)

def save_vault(vault):
    with open(VAULT_FILE, 'wb') as f:
        f.write(encrypt_data(vault))

def set_key(name, value):
    vault = load_vault()
    vault[name] = value
    save_vault(vault)

def get_key(name):
    vault = load_vault()
    return vault.get(name)
