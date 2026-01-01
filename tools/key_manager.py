"""
Key Manager - Encryption Key Management Utility
Generates, backs up, and manages the master encryption key
"""

import os
import sys
import shutil
import hashlib
import getpass
from pathlib import Path
from datetime import datetime

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def get_key_path() -> Path:
    """Get encryption key path from environment"""
    return Path(os.getenv("ENCRYPTION_KEY_PATH", "keys/master.key"))


def get_rsa_public_key_path() -> Path:
    """Get RSA public key path from environment"""
    return Path(os.getenv("RSA_PUBLIC_KEY_PATH", "keys/rsa_public.pem"))


def get_rsa_private_key_path() -> Path:
    """Get RSA private key path from environment"""
    return Path(os.getenv("RSA_PRIVATE_KEY_PATH", "keys/rsa_private.pem"))


def generate_key(force: bool = False) -> bool:
    """
    Generate new encryption key
    
    Args:
        force: Overwrite existing key if True
    """
    from modules.security import SecureVault
    
    key_path = get_key_path()
    
    if key_path.exists() and not force:
        print(f"❌ Key already exists: {key_path}")
        print("   Use --force to overwrite (WARNING: existing evidence will be unreadable!)")
        return False
    
    # Ensure directory exists
    key_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate new key
    vault = SecureVault()  # Generates new key
    vault.save_key(str(key_path))
    
    print(f"✓ Key generated: {key_path}")
    print(f"  Size: 32 bytes (256-bit)")
    print(f"  Hash: {hashlib.sha256(key_path.read_bytes()).hexdigest()[:16]}...")
    print()
    print("⚠️  IMPORTANT: Backup this key immediately!")
    print("   Without it, encrypted evidence cannot be recovered.")
    
    return True


