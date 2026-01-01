"""
Security Module
AES-256-GCM encryption with SHA-256 integrity verification
Ensures forensic evidence cannot be tampered with
"""

import hashlib
import os
import base64
import logging
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EncryptedPackage:
    """Encrypted data package with metadata"""
    nonce: bytes
    ciphertext: bytes
    original_hash: str
    timestamp: float
    metadata: dict


class SecureVault:
    """
    Secure encryption/decryption for forensic evidence
    Uses AES-256-GCM for authenticated encryption
    Includes SHA-256 hash for integrity verification
    """
    
    NONCE_SIZE = 12  # 96 bits for GCM
    KEY_SIZE = 32    # 256 bits
    SALT_SIZE = 16   # 128 bits
    
    def __init__(self, key: Optional[bytes] = None, key_path: Optional[str] = None):
        """
        Initialize vault with encryption key
        
        Args:
            key: Raw 32-byte encryption key
            key_path: Path to key file (will create if not exists)
        """
        if key is not None:
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
            self._key = key
        elif key_path is not None:
            self._key = self._load_or_create_key(key_path)
        else:
            # Generate random key (WARNING: key will be lost on restart)
            self._key = self.generate_key()
            logger.warning("Using ephemeral key - evidence will not be decryptable after restart!")
        
        self.aesgcm = AESGCM(self._key)
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit encryption key"""
        return os.urandom(SecureVault.KEY_SIZE)
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2
        Returns: (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(SecureVault.SALT_SIZE)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=SecureVault.KEY_SIZE,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    def _load_or_create_key(self, key_path: str) -> bytes:
        """Load key from file or create new one"""
        path = Path(key_path)
        
        if path.exists():
            with open(path, 'rb') as f:
                key = f.read()
            
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Invalid key file: expected {self.KEY_SIZE} bytes")
            
            logger.info(f"Loaded encryption key from {key_path}")
            return key
        
        # Create new key
        key = self.generate_key()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (owner read/write only)
        try:
            os.chmod(path, 0o600)
        except:
            pass  # Windows may not support chmod
        
        logger.info(f"Generated new encryption key: {key_path}")
        logger.warning("BACKUP THIS KEY FILE! Without it, evidence cannot be decrypted.")
        
        return key
    
    def save_key(self, output_path: str):
        """Save current key to file"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(self._key)
        
        try:
            os.chmod(path, 0o600)
        except:
            pass
        
        logger.info(f"Saved encryption key: {output_path}")
    
    def lock_evidence(self, raw_bytes: bytes, metadata: Optional[dict] = None) -> EncryptedPackage:
        """
        Encrypt evidence with integrity protection
        
        The process:
        1. Compute SHA-256 hash of original data
        2. Combine hash + separator + data
        3. Encrypt with AES-GCM (provides authenticated encryption)
        
        Args:
            raw_bytes: Raw evidence data (e.g., video frame bytes)
            metadata: Optional metadata to include
            
        Returns:
            EncryptedPackage with all necessary data for decryption
        """
        # 1. Compute integrity hash
        original_hash = hashlib.sha256(raw_bytes).hexdigest()
        
        # 2. Create payload: hash + separator + data
        separator = b"::"
        payload = original_hash.encode('utf-8') + separator + raw_bytes
        
        # 3. Generate unique nonce
        nonce = os.urandom(self.NONCE_SIZE)
        
        # 4. Encrypt with AES-GCM
        # GCM mode provides both confidentiality and integrity (auth tag)
        ciphertext = self.aesgcm.encrypt(nonce, payload, associated_data=None)
        
        return EncryptedPackage(
            nonce=nonce,
            ciphertext=ciphertext,
            original_hash=original_hash,
            timestamp=datetime.now().timestamp(),
            metadata=metadata or {}
        )
    
    def unlock_evidence(self, package: EncryptedPackage) -> Tuple[bytes, str]:
        """
        Decrypt and verify evidence integrity
        
        Args:
            package: EncryptedPackage from lock_evidence
            
        Returns:
            (original_data, hash) if successful
            
        Raises:
            ValueError: If decryption fails or integrity check fails
        """
        try:
            # Decrypt
            payload = self.aesgcm.decrypt(package.nonce, package.ciphertext, associated_data=None)
        except Exception as e:
            raise ValueError(f"Decryption failed - evidence may have been tampered with: {e}")
        
        # Split payload
        separator = b"::"
        try:
            sep_index = payload.index(separator)
            stored_hash = payload[:sep_index].decode('utf-8')
            original_data = payload[sep_index + len(separator):]
        except (ValueError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid payload format - evidence may have been tampered with: {e}")
        
        # Verify integrity
        computed_hash = hashlib.sha256(original_data).hexdigest()
        
        if computed_hash != stored_hash:
            msg = (
                f"AUDIT WARNING: INTEGRITY CHECK FAILED for evidence package!\n"
                f"Expected: {stored_hash} | Computed: {computed_hash}"
            )
            logger.warning(msg)
            raise ValueError(msg)
        
        logger.info("AUDIT: Evidence integrity verified successfully")
        return original_data, stored_hash
    
    def save_encrypted_file(self, data: bytes, output_path: str, metadata: Optional[dict] = None):
        """
        Encrypt and save data to file
        
        File format:
        - 12 bytes: nonce
        - 8 bytes: timestamp (double)
        - 4 bytes: metadata length
        - N bytes: metadata (JSON)
        - Rest: ciphertext
        """
        import json
        import struct
        
        package = self.lock_evidence(data, metadata)
        
        # Serialize metadata
        meta_json = json.dumps(package.metadata).encode('utf-8')
        
        with open(output_path, 'wb') as f:
            # Write header
            f.write(package.nonce)                          # 12 bytes
            f.write(struct.pack('d', package.timestamp))    # 8 bytes
            f.write(struct.pack('I', len(meta_json)))       # 4 bytes
            f.write(meta_json)                              # Variable
            f.write(package.ciphertext)                     # Rest
        
        logger.debug(f"Saved encrypted evidence: {output_path}")
    
    def load_encrypted_file(self, input_path: str) -> Tuple[bytes, dict]:
        """
        Load and decrypt file
        
        Returns:
            (decrypted_data, metadata)
        """
        import json
        import struct
        
        with open(input_path, 'rb') as f:
            # Read header
            nonce = f.read(self.NONCE_SIZE)
            timestamp = struct.unpack('d', f.read(8))[0]
            meta_len = struct.unpack('I', f.read(4))[0]
            meta_json = f.read(meta_len)
            ciphertext = f.read()
        
        metadata = json.loads(meta_json.decode('utf-8'))
        
        package = EncryptedPackage(
            nonce=nonce,
            ciphertext=ciphertext,
            original_hash="",  # Will be verified during decryption
            timestamp=timestamp,
            metadata=metadata
        )
        
        data, _ = self.unlock_evidence(package)
        return data, metadata


class EvidenceManager:
    """
    High-level evidence management for video frames
    Handles buffering and file rotation
    """
    
    def __init__(self, vault: SecureVault, output_dir: str):
        self.vault = vault
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._buffer = []
        self._buffer_start_time = None
        self._file_count = 0
    
    def add_frame(self, frame_bytes: bytes, detections: list, timestamp: float):
        """Add frame to buffer"""
        if self._buffer_start_time is None:
            self._buffer_start_time = timestamp
        
        self._buffer.append({
            "frame": frame_bytes,
            "detections": [
                {"x1": d.x1, "y1": d.y1, "x2": d.x2, "y2": d.y2, "conf": d.confidence}
                for d in detections
            ],
            "timestamp": timestamp
        })
    
    def flush(self, force: bool = False):
        """Flush buffer to encrypted file"""
        if not self._buffer:
            return None
        
        import pickle
        
        # Serialize buffer data
        data = pickle.dumps(self._buffer)
        
        # Generate filename
        dt = datetime.fromtimestamp(self._buffer_start_time)
        filename = f"evidence_{dt.strftime('%Y%m%d_%H%M%S')}_{self._file_count:04d}.enc"
        filepath = self.output_dir / filename
        
        # Save encrypted
        metadata = {
            "frame_count": len(self._buffer),
            "start_time": self._buffer_start_time,
            "end_time": self._buffer[-1]["timestamp"]
        }
        
        self.vault.save_encrypted_file(data, str(filepath), metadata)
        
        # Clear buffer
        self._buffer = []
        self._buffer_start_time = None
        self._file_count += 1
        
        logger.info(f"Saved encrypted evidence: {filename}")
        return str(filepath)


class HybridVault:
    """
    Hybrid RSA+AES encryption vault
    
    Uses RSA to encrypt per-file AES session key,
    then AES-256-GCM for actual data encryption.
    
    File format:
    - 8 bytes: Magic "HYBRID1\x00"
    - 256 bytes: RSA-encrypted session key
    - 12 bytes: Nonce
    - 8 bytes: Timestamp
    - 4 bytes: Metadata length
    - N bytes: Metadata JSON
    - Rest: AES-GCM ciphertext
    """
    
    MAGIC = b"HYBRID1\x00"
    NONCE_SIZE = 12
    RSA_ENCRYPTED_KEY_SIZE = 256  # For RSA-2048
    
    def __init__(
        self,
        public_key_path: Optional[str] = None,
        private_key_path: Optional[str] = None,
        private_key_password: Optional[str] = None
    ):
        """
        Initialize hybrid vault
        
        Args:
            public_key_path: Path to RSA public key (for encryption)
            private_key_path: Path to RSA private key (for decryption)
            private_key_password: Password for encrypted private key
        """
        from modules.rsa_crypto import load_public_key, load_private_key
        
        self._public_key = None
        self._private_key = None
        
        if public_key_path:
            self._public_key = load_public_key(public_key_path)
            logger.info(f"Loaded RSA public key from {public_key_path}")
        
        if private_key_path:
            self._private_key = load_private_key(private_key_path, private_key_password)
            logger.info(f"Loaded RSA private key from {private_key_path}")
    
    def lock_evidence(self, raw_bytes: bytes, metadata: Optional[dict] = None) -> bytes:
        """
        Encrypt evidence using hybrid RSA+AES
        
        Args:
            raw_bytes: Data to encrypt
            metadata: Optional metadata dict
            
        Returns:
            Complete encrypted package as bytes (ready to write to file)
        """
        if self._public_key is None:
            raise ValueError("Public key required for encryption")
        
        from modules.rsa_crypto import encrypt_session_key
        import json
        import struct
        
        # 1. Generate random AES session key
        session_key = os.urandom(32)  # AES-256
        
        # 2. Encrypt session key with RSA
        encrypted_session_key = encrypt_session_key(session_key, self._public_key)
        
        # 3. Create AES-GCM cipher with session key
        aesgcm = AESGCM(session_key)
        
        # 4. Compute integrity hash and create payload
        original_hash = hashlib.sha256(raw_bytes).hexdigest()
        separator = b"::"
        payload = original_hash.encode('utf-8') + separator + raw_bytes
        
        # 5. Encrypt with AES-GCM
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, payload, associated_data=None)
        
        # 6. Build file format
        timestamp = datetime.now().timestamp()
        meta_json = json.dumps(metadata or {}).encode('utf-8')
        
        result = bytearray()
        result.extend(self.MAGIC)                              # 8 bytes
        result.extend(encrypted_session_key)                   # 256 bytes
        result.extend(nonce)                                   # 12 bytes
        result.extend(struct.pack('d', timestamp))             # 8 bytes
        result.extend(struct.pack('I', len(meta_json)))        # 4 bytes
        result.extend(meta_json)                               # Variable
        result.extend(ciphertext)                              # Rest
        
        return bytes(result)
    
    def unlock_evidence(self, encrypted_data: bytes) -> Tuple[bytes, dict]:
        """
        Decrypt evidence using hybrid RSA+AES
        
        Args:
            encrypted_data: Complete encrypted package bytes
            
        Returns:
            (decrypted_data, metadata)
        """
        if self._private_key is None:
            raise ValueError("Private key required for decryption")
        
        from modules.rsa_crypto import decrypt_session_key
        import json
        import struct
        
        # 1. Verify magic
        if encrypted_data[:8] != self.MAGIC:
            raise ValueError("Invalid file format - not a hybrid encrypted file")
        
        offset = 8
        
        # 2. Extract RSA-encrypted session key
        encrypted_session_key = encrypted_data[offset:offset + self.RSA_ENCRYPTED_KEY_SIZE]
        offset += self.RSA_ENCRYPTED_KEY_SIZE
        
        # 3. Decrypt session key with RSA private key
        try:
            session_key = decrypt_session_key(encrypted_session_key, self._private_key)
        except Exception as e:
            raise ValueError(f"Failed to decrypt session key - wrong private key? {e}")
        
        # 4. Extract nonce
        nonce = encrypted_data[offset:offset + self.NONCE_SIZE]
        offset += self.NONCE_SIZE
        
        # 5. Extract timestamp
        timestamp = struct.unpack('d', encrypted_data[offset:offset + 8])[0]
        offset += 8
        
        # 6. Extract metadata
        meta_len = struct.unpack('I', encrypted_data[offset:offset + 4])[0]
        offset += 4
        meta_json = encrypted_data[offset:offset + meta_len]
        offset += meta_len
        metadata = json.loads(meta_json.decode('utf-8'))
        
        # 7. Extract and decrypt ciphertext
        ciphertext = encrypted_data[offset:]
        
        aesgcm = AESGCM(session_key)
        
        try:
            payload = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        except Exception as e:
            raise ValueError(f"Decryption failed - evidence may have been tampered with: {e}")
        
        # 8. Verify integrity
        separator = b"::"
        try:
            sep_index = payload.index(separator)
            stored_hash = payload[:sep_index].decode('utf-8')
            original_data = payload[sep_index + len(separator):]
        except (ValueError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid payload format - evidence may have been tampered with: {e}")
        
        computed_hash = hashlib.sha256(original_data).hexdigest()
        
        if computed_hash != stored_hash:
            raise ValueError(
                f"INTEGRITY CHECK FAILED!\n"
                f"Expected hash: {stored_hash}\n"
                f"Computed hash: {computed_hash}\n"
                f"Evidence has been tampered with!"
            )
        
        return original_data, metadata
    
    def save_encrypted_file(self, data: bytes, output_path: str, metadata: Optional[dict] = None):
        """Encrypt and save data to file"""
        encrypted = self.lock_evidence(data, metadata)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        logger.debug(f"Saved hybrid-encrypted evidence: {output_path}")
    
    def load_encrypted_file(self, input_path: str) -> Tuple[bytes, dict]:
        """Load and decrypt file"""
        with open(input_path, 'rb') as f:
            encrypted_data = f.read()
        
        return self.unlock_evidence(encrypted_data)
    
    @staticmethod
    def is_hybrid_format(filepath: str) -> bool:
        """Check if file is hybrid encrypted format"""
        try:
            with open(filepath, 'rb') as f:
                magic = f.read(8)
            return magic == HybridVault.MAGIC
        except:
            return False


def create_vault_from_env() -> SecureVault:
    """Create vault from environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    key_path = os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key")
    return SecureVault(key_path=key_path)


def create_hybrid_vault_from_env(for_encryption: bool = True) -> HybridVault:
    """
    Create hybrid vault from environment variables
    
    Args:
        for_encryption: If True, load public key. If False, load private key.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    public_key_path = os.getenv("RSA_PUBLIC_KEY_PATH", "keys/rsa_public.pem")
    private_key_path = os.getenv("RSA_PRIVATE_KEY_PATH", "keys/rsa_private.pem")
    
    if for_encryption:
        return HybridVault(public_key_path=public_key_path)
    else:
        return HybridVault(private_key_path=private_key_path)


# Test code
if __name__ == "__main__":
    # Test encryption/decryption
    vault = SecureVault()
    
    # Test data
    test_data = b"This is secret video frame data for forensic evidence"
    
    print("Original data:", test_data[:50], "...")
    print("Original hash:", hashlib.sha256(test_data).hexdigest())
    
    # Encrypt
    package = vault.lock_evidence(test_data, {"camera": "CAM01"})
    print("\nEncrypted successfully")
    print("Nonce:", package.nonce.hex())
    print("Ciphertext length:", len(package.ciphertext))
    
    # Decrypt
    decrypted, hash_val = vault.unlock_evidence(package)
    print("\nDecrypted successfully")
    print("Decrypted data:", decrypted[:50], "...")
    print("Verified hash:", hash_val)
    
    # Test tampering detection
    print("\n--- Testing Tamper Detection ---")
    tampered = EncryptedPackage(
        nonce=package.nonce,
        ciphertext=package.ciphertext[:-1] + bytes([package.ciphertext[-1] ^ 1]),  # Flip one bit
        original_hash=package.original_hash,
        timestamp=package.timestamp,
        metadata=package.metadata
    )
    
    try:
        vault.unlock_evidence(tampered)
        print("ERROR: Tamper detection failed!")
    except ValueError as e:
        print("SUCCESS: Tampering detected!")
        print(str(e)[:100])
