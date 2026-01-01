"""
RSA Cryptography Module
Hybrid RSA+AES encryption for forensic evidence
RSA encrypts session keys, AES encrypts data
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# RSA Configuration
RSA_KEY_SIZE = 2048  # bits
RSA_PUBLIC_EXPONENT = 65537


def generate_rsa_keypair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate RSA 2048-bit key pair
    
    Returns:
        (private_key, public_key) tuple
    """
    private_key = rsa.generate_private_key(
        public_exponent=RSA_PUBLIC_EXPONENT,
        key_size=RSA_KEY_SIZE,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    logger.info(f"Generated RSA-{RSA_KEY_SIZE} key pair")
    return private_key, public_key


def save_private_key(
    private_key: rsa.RSAPrivateKey,
    filepath: str,
    password: Optional[str] = None
) -> None:
    """
    Save RSA private key to PEM file
    
    Args:
        private_key: RSA private key object
        filepath: Output file path
        password: Optional password to encrypt the key file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if password:
        encryption = serialization.BestAvailableEncryption(password.encode())
    else:
        encryption = serialization.NoEncryption()
    
    pem_data = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption
    )
    
    with open(path, 'wb') as f:
        f.write(pem_data)
    
    # Set restrictive permissions
    try:
        os.chmod(path, 0o600)
    except:
        pass  # Windows may not support chmod
    
    logger.info(f"Saved private key: {filepath}")


def save_public_key(public_key: rsa.RSAPublicKey, filepath: str) -> None:
    """
    Save RSA public key to PEM file
    
    Args:
        public_key: RSA public key object
        filepath: Output file path
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    pem_data = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open(path, 'wb') as f:
        f.write(pem_data)
    
    logger.info(f"Saved public key: {filepath}")


def load_private_key(
    filepath: str,
    password: Optional[str] = None
) -> rsa.RSAPrivateKey:
    """
    Load RSA private key from PEM file
    
    Args:
        filepath: Path to private key file
        password: Password if key is encrypted
        
    Returns:
        RSA private key object
    """
    with open(filepath, 'rb') as f:
        pem_data = f.read()
    
    pwd = password.encode() if password else None
    
    private_key = serialization.load_pem_private_key(
        pem_data,
        password=pwd,
        backend=default_backend()
    )
    
    logger.debug(f"Loaded private key: {filepath}")
    return private_key


def load_public_key(filepath: str) -> rsa.RSAPublicKey:
    """
    Load RSA public key from PEM file
    
    Args:
        filepath: Path to public key file
        
    Returns:
        RSA public key object
    """
    with open(filepath, 'rb') as f:
        pem_data = f.read()
    
    public_key = serialization.load_pem_public_key(
        pem_data,
        backend=default_backend()
    )
    
    logger.debug(f"Loaded public key: {filepath}")
    return public_key


def encrypt_session_key(session_key: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """
    Encrypt AES session key with RSA public key
    
    Uses OAEP padding with SHA-256 for security
    
    Args:
        session_key: 32-byte AES key to encrypt
        public_key: RSA public key
        
    Returns:
        RSA-encrypted session key (256 bytes for RSA-2048)
    """
    encrypted = public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return encrypted


def decrypt_session_key(
    encrypted_key: bytes,
    private_key: rsa.RSAPrivateKey
) -> bytes:
    """
    Decrypt AES session key with RSA private key
    
    Args:
        encrypted_key: RSA-encrypted session key
        private_key: RSA private key
        
    Returns:
        Original 32-byte AES session key
    """
    session_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return session_key


def get_key_fingerprint(public_key: rsa.RSAPublicKey) -> str:
    """
    Get SHA-256 fingerprint of public key
    
    Args:
        public_key: RSA public key
        
    Returns:
        Hex string fingerprint (first 16 chars)
    """
    import hashlib
    
    pem_data = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    fingerprint = hashlib.sha256(pem_data).hexdigest()
    return fingerprint[:16]


# Test code
if __name__ == "__main__":
    print("=" * 50)
    print("RSA Crypto Module Test")
    print("=" * 50)
    
    # Generate key pair
    priv, pub = generate_rsa_keypair()
    print(f"\n✓ Generated RSA-{RSA_KEY_SIZE} key pair")
    print(f"  Public key fingerprint: {get_key_fingerprint(pub)}...")
    
    # Test session key encryption
    session_key = os.urandom(32)  # AES-256 key
    print(f"\n✓ Original session key: {session_key.hex()[:32]}...")
    
    # Encrypt
    encrypted = encrypt_session_key(session_key, pub)
    print(f"✓ Encrypted key size: {len(encrypted)} bytes")
    
    # Decrypt
    decrypted = decrypt_session_key(encrypted, priv)
    print(f"✓ Decrypted session key: {decrypted.hex()[:32]}...")
    
    assert session_key == decrypted
    print("\n✅ Encryption/Decryption successful!")
