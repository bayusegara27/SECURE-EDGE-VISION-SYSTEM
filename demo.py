"""
Demo Script - Secure Edge Vision System
Tests all components with beautiful output
"""

import os
import sys
import time
import logging
from pathlib import Path

# Disable logging noise
logging.disable(logging.WARNING)

import cv2
import numpy as np

# Project root
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


# Colors for terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_banner():
    """Print beautiful banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗███████╗ ██████╗██╗   ██╗██████╗ ███████╗          ║
║   ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝          ║
║   ███████╗█████╗  ██║     ██║   ██║██████╔╝█████╗            ║
║   ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝            ║
║   ███████║███████╗╚██████╗╚██████╔╝██║  ██║███████╗          ║
║   ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝          ║
║                                                              ║
║   ███████╗██████╗  ██████╗ ███████╗                          ║
║   ██╔════╝██╔══██╗██╔════╝ ██╔════╝                          ║
║   █████╗  ██║  ██║██║  ███╗█████╗                            ║
║   ██╔══╝  ██║  ██║██║   ██║██╔══╝                            ║
║   ███████╗██████╔╝╚██████╔╝███████╗                          ║
║   ╚══════╝╚═════╝  ╚═════╝ ╚══════╝                          ║
║                                                              ║
║   {Colors.YELLOW}Real-time Video Anonymization System{Colors.CYAN}                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}"""
    print(banner)


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.CYAN}┌{'─' * 58}┐{Colors.END}")
    print(f"{Colors.CYAN}│{Colors.END} {Colors.BOLD}{title:<56}{Colors.END} {Colors.CYAN}│{Colors.END}")
    print(f"{Colors.CYAN}└{'─' * 58}┘{Colors.END}")


def print_success(text: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✓{Colors.END} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"  {Colors.RED}✗{Colors.END} {text}")


def print_info(text: str):
    """Print info message"""
    print(f"  {Colors.CYAN}→{Colors.END} {text}")


def test_camera() -> bool:
    """Test camera capture"""
    print_section("Camera")
    
    source = os.getenv("CAMERA_SOURCES", "0")
    source = int(source) if source.isdigit() else source
    
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print_error(f"Cannot open camera: {source}")
        return False
    
    ret, frame = cap.read()
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap.release()
    
    if ret:
        print_success(f"Camera opened: {source}")
        print_info(f"Resolution: {width}x{height} @ {fps}fps")
        return True
    else:
        print_error("Cannot capture frame")
        return False


def test_gpu() -> bool:
    """Test GPU availability"""
    print_section("GPU (CUDA)")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            cuda_ver = torch.version.cuda
            
            print_success(f"CUDA Available")
            print_info(f"GPU: {gpu_name}")
            print_info(f"Memory: {gpu_memory:.1f} GB")
            print_info(f"CUDA: {cuda_ver}")
            return True
        else:
            print_warning("CUDA not available - Using CPU")
            return True
            
    except ImportError:
        print_warning("PyTorch not installed")
        return True


def test_detection() -> bool:
    """Test YOLO detection"""
    print_section("AI Model (YOLOv8)")
    
    try:
        from ultralytics import YOLO
        import torch
        
        # Check for face model
        if os.path.exists("models/model.pt"):
            model_path = "models/model.pt"
            model_type = "Face Detection"
        else:
            model_path = "yolov8n.pt"
            model_type = "Object Detection"
        
        model = YOLO(model_path)
        print_success(f"Model loaded: {model_type}")
        print_info(f"Path: {model_path}")
        
        # Test detection
        source = os.getenv("CAMERA_SOURCES", "0")
        source = int(source) if source.isdigit() else source
        
        cap = cv2.VideoCapture(source)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            start = time.time()
            results = model.predict(frame, device=device, verbose=False)
            elapsed = (time.time() - start) * 1000
            
            detections = len(results[0].boxes) if results else 0
            print_success(f"Detection test passed")
            print_info(f"Found {detections} object(s) in {elapsed:.0f}ms")
        
        return True
        
    except Exception as e:
        print_error(f"Detection error: {e}")
        return False


