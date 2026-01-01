"""
Unit Tests for Security Module
Tests encryption, decryption, and tamper detection
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.security import SecureVault, EncryptedPackage


class TestSecureVault:
    """Test cases for SecureVault"""
    
    def test_key_generation(self):
        """Test random key generation"""
        key = SecureVault.generate_key()
        assert len(key) == 32
        assert isinstance(key, bytes)
    
    def test_key_uniqueness(self):
        """Test that generated keys are unique"""
        key1 = SecureVault.generate_key()
        key2 = SecureVault.generate_key()
        assert key1 != key2
    
    def test_password_key_derivation(self):
        """Test password-based key derivation"""
        password = "test_password_123"
        key, salt = SecureVault.derive_key_from_password(password)
        
        assert len(key) == 32
        assert len(salt) == 16
        
        # Same password + salt should give same key
        key2, _ = SecureVault.derive_key_from_password(password, salt)
        assert key == key2
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption/decryption roundtrip"""
        vault = SecureVault()
        
        test_data = b"This is secret video frame data"
        
        package = vault.lock_evidence(test_data)
        decrypted, hash_val = vault.unlock_evidence(package)
        
        assert decrypted == test_data
        assert len(hash_val) == 64  # SHA-256 hex
    
    def test_different_data_different_ciphertext(self):
        """Test that different data produces different ciphertext"""
        vault = SecureVault()
        
        data1 = b"Data 1"
        data2 = b"Data 2"
        
        pkg1 = vault.lock_evidence(data1)
        pkg2 = vault.lock_evidence(data2)
        
        assert pkg1.ciphertext != pkg2.ciphertext
    
    def test_same_data_different_nonce(self):
        """Test that same data with different nonce produces different ciphertext"""
        vault = SecureVault()
        
        data = b"Same data"
        
        pkg1 = vault.lock_evidence(data)
        pkg2 = vault.lock_evidence(data)
        
        assert pkg1.nonce != pkg2.nonce
        assert pkg1.ciphertext != pkg2.ciphertext
    
    def test_tamper_detection_ciphertext(self):
        """Test that modifying ciphertext is detected"""
        vault = SecureVault()
        
        data = b"Original data"
        package = vault.lock_evidence(data)
        
        # Modify ciphertext
        tampered = EncryptedPackage(
            nonce=package.nonce,
            ciphertext=package.ciphertext[:-1] + bytes([package.ciphertext[-1] ^ 1]),
            original_hash=package.original_hash,
            timestamp=package.timestamp,
            metadata=package.metadata
        )
        
        with pytest.raises(ValueError, match="tampered"):
            vault.unlock_evidence(tampered)
    
    def test_tamper_detection_nonce(self):
        """Test that modifying nonce causes decryption failure"""
        vault = SecureVault()
        
        data = b"Original data"
        package = vault.lock_evidence(data)
        
        # Modify nonce
        tampered = EncryptedPackage(
            nonce=bytes([package.nonce[0] ^ 1]) + package.nonce[1:],
            ciphertext=package.ciphertext,
            original_hash=package.original_hash,
            timestamp=package.timestamp,
            metadata=package.metadata
        )
        
        with pytest.raises(ValueError):
            vault.unlock_evidence(tampered)
    
    def test_file_save_load(self):
        """Test saving and loading encrypted files"""
        vault = SecureVault()
        
        test_data = b"Video frame data for file test"
        metadata = {"camera": "CAM01", "frame_count": 100}
        
        with tempfile.NamedTemporaryFile(suffix=".enc", delete=False) as f:
            filepath = f.name
        
        try:
            vault.save_encrypted_file(test_data, filepath, metadata)
            
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > len(test_data)
            
            loaded_data, loaded_meta = vault.load_encrypted_file(filepath)
            
            assert loaded_data == test_data
            assert loaded_meta == metadata
            
        finally:
            os.unlink(filepath)
    
    def test_key_file_creation(self):
        """Test key file creation and loading"""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "test.key")
            
            # Create vault with new key file
            vault1 = SecureVault(key_path=key_path)
            
            assert os.path.exists(key_path)
            
            # Load same key
            vault2 = SecureVault(key_path=key_path)
            
            # Both should decrypt same data
            data = b"Test data"
            package = vault1.lock_evidence(data)
            decrypted, _ = vault2.unlock_evidence(package)
            
            assert decrypted == data
    
    def test_wrong_key_fails(self):
        """Test that wrong key cannot decrypt"""
        vault1 = SecureVault()
        vault2 = SecureVault()  # Different key
        
        data = b"Secret data"
        package = vault1.lock_evidence(data)
        
        with pytest.raises(ValueError):
            vault2.unlock_evidence(package)
    
    def test_large_data(self):
        """Test encryption of large data"""
        vault = SecureVault()
        
        # 1MB of random data
        large_data = os.urandom(1024 * 1024)
        
        package = vault.lock_evidence(large_data)
        decrypted, _ = vault.unlock_evidence(package)
        
        assert decrypted == large_data
    
    def test_empty_data(self):
        """Test encryption of empty data"""
        vault = SecureVault()
        
        empty_data = b""
        
        package = vault.lock_evidence(empty_data)
        decrypted, _ = vault.unlock_evidence(package)
        
        assert decrypted == empty_data


