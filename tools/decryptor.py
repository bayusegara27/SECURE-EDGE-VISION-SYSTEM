"""
Evidence Decryptor Tool
CLI tool for decrypting and playing encrypted evidence files
For authorized personnel only (Forensic Investigation)
"""

import os
import sys
import pickle
import argparse
import getpass
from pathlib import Path
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.security import SecureVault, HybridVault


def print_banner():
    """Print tool banner"""
    print("=" * 60)
    print("  🔐 SECURE EDGE VISION - EVIDENCE DECRYPTOR")
    print("  For Authorized Personnel Only")
    print("=" * 60)
    print()


def list_evidence_files(evidence_dir: str) -> list:
    """List all encrypted evidence files"""
    path = Path(evidence_dir)
    if not path.exists():
        return []
    
    files = []
    # Search recursively for .enc files in subdirectories (cam0, cam1, etc.)
    for f in sorted(path.rglob("*.enc"), reverse=True):
        stat = f.stat()
        files.append({
            "path": str(f),
            "filename": f.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime)
        })
    
    return files


def decrypt_and_play(
    filepath: str,
    key_path: str,
    private_key_path: str = None,
    output_video: Optional[str] = None,
    show_boxes: bool = True
):
    """Decrypt evidence file and play/export the video
    
    Args:
        filepath: Path to encrypted evidence file
        key_path: Path to symmetric key (for legacy files)
        private_key_path: Path to RSA private key (for hybrid files)
        output_video: Optional output path for MP4 export
        show_boxes: Whether to draw detection boxes (default: True)
    """
    print(f"\n🔓 Decrypting: {filepath}")
    print("-" * 50)
    
    # Auto-detect file format
    is_hybrid = HybridVault.is_hybrid_format(filepath)
    
    if is_hybrid:
        print("🔐 Format: Hybrid RSA+AES encryption")
        if not private_key_path:
            private_key_path = "keys/rsa_private.pem"
            print(f"   Using default private key: {private_key_path}")
        
        try:
            vault = HybridVault(private_key_path=private_key_path)
            print("✓ RSA private key loaded")
        except Exception as e:
            print(f"✗ Failed to load private key: {e}")
            print("\n⚠️  Private key is required to decrypt hybrid-encrypted files!")
            print("   Use: --private-key <path_to_private_key.pem>")
            return False
    else:
        print("🔑 Format: Symmetric AES encryption (legacy)")
        try:
            vault = SecureVault(key_path=key_path)
            print("✓ Symmetric encryption key loaded")
        except Exception as e:
            print(f"✗ Failed to load key: {e}")
            return False
    
    # Decrypt file
    try:
        data, metadata = vault.load_encrypted_file(filepath)
        print("✓ File decrypted and integrity verified")
        print(f"  Frames: {metadata.get('frame_count', 'unknown')}")
        print(f"  Start: {datetime.fromtimestamp(metadata.get('start_time', 0))}")
        print(f"  End: {datetime.fromtimestamp(metadata.get('end_time', 0))}")
    except ValueError as e:
        print(f"\n❌ DECRYPTION FAILED!")
        print(f"   {e}")
        print("\n⚠️  This evidence file may have been tampered with!")
        return False
    except Exception as e:
        print(f"✗ Error decrypting: {e}")
        return False
    
    # Deserialize frames
    try:
        frames_data = pickle.loads(data)
        print(f"✓ Deserialized {len(frames_data)} frames")
    except Exception as e:
        print(f"✗ Failed to deserialize: {e}")
        return False
    
    # Option to export to video file
    if output_video:
        print(f"\n📁 Exporting to: {output_video}")
        if not show_boxes:
            print("   Detection boxes: DISABLED")
        export_to_video(frames_data, output_video, show_boxes=show_boxes)
        print("✓ Export complete")
        return True
    
    # Play video
    print("\n🎬 Playing evidence video...")
    print("   Press 'Q' to quit, SPACE to pause")
    if not show_boxes:
        print("   Detection boxes: DISABLED")
    
    play_frames(frames_data, show_boxes=show_boxes)
    
    return True


def export_to_video(frames_data: list, output_path: str, fps: int = 30, show_boxes: bool = True):
    """Export frames to MP4 video
    
    Args:
        frames_data: List of frame data dicts
        output_path: Output MP4 file path
        fps: Frames per second
        show_boxes: Whether to draw detection boxes
    """
    if not frames_data:
        return
    
    # Decode first frame to get dimensions
    first_frame = cv2.imdecode(
        np.frombuffer(frames_data[0]["frame_jpg"], np.uint8),
        cv2.IMREAD_COLOR
    )
    h, w = first_frame.shape[:2]
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    for frame_data in frames_data:
        frame = cv2.imdecode(
            np.frombuffer(frame_data["frame_jpg"], np.uint8),
            cv2.IMREAD_COLOR
        )
        
        # Draw detection boxes on original (if enabled)
        if show_boxes:
            for det in frame_data.get("detections", []):
                x1, y1 = det["x1"], det["y1"]
                x2, y2 = det["x2"], det["y2"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"Face {det.get('confidence', 0):.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1
                )
        
        writer.write(frame)
    
    writer.release()