def test_security() -> bool:
    """Test encryption/decryption"""
    print_section("Security (AES-256-GCM)")
    
    try:
        from modules.security import SecureVault, EncryptedPackage
        
        vault = SecureVault()
        test_data = b"Secret video frame data for forensic evidence"
        
        # Encrypt
        package = vault.lock_evidence(test_data)
        print_success("Encryption working")
        print_info(f"Original: {len(test_data)} bytes → Encrypted: {len(package.ciphertext)} bytes")
        
        # Decrypt
        decrypted, _ = vault.unlock_evidence(package)
        if decrypted == test_data:
            print_success("Decryption verified")
        
        # Tamper test
        tampered = EncryptedPackage(
            nonce=package.nonce,
            ciphertext=package.ciphertext[:-1] + bytes([package.ciphertext[-1] ^ 1]),
            original_hash=package.original_hash,
            timestamp=package.timestamp,
            metadata=package.metadata
        )
        
        try:
            vault.unlock_evidence(tampered)
            print_error("Tamper detection FAILED!")
            return False
        except ValueError:
            print_success("Tamper detection working")
        
        return True
        
    except Exception as e:
        print_error(f"Security error: {e}")
        return False


def test_blur_live() -> bool:
    """Test face blurring with live video"""
    print_section("Live Face Blur")
    
    try:
        from modules.processor import FrameProcessor
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        processor = FrameProcessor(device=device)
        
        if not processor.load_model():
            print_error("Failed to load model")
            return False
        
        info = processor.get_info()
        print_success(f"Model: {'Face' if info.get('is_face_model') else 'Person'} detection")
        print_info(f"Device: {device.upper()}")
        
        # Open camera
        source = os.getenv("CAMERA_SOURCES", "0")
        source = int(source) if source.isdigit() else source
        
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print_error("Cannot open camera")
            return False
        
        print()
        print(f"  {Colors.YELLOW}Starting live preview...{Colors.END}")
        print(f"  {Colors.YELLOW}Press Q to stop{Colors.END}")
        
        frame_count = 0
        fps_start = time.time()
        current_fps = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process
            start = time.time()
            blurred, raw, detections = processor.process(frame)
            proc_time = (time.time() - start) * 1000
            
            # FPS
            frame_count += 1
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                current_fps = frame_count / elapsed
                frame_count = 0
                fps_start = time.time()
            
            # Draw overlay
            h, w = blurred.shape[:2]
            
            # Semi-transparent header
            overlay = blurred.copy()
            cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
            blurred = cv2.addWeighted(overlay, 0.5, blurred, 0.5, 0)
            
            # Stats
            cv2.putText(blurred, f"FPS: {current_fps:.1f}", (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(blurred, f"Faces: {len(detections)}", (20, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(blurred, f"Latency: {proc_time:.0f}ms", (20, 95),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Device badge
            cv2.putText(blurred, device.upper(), (w - 80, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            
            # Privacy notice
            cv2.putText(blurred, "PRIVACY PROTECTED", (w//2 - 100, h - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
            
            cv2.imshow("Secure Edge Vision - Live Preview (Q to quit)", blurred)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print()
        print_success("Live blur test completed")
        return True
        
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results: dict):
    """Print test summary"""
    print(f"\n{Colors.CYAN}{'═' * 60}{Colors.END}")
    print(f"{Colors.BOLD}  TEST SUMMARY{Colors.END}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.END}\n")
    
    all_passed = True
    for name, passed in results.items():
        if passed:
            print(f"  {Colors.GREEN}✓{Colors.END} {name}")
        else:
            print(f"  {Colors.RED}✗{Colors.END} {name}")
            all_passed = False
    
    print()
    if all_passed:
        print(f"  {Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}")
        print(f"\n  {Colors.CYAN}Next steps:{Colors.END}")
        print(f"    python main.py")
        print(f"    Open: http://localhost:8000")
    else:
        print(f"  {Colors.YELLOW}⚠ Some tests failed{Colors.END}")
    
    print()


def run_all_tests():
    """Run all component tests"""
    print_banner()
    
    results = {
        "Camera": test_camera(),
        "GPU": test_gpu(),
        "AI Model": test_detection(),
        "Security": test_security(),
        "Live Blur": test_blur_live()
    }
    
    print_summary(results)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure Edge Vision - Tests")
    parser.add_argument("--cameras", "-c", action="store_true", help="List cameras")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick test")
    parser.add_argument("--camera", type=str, help="Camera index/URL")
    
    args = parser.parse_args()
    
    if args.camera:
        os.environ["CAMERA_SOURCES"] = args.camera
    
    if args.cameras:
        from tools.camera_selector import list_available_cameras
        print_section("Available Cameras")
        cameras = list_available_cameras()
        for cam in cameras:
            print_info(f"[{cam['index']}] {cam['resolution']} @ {cam['fps']}fps")
        return
    
    if args.quick:
        print_banner()
        results = {
            "Camera": test_camera(),
            "GPU": test_gpu(),
            "AI Model": test_detection(),
            "Security": test_security()
        }
        print_summary(results)
        return
    
    run_all_tests()


if __name__ == "__main__":
    main()
