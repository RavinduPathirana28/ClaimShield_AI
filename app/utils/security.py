import hashlib
import os
import re
import datetime
import jwt
from app import config

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with a random salt."""
    salt = os.urandom(16)
    db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + db_hash.hex()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against its PBKDF2 hash."""
    try:
        salt_hex, hash_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        db_hash = bytes.fromhex(hash_hex)
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return new_hash == db_hash
    except Exception:
        return False

def sanitize_input(text: str) -> str:
    """Sanitizes user input by removing HTML tags and scripts, and truncating length."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Remove javascript schemes
    clean = re.sub(r'javascript:', '', clean, flags=re.IGNORECASE)
    # Remove inline script tags or alert calls
    clean = re.sub(r'script', '', clean, flags=re.IGNORECASE)
    # Truncate length to prevent buffer/rate abuses
    return clean.strip()[:1000]

def generate_jwt(username: str, role: str) -> str:
    """Generates a JSON Web Token for the user session."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=config.JWT_EXPIRY_MINUTES)
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")

def verify_jwt(token: str) -> dict:
    """Verifies a JWT token, returning the payload or an error dict."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired."}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token."}

def encrypt_data(plaintext: str) -> str:
    """Encrypts plaintext using Fernet symmetric encryption for data-at-rest protection."""
    from cryptography.fernet import Fernet
    key = config.ENCRYPTION_KEY
    if not key:
        return plaintext  # Graceful fallback if no key configured
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')
    except Exception:
        return plaintext  # Fallback to unencrypted on error


def decrypt_data(ciphertext: str) -> str:
    """Decrypts Fernet-encrypted ciphertext back to plaintext."""
    from cryptography.fernet import Fernet
    key = config.ENCRYPTION_KEY
    if not key:
        return ciphertext
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception:
        return ciphertext  # Return as-is if decryption fails (e.g. unencrypted legacy data)