def backup_key(backup_path: str = None) -> bool:
    """
    Backup encryption key to safe location
    
    Args:
        backup_path: Custom backup path (optional)
    """
    key_path = get_key_path()
    
    if not key_path.exists():
        print(f"❌ Key not found: {key_path}")
        print("   Run: python tools/key_manager.py --generate")
        return False
    
    # Default backup location
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("keys/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"master_{timestamp}.key"
    else:
        backup_path = Path(backup_path)
    
    # Copy key
    shutil.copy2(key_path, backup_path)
    
    # Verify copy
    original_hash = hashlib.sha256(key_path.read_bytes()).hexdigest()
    backup_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()
    
    if original_hash == backup_hash:
        print(f"✓ Key backed up to: {backup_path}")
        print(f"  Hash verified: {backup_hash[:16]}...")
        return True
    else:
        print("❌ Backup verification failed!")
        return False


def restore_key(backup_path: str) -> bool:
    """
    Restore encryption key from backup
    
    Args:
        backup_path: Path to backup key file
    """
    backup = Path(backup_path)
    
    if not backup.exists():
        print(f"❌ Backup not found: {backup_path}")
        return False
    
    key_path = get_key_path()
    
    # Confirm overwrite
    if key_path.exists():
        print(f"⚠️  Current key will be overwritten: {key_path}")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return False
    
    # Ensure directory
    key_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Restore
    shutil.copy2(backup, key_path)
    
    # Verify
    backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
    restored_hash = hashlib.sha256(key_path.read_bytes()).hexdigest()
    
    if backup_hash == restored_hash:
        print(f"✓ Key restored from: {backup_path}")
        print(f"  Hash verified: {restored_hash[:16]}...")
        return True
    else:
        print("❌ Restore verification failed!")
        return False


def show_key_info():
    """Display key information"""
    key_path = get_key_path()
    
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ ENCRYPTION KEY INFORMATION                             │")
    print("└────────────────────────────────────────────────────────┘\n")
    
    if not key_path.exists():
        print(f"  Status: ❌ NOT FOUND")
        print(f"  Path: {key_path}")
        print()
        print("  To generate a new key:")
        print("    python tools/key_manager.py --generate")
        return
    
    # Key info
    key_data = key_path.read_bytes()
    key_hash = hashlib.sha256(key_data).hexdigest()
    created = datetime.fromtimestamp(key_path.stat().st_mtime)
    
    print(f"  Status: ✓ ACTIVE")
    print(f"  Path: {key_path}")
    print(f"  Size: {len(key_data)} bytes ({len(key_data) * 8}-bit)")
    print(f"  SHA-256: {key_hash[:32]}...")
    print(f"  Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check backups
    backup_dir = Path("keys/backups")
    if backup_dir.exists():
        backups = list(backup_dir.glob("*.key"))
        print(f"\n  Backups: {len(backups)} found")
        for b in backups[-3:]:  # Show last 3
            print(f"    → {b.name}")
    else:
        print("\n  Backups: None")
        print("    Run: python tools/key_manager.py --backup")
    
    print()


def generate_rsa_keys(force: bool = False, password: str = None) -> bool:
    """
    Generate RSA key pair for hybrid encryption
    
    Args:
        force: Overwrite existing keys if True
        password: Optional password to protect private key
    """
    from modules.rsa_crypto import (
        generate_rsa_keypair,
        save_private_key,
        save_public_key,
        get_key_fingerprint
    )
    
    pub_path = get_rsa_public_key_path()
    priv_path = get_rsa_private_key_path()
    
    if (pub_path.exists() or priv_path.exists()) and not force:
        print(f"❌ RSA keys already exist:")
        print(f"   Public: {pub_path}")
        print(f"   Private: {priv_path}")
        print("   Use --force to overwrite (WARNING: existing hybrid-encrypted files need these keys!)")
        return False
    
    # Generate key pair
    private_key, public_key = generate_rsa_keypair()
    
    # Save keys
    pub_path.parent.mkdir(parents=True, exist_ok=True)
    save_public_key(public_key, str(pub_path))
    save_private_key(private_key, str(priv_path), password)
    
    fingerprint = get_key_fingerprint(public_key)
    
    print(f"✓ RSA key pair generated:")
    print(f"  📤 Public key: {pub_path}")
    print(f"  🔐 Private key: {priv_path}")
    print(f"  Fingerprint: {fingerprint}...")
    print(f"  Key size: 2048 bits")
    print()
    print("⚠️  IMPORTANT:")
    print("   • Public key: Used for ENCRYPTION (can be shared)")
    print("   • Private key: Used for DECRYPTION (keep SECURE and BACKUP!)")
    print("   • Private key can be stored offline for maximum security")
    
    if password:
        print("   • Private key is password-protected")
    
    return True


def show_rsa_key_info():
    """Display RSA key information"""
    from modules.rsa_crypto import load_public_key, get_key_fingerprint
    
    pub_path = get_rsa_public_key_path()
    priv_path = get_rsa_private_key_path()
    
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ RSA KEY PAIR INFORMATION (Hybrid Encryption)           │")
    print("└────────────────────────────────────────────────────────┘\n")
    
    if not pub_path.exists() and not priv_path.exists():
        print(f"  Status: ❌ NOT FOUND")
        print()
        print("  To generate RSA keys:")
        print("    python tools/key_manager.py --generate-rsa")
        return
    
    # Public key info
    print("  📤 PUBLIC KEY (for encryption):")
    if pub_path.exists():
        try:
            public_key = load_public_key(str(pub_path))
            fingerprint = get_key_fingerprint(public_key)
            created = datetime.fromtimestamp(pub_path.stat().st_mtime)
            
            print(f"     Status: ✓ AVAILABLE")
            print(f"     Path: {pub_path}")
            print(f"     Fingerprint: {fingerprint}...")
            print(f"     Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"     Status: ❌ ERROR - {e}")
    else:
        print(f"     Status: ❌ NOT FOUND")
        print(f"     Path: {pub_path}")
    
    print()
    
    # Private key info
    print("  🔐 PRIVATE KEY (for decryption):")
    if priv_path.exists():
        created = datetime.fromtimestamp(priv_path.stat().st_mtime)
        size = priv_path.stat().st_size
        
        print(f"     Status: ✓ AVAILABLE")
        print(f"     Path: {priv_path}")
        print(f"     Size: {size} bytes")
        print(f"     Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"     Status: ❌ NOT FOUND (needed for decryption)")
        print(f"     Path: {priv_path}")
    
    print()


def export_key_secure(password: str = None) -> bool:
    """
    Export key with password protection
    
    Args:
        password: Password to encrypt the key (prompted if not provided)
    """
    from modules.security import SecureVault
    import base64
    
    key_path = get_key_path()
    
    if not key_path.exists():
        print(f"❌ Key not found: {key_path}")
        return False
    
    # Get password
    if password is None:
        password = getpass.getpass("Enter export password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌ Passwords do not match!")
            return False
    
    # Create password-protected export
    vault = SecureVault()
    vault.derive_key_from_password(password)
    
    # Encrypt the master key with password-derived key
    key_data = key_path.read_bytes()
    package = vault.lock_evidence(key_data, {"type": "master_key_export"})
    
    # Save export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = Path(f"keys/exports/master_{timestamp}.enc")
    export_path.parent.mkdir(parents=True, exist_ok=True)
    
    vault.save_encrypted_file(key_data, str(export_path), {"type": "master_key"})
    
    print(f"✓ Key exported (password-protected): {export_path}")
    print("  Keep the password safe - you'll need it to restore!")
    
    return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🔐 Encryption Key Manager - Secure Edge CCTV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔥 COMMON WORKFLOWS & EXAMPLES:

1. Setup Symmetric Encryption (Standard):
   python tools/key_manager.py --generate

2. Setup Hybrid Encryption (Pro/Forensic) with PIN:
   python tools/key_manager.py --generate-rsa
   # (Follow the prompt to set a PIN, e.g., 1234)

3. Generate RSA Key with PIN via CLI (Non-interactive):
   python tools/key_manager.py --generate-rsa --pin 1234 --force

4. Backup Your Keys (Do this often!):
   python tools/key_manager.py --backup

5. Restore from a Specific Backup:
   python tools/key_manager.py --restore keys/backups/master_20260101_120000.key

6. Export Protected Master Key (For off-site storage):
   python tools/key_manager.py --export

7. Check All Key Statuses & Fingerprints:
   python tools/key_manager.py
        """
    )
    
    parser.add_argument("--generate", "-g", action="store_true",
                       help="Generate new symmetric encryption key (AES)")
    parser.add_argument("--generate-rsa", action="store_true",
                       help="Generate RSA key pair for hybrid encryption")
    parser.add_argument("--pin", type=str,
                       help="Password/PIN for RSA private key (will prompt if omitted)")
    parser.add_argument("--rsa-info", action="store_true",
                       help="Show RSA key pair information")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Force overwrite existing key")
    parser.add_argument("--backup", "-b", action="store_true",
                       help="Backup current key")
    parser.add_argument("--restore", "-r", type=str, metavar="PATH",
                       help="Restore key from backup")
    parser.add_argument("--export", "-e", action="store_true",
                       help="Export key with password protection")
    
    args = parser.parse_args()
    
    if args.generate:
        generate_key(force=args.force)
    elif args.generate_rsa:
        pin = args.pin
        if pin is None:
            choice = input("Protect private key with a PIN/Password? (y/n): ").lower()
            if choice == 'y':
                import getpass
                pin = getpass.getpass("Enter Private Key PIN: ")
                confirm = getpass.getpass("Confirm Private Key PIN: ")
                if pin != confirm:
                    print("❌ PINs do not match!")
                    return
            
        generate_rsa_keys(force=args.force, password=pin)
    elif args.rsa_info:
        show_rsa_key_info()
    elif args.backup:
        backup_key()
    elif args.restore:
        restore_key(args.restore)
    elif args.export:
        export_key_secure()
    else:
        show_key_info()
        show_rsa_key_info()


if __name__ == "__main__":
    main()
