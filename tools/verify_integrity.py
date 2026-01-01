"""
Integrity Verification Script
Demonstrates tamper detection for evidence files (for thesis defense demo)
"""

import os
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def demonstrate_tamper_detection():
    """
    Demonstrates that evidence files cannot be tampered with
    This is a key security feature for the thesis
    """
    from modules.security import SecureVault
    
    print("\n" + "=" * 60)
    print("  TAMPER DETECTION DEMONSTRATION")
    print("  For Thesis Defense (Sidang)")
    print("=" * 60)
    
    # Create vault
    vault = SecureVault()
    
    # Create test evidence data
    test_data = b"This represents a video frame containing sensitive evidence data. " * 100
    
    print(f"\n1. Original Data Size: {len(test_data)} bytes")
    
    # Encrypt
    print("\n2. Encrypting evidence...")
    package = vault.lock_evidence(test_data, {"camera": "CAM01", "type": "demo"})
    print(f"   Ciphertext size: {len(package.ciphertext)} bytes")
    print(f"   Original hash: {package.original_hash[:32]}...")
    
    # Verify normal decryption works
    print("\n3. Verifying normal decryption...")
    decrypted, hash_val = vault.unlock_evidence(package)
    assert decrypted == test_data
    print("   ✓ Decryption successful, data matches!")
    
    # Demonstrate tamper detection
    print("\n" + "-" * 60)
    print("  TAMPERING SIMULATION")
    print("-" * 60)
    
    from modules.security import EncryptedPackage
    
    # Test 1: Modify single byte in ciphertext
    print("\n4. Test 1: Modifying 1 byte in ciphertext...")
    
    modified_ct = bytearray(package.ciphertext)
    original_byte = modified_ct[50]
    modified_ct[50] = (modified_ct[50] + 1) % 256
    
    tampered1 = EncryptedPackage(
        nonce=package.nonce,
        ciphertext=bytes(modified_ct),
        original_hash=package.original_hash,
        timestamp=package.timestamp,
        metadata=package.metadata
    )
    
    try:
        vault.unlock_evidence(tampered1)
        print("   ✗ FAILED - Tampering not detected!")
    except ValueError as e:
        print("   ✓ DETECTED! Decryption failed as expected")
        print(f"   Error: {str(e)[:80]}...")
    
    # Test 2: Modify nonce
    print("\n5. Test 2: Modifying nonce...")
    
    modified_nonce = bytearray(package.nonce)
    modified_nonce[0] = (modified_nonce[0] + 1) % 256
    
    tampered2 = EncryptedPackage(
        nonce=bytes(modified_nonce),
        ciphertext=package.ciphertext,
        original_hash=package.original_hash,
        timestamp=package.timestamp,
        metadata=package.metadata
    )
    
    try:
        vault.unlock_evidence(tampered2)
        print("   ✗ FAILED - Tampering not detected!")
    except ValueError as e:
        print("   ✓ DETECTED! Decryption failed as expected")
    
    # Test 3: Add extra bytes
    print("\n6. Test 3: Appending data to ciphertext...")
    
    tampered3 = EncryptedPackage(
        nonce=package.nonce,
        ciphertext=package.ciphertext + b"EXTRA",
        original_hash=package.original_hash,
        timestamp=package.timestamp,
        metadata=package.metadata
    )
    
    try:
        vault.unlock_evidence(tampered3)
        print("   ✗ FAILED - Tampering not detected!")
    except ValueError as e:
        print("   ✓ DETECTED! Decryption failed as expected")
    
    # Test 4: Truncate ciphertext
    print("\n7. Test 4: Truncating ciphertext...")
    
    tampered4 = EncryptedPackage(
        nonce=package.nonce,
        ciphertext=package.ciphertext[:-10],
        original_hash=package.original_hash,
        timestamp=package.timestamp,
        metadata=package.metadata
    )
    
    try:
        vault.unlock_evidence(tampered4)
        print("   ✗ FAILED - Tampering not detected!")
    except ValueError as e:
        print("   ✓ DETECTED! Decryption failed as expected")
    
    # Test 5: Using wrong key
    print("\n8. Test 5: Using wrong encryption key...")
    
    wrong_vault = SecureVault()  # New vault with different key
    
    try:
        wrong_vault.unlock_evidence(package)
        print("   ✗ FAILED - Wrong key accepted!")
    except ValueError as e:
        print("   ✓ DETECTED! Wrong key rejected")
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print("""
    The AES-256-GCM encryption provides:
    
    1. CONFIDENTIALITY: Data is encrypted and unreadable without key
    2. INTEGRITY: Any modification is detected via authentication tag
    3. AUTHENTICITY: Only the correct key can decrypt
    
    This proves that evidence files:
    - Cannot be read without the master key
    - Cannot be modified without detection
    - Cannot be forged by attackers
    
    Answer for thesis defense:
    "Sistem menggunakan AES-256-GCM yang merupakan Authenticated Encryption.
     Mode GCM menghasilkan authentication tag yang terverifikasi saat dekripsi.
     Jika file dimodifikasi walau 1 bit, dekripsi akan gagal."
    """)


