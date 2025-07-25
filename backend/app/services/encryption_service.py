from cryptography.fernet import Fernet
from app.core.config import settings
import base64

# This ensures the app crashes on startup if the key is missing
if not settings.ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is not configured.")

# The key from .env is a 64-char hex string (32 bytes).
# Fernet needs a 32-byte URL-safe base64 encoded key. We must convert it.
key_hex = settings.ENCRYPTION_KEY
key_bytes = bytes.fromhex(key_hex) # Convert hex string to raw bytes
key_base64 = base64.urlsafe_b64encode(key_bytes) # Encode the raw bytes to base64

cipher_suite = Fernet(key_base64)

def encrypt_token(token: str) -> str:
    """Encrypts a string token."""
    encrypted_token = cipher_suite.encrypt(token.encode())
    return encrypted_token.decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts an encrypted token string."""
    decrypted_token = cipher_suite.decrypt(encrypted_token.encode())
    return decrypted_token.decode()