def play_frames(frames_data: list, show_boxes: bool = True):
    """Play frames with optional detection boxes
    
    Args:
        frames_data: List of frame data dicts
        show_boxes: Whether to draw detection boxes
    """
    window_name = "Evidence Playback - CONFIDENTIAL"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    paused = False
    frame_idx = 0
    
    while frame_idx < len(frames_data):
        frame_data = frames_data[frame_idx]
        
        # Decode JPEG
        frame = cv2.imdecode(
            np.frombuffer(frame_data["frame_jpg"], np.uint8),
            cv2.IMREAD_COLOR
        )
        
        # Draw detection boxes (if enabled)
        if show_boxes:
            for det in frame_data.get("detections", []):
                x1, y1 = det["x1"], det["y1"]
                x2, y2 = det["x2"], det["y2"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"Face {det.get('confidence', 0):.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1
                )
        
        # Draw info overlay
        timestamp = datetime.fromtimestamp(frame_data.get("timestamp", 0))
        cv2.putText(
            frame,
            f"Frame: {frame_idx + 1}/{len(frames_data)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        cv2.putText(
            frame,
            f"Time: {timestamp.strftime('%H:%M:%S.%f')[:-3]}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        cv2.putText(
            frame,
            "CONFIDENTIAL EVIDENCE",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )
        
        cv2.imshow(window_name, frame)
        
        key = cv2.waitKey(33 if not paused else 0) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('n') or (not paused):
            frame_idx += 1
        elif key == ord('p') and frame_idx > 0:
            frame_idx -= 1
    
    cv2.destroyAllWindows()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Decrypt and play encrypted evidence files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python decryptor.py --list
  python decryptor.py --file evidence_20241231_120000_0001.enc
  python decryptor.py --file evidence.enc --export output.mp4
        """
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available evidence files"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Evidence file to decrypt (.enc)"
    )
    
    parser.add_argument(
        "--key", "-k",
        type=str,
        default="keys/master.key",
        help="Path to symmetric encryption key file (default: keys/master.key)"
    )
    
    parser.add_argument(
        "--private-key", "-p",
        type=str,
        default=None,
        help="Path to RSA private key for hybrid-encrypted files (default: keys/rsa_private.pem)"
    )
    
    parser.add_argument(
        "--evidence-dir", "-d",
        type=str,
        default="recordings/evidence",
        help="Evidence directory (default: recordings/evidence)"
    )
    
    parser.add_argument(
        "--export", "-e",
        type=str,
        help="Export to MP4 file instead of playing"
    )
    
    parser.add_argument(
        "--no-boxes",
        action="store_true",
        help="Disable detection box overlays in output video"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if args.list:
        files = list_evidence_files(args.evidence_dir)
        if not files:
            print("No evidence files found.")
        else:
            print(f"Found {len(files)} evidence file(s):\n")
            for i, f in enumerate(files, 1):
                print(f"  {i}. {f['filename']}")
                print(f"     Size: {f['size_mb']} MB")
                print(f"     Created: {f['created']}")
                print()
        return
    
    if args.file:
        # Find file
        filepath = Path(args.file)
        if not filepath.exists():
            filepath = Path(args.evidence_dir) / args.file
        
        if not filepath.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        
        # Decrypt and play/export
        success = decrypt_and_play(
            str(filepath),
            args.key,
            args.private_key,
            args.export,
            show_boxes=not args.no_boxes
        )
        
        sys.exit(0 if success else 1)
    
    # Interactive mode
    files = list_evidence_files(args.evidence_dir)
    
    if not files:
        print("No evidence files found in", args.evidence_dir)
        print("Run the main system first to generate evidence files.")
        return
    
    print(f"Available evidence files ({len(files)}):\n")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f['filename']} ({f['size_mb']} MB)")
    
    print("\n  [0] Exit\n")
    
    try:
        choice = int(input("Select file number: "))
        
        if choice == 0:
            print("Exiting.")
            return
        
        if 1 <= choice <= len(files):
            selected = files[choice - 1]
            decrypt_and_play(selected["path"], args.key)
        else:
            print("Invalid selection.")
            
    except KeyboardInterrupt:
        print("\nExiting.")
    except ValueError:
        print("Invalid input.")


if __name__ == "__main__":
    main()