def test_file_integrity():
    """Test integrity with actual file operations"""
    import tempfile
    from modules.security import SecureVault
    
    print("\n" + "=" * 60)
    print("  FILE-LEVEL INTEGRITY TEST")
    print("=" * 60)
    
    vault = SecureVault()
    
    # Create test evidence
    test_data = os.urandom(10000)  # 10KB random data
    
    with tempfile.NamedTemporaryFile(suffix=".enc", delete=False) as f:
        filepath = f.name
    
    print(f"\n1. Saving encrypted file: {filepath}")
    vault.save_encrypted_file(test_data, filepath, {"test": True})
    print(f"   File size: {os.path.getsize(filepath)} bytes")
    
    print("\n2. Loading and verifying...")
    loaded, meta = vault.load_encrypted_file(filepath)
    assert loaded == test_data
    print("   ✓ File loaded and verified successfully")
    
    print("\n3. Tampering with file...")
    with open(filepath, 'r+b') as f:
        f.seek(100)  # Go to middle
        original = f.read(1)
        f.seek(100)
        f.write(bytes([(original[0] + 1) % 256]))  # Flip one byte
    print("   Modified 1 byte at position 100")
    
    print("\n4. Attempting to load tampered file...")
    try:
        vault.load_encrypted_file(filepath)
        print("   ✗ FAILED - Tampering not detected!")
    except ValueError as e:
        print("   ✓ DETECTED! File tampering rejected")
        print(f"   Error: {str(e)[:60]}...")
    
    # Cleanup
    os.unlink(filepath)
    print("\n5. Test file cleaned up")


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(
        description="🛡️ Forensic Integrity Verification Tool - Secure Edge CCTV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔥 COMMON WORKFLOWS & EXAMPLES:

1. Run Full Security Demo (Recommended for Sidang):
   python tools/verify_integrity.py --demo

2. Run File-Level Tamper Test:
   python tools/verify_integrity.py --test-file

3. Verify a Specific Encrypted File:
   python tools/verify_integrity.py --verify recordings/evidence/evidence_20260101.enc

💡 This tool proves the 'Integrity' pillar of your cybersecurity thesis.
   If even 1 bit of evidence is altered, decryption will fail!
        """
    )
    parser.add_argument("--demo", action="store_true", help="Run tampering detection demo")
    parser.add_argument("--test-file", action="store_true", help="Run file-level integrity tests")
    parser.add_argument("--verify", type=str, metavar="PATH", help="Verify integrity of a specific file")
    
    args = parser.parse_args()
    
    if args.demo:
        demonstrate_tamper_detection()
    elif args.test_file:
        test_file_integrity()
    elif args.verify:
        from modules.security import SecureVault
        vault = SecureVault()
        try:
            vault.load_encrypted_file(args.verify)
            print(f"✓ {args.verify}: Integrity Verified (SUCCESS)")
        except Exception as e:
            print(f"✗ {args.verify}: Tampering Detected or Invalid Key! (ERROR)")
            print(f"  Details: {e}")
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