class TestRSACrypto:
    """Test cases for RSA cryptography module"""
    
    def test_rsa_key_generation(self):
        """Test RSA key pair generation"""
        from modules.rsa_crypto import generate_rsa_keypair
        
        private_key, public_key = generate_rsa_keypair()
        
        assert private_key is not None
        assert public_key is not None
    
    def test_rsa_key_save_load(self):
        """Test saving and loading RSA keys"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            save_private_key,
            save_public_key,
            load_private_key,
            load_public_key
        )
        
        private_key, public_key = generate_rsa_keypair()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pub_path = os.path.join(tmpdir, "public.pem")
            priv_path = os.path.join(tmpdir, "private.pem")
            
            save_public_key(public_key, pub_path)
            save_private_key(private_key, priv_path)
            
            assert os.path.exists(pub_path)
            assert os.path.exists(priv_path)
            
            loaded_pub = load_public_key(pub_path)
            loaded_priv = load_private_key(priv_path)
            
            assert loaded_pub is not None
            assert loaded_priv is not None
    
    def test_session_key_encryption(self):
        """Test session key encryption/decryption with RSA"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            encrypt_session_key,
            decrypt_session_key
        )
        
        private_key, public_key = generate_rsa_keypair()
        
        session_key = os.urandom(32)  # AES-256 key
        
        encrypted = encrypt_session_key(session_key, public_key)
        assert len(encrypted) == 256  # RSA-2048 output
        
        decrypted = decrypt_session_key(encrypted, private_key)
        assert decrypted == session_key
    
    def test_wrong_private_key_fails(self):
        """Test that wrong private key cannot decrypt"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            encrypt_session_key,
            decrypt_session_key
        )
        
        priv1, pub1 = generate_rsa_keypair()
        priv2, pub2 = generate_rsa_keypair()
        
        session_key = os.urandom(32)
        encrypted = encrypt_session_key(session_key, pub1)
        
        with pytest.raises(Exception):
            decrypt_session_key(encrypted, priv2)


class TestHybridVault:
    """Test cases for HybridVault (RSA+AES)"""
    
    def test_hybrid_encrypt_decrypt(self):
        """Test hybrid encryption/decryption roundtrip"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            save_private_key,
            save_public_key
        )
        from modules.security import HybridVault
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pub_path = os.path.join(tmpdir, "public.pem")
            priv_path = os.path.join(tmpdir, "private.pem")
            
            private_key, public_key = generate_rsa_keypair()
            save_public_key(public_key, pub_path)
            save_private_key(private_key, priv_path)
            
            vault = HybridVault(public_key_path=pub_path, private_key_path=priv_path)
            
            test_data = b"Hybrid encrypted video frame data"
            metadata = {"camera": "CAM01", "type": "hybrid_test"}
            
            encrypted = vault.lock_evidence(test_data, metadata)
            
            # Check magic bytes
            assert encrypted[:8] == b"HYBRID1\x00"
            
            decrypted, meta = vault.unlock_evidence(encrypted)
            
            assert decrypted == test_data
            assert meta == metadata
    
    def test_hybrid_file_save_load(self):
        """Test hybrid vault file operations"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            save_private_key,
            save_public_key
        )
        from modules.security import HybridVault
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pub_path = os.path.join(tmpdir, "public.pem")
            priv_path = os.path.join(tmpdir, "private.pem")
            enc_path = os.path.join(tmpdir, "test.enc")
            
            private_key, public_key = generate_rsa_keypair()
            save_public_key(public_key, pub_path)
            save_private_key(private_key, priv_path)
            
            vault = HybridVault(public_key_path=pub_path, private_key_path=priv_path)
            
            test_data = b"Test data for file operations"
            metadata = {"test": True}
            
            vault.save_encrypted_file(test_data, enc_path, metadata)
            
            assert os.path.exists(enc_path)
            assert HybridVault.is_hybrid_format(enc_path)
            
            loaded_data, loaded_meta = vault.load_encrypted_file(enc_path)
            
            assert loaded_data == test_data
            assert loaded_meta == metadata
    
    def test_hybrid_tamper_detection(self):
        """Test that tampering is detected in hybrid encrypted data"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            save_private_key,
            save_public_key
        )
        from modules.security import HybridVault
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pub_path = os.path.join(tmpdir, "public.pem")
            priv_path = os.path.join(tmpdir, "private.pem")
            
            private_key, public_key = generate_rsa_keypair()
            save_public_key(public_key, pub_path)
            save_private_key(private_key, priv_path)
            
            vault = HybridVault(public_key_path=pub_path, private_key_path=priv_path)
            
            test_data = b"Original secure data"
            encrypted = vault.lock_evidence(test_data)
            
            # Tamper with ciphertext
            tampered = bytearray(encrypted)
            tampered[-10] ^= 1
            
            with pytest.raises(ValueError, match="tampered|Decryption failed"):
                vault.unlock_evidence(bytes(tampered))
    
    def test_hybrid_format_detection(self):
        """Test format detection between symmetric and hybrid"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            save_private_key,
            save_public_key
        )
        from modules.security import HybridVault, SecureVault
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pub_path = os.path.join(tmpdir, "public.pem")
            priv_path = os.path.join(tmpdir, "private.pem")
            hybrid_file = os.path.join(tmpdir, "hybrid.enc")
            symmetric_file = os.path.join(tmpdir, "symmetric.enc")
            
            # Create hybrid file
            private_key, public_key = generate_rsa_keypair()
            save_public_key(public_key, pub_path)
            save_private_key(private_key, priv_path)
            
            hybrid_vault = HybridVault(public_key_path=pub_path, private_key_path=priv_path)
            hybrid_vault.save_encrypted_file(b"hybrid data", hybrid_file)
            
            # Create symmetric file
            symmetric_vault = SecureVault()
            symmetric_vault.save_encrypted_file(b"symmetric data", symmetric_file)
            
            # Test detection
            assert HybridVault.is_hybrid_format(hybrid_file) == True
            assert HybridVault.is_hybrid_format(symmetric_file) == False
    
    def test_hybrid_large_data(self):
        """Test hybrid encryption of large data"""
        from modules.rsa_crypto import (
            generate_rsa_keypair,
            save_private_key,
            save_public_key
        )
        from modules.security import HybridVault
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pub_path = os.path.join(tmpdir, "public.pem")
            priv_path = os.path.join(tmpdir, "private.pem")
            
            private_key, public_key = generate_rsa_keypair()
            save_public_key(public_key, pub_path)
            save_private_key(private_key, priv_path)
            
            vault = HybridVault(public_key_path=pub_path, private_key_path=priv_path)
            
            # 1MB of random data
            large_data = os.urandom(1024 * 1024)
            
            encrypted = vault.lock_evidence(large_data)
            decrypted, _ = vault.unlock_evidence(encrypted)
            
            assert decrypted == large_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

