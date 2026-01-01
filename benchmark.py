"""
Performance Benchmark Script
Measures latency, FPS, GPU utilization for thesis documentation (BAB 5)
"""

import os
import sys
import time
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Add project root
sys.path.insert(0, str(Path(__file__).parent))


class BenchmarkResult:
    """Stores benchmark results"""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.fps_samples: List[float] = []
        self.gpu_utilizations: List[float] = []
        self.detection_times: List[float] = []
        self.blur_times: List[float] = []
        self.frame_counts: List[int] = []
    
    def add_sample(self, latency: float, fps: float, gpu_util: float,
                   detection_time: float, blur_time: float, detection_count: int):
        self.latencies.append(latency)
        self.fps_samples.append(fps)
        self.gpu_utilizations.append(gpu_util)
        self.detection_times.append(detection_time)
        self.blur_times.append(blur_time)
        self.frame_counts.append(detection_count)
    
    def summary(self) -> Dict:
        """Get statistical summary"""
        def stats(data):
            if not data:
                return {"min": 0, "max": 0, "avg": 0, "std": 0}
            arr = np.array(data)
            return {
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "avg": float(np.mean(arr)),
                "std": float(np.std(arr))
            }
        
        return {
            "latency_ms": stats(self.latencies),
            "fps": stats(self.fps_samples),
            "gpu_utilization": stats(self.gpu_utilizations),
            "detection_time_ms": stats(self.detection_times),
            "blur_time_ms": stats(self.blur_times),
            "detections_per_frame": stats(self.frame_counts)
        }


def get_gpu_utilization() -> float:
    """Get GPU utilization percentage"""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        return float(result.stdout.strip())
    except:
        return 0.0


def run_benchmark(duration_seconds: int = 60, warmup_seconds: int = 5) -> BenchmarkResult:
    """
    Run performance benchmark
    
    Args:
        duration_seconds: How long to run the benchmark
        warmup_seconds: Warmup period before measuring
    
    Returns:
        BenchmarkResult with all measurements
    """
    print("\n" + "=" * 60)
    print("  PERFORMANCE BENCHMARK")
    print("  For Thesis Documentation (BAB 5)")
    print("=" * 60)
    
    result = BenchmarkResult()
    
    # Initialize components
    print("\nInitializing...")
    
    # Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return result
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("Camera: OK")
    
    # YOLO model
    try:
        from ultralytics import YOLO
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = YOLO("yolov8n.pt")
        
        # Warm up model
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        model.predict(dummy, device=device, verbose=False)
        
        print(f"YOLO: OK ({device})")
        if device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
    except Exception as e:
        print(f"ERROR: Cannot load model - {e}")
        cap.release()
        return result
    
    blur_intensity = int(os.getenv("BLUR_INTENSITY", "51"))
    if blur_intensity % 2 == 0:
        blur_intensity += 1
    
    # Warmup phase
    print(f"\nWarmup ({warmup_seconds}s)...")
    warmup_start = time.time()
    while time.time() - warmup_start < warmup_seconds:
        ret, frame = cap.read()
        if ret:
            model.predict(frame, device=device, verbose=False)
    
    # Benchmark phase
    print(f"Benchmarking ({duration_seconds}s)...")
    print("Progress: ", end="", flush=True)
    
    start_time = time.time()
    frame_count = 0
    fps_frame_count = 0
    fps_start = time.time()
    
    while time.time() - start_time < duration_seconds:
        frame_start = time.time()
        
        # Capture
        ret, frame = cap.read()
        if not ret:
            continue
        
        capture_time = time.time()
        
        # Detection
        results = model.predict(
            frame, device=device, conf=0.5, classes=[0], verbose=False
        )
        
        detection_time = time.time()
        
        # Process detections and apply blur
        detection_count = 0
        blurred = frame.copy()
        
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    
                    # Face estimation
                    height = y2 - y1
                    face_y2 = y1 + int(height * 0.3)
                    
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, face_y2 = min(w, x2), min(h, face_y2)
                    
                    if x2 > x1 and face_y2 > y1:
                        roi = blurred[y1:face_y2, x1:x2]
                        blurred_roi = cv2.GaussianBlur(roi, (blur_intensity, blur_intensity), 0)
                        blurred[y1:face_y2, x1:x2] = blurred_roi
                        detection_count += 1
        
        blur_time = time.time()
        
        # Calculate metrics
        total_latency = (blur_time - frame_start) * 1000  # ms
        det_time = (detection_time - capture_time) * 1000
        bl_time = (blur_time - detection_time) * 1000
        
        # FPS calculation
        fps_frame_count += 1
        if time.time() - fps_start >= 1.0:
            current_fps = fps_frame_count / (time.time() - fps_start)
            gpu_util = get_gpu_utilization()
            
            result.add_sample(
                latency=total_latency,
                fps=current_fps,
                gpu_util=gpu_util,
                detection_time=det_time,
                blur_time=bl_time,
                detection_count=detection_count
            )
            
            fps_frame_count = 0
            fps_start = time.time()
        
        frame_count += 1
        
        # Progress indicator
        elapsed = time.time() - start_time
        progress = int((elapsed / duration_seconds) * 20)
        print(f"\rProgress: [{'=' * progress}{' ' * (20 - progress)}] {int(elapsed)}s/{duration_seconds}s", end="", flush=True)
    
    print("\n")
    
    cap.release()
    
    return result


def save_results(result: BenchmarkResult, output_path: str):
    """Save results to CSV file"""
    summary = result.summary()
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(["Metric", "Min", "Max", "Average", "Std Dev"])
        
        # Data
        for metric, data in summary.items():
            writer.writerow([
                metric,
                f"{data['min']:.2f}",
                f"{data['max']:.2f}",
                f"{data['avg']:.2f}",
                f"{data['std']:.2f}"
            ])
    
    print(f"Results saved to: {output_path}")


def print_results(result: BenchmarkResult):
    """Print results in formatted table"""
    summary = result.summary()
    
    print("=" * 70)
    print("  BENCHMARK RESULTS")
    print("=" * 70)
    print(f"{'Metric':<25} {'Min':<10} {'Max':<10} {'Avg':<10} {'Std':<10}")
    print("-" * 70)
    
    metric_names = {
        "latency_ms": "Latency (ms)",
        "fps": "FPS",
        "gpu_utilization": "GPU Usage (%)",
        "detection_time_ms": "Detection (ms)",
        "blur_time_ms": "Blur (ms)",
        "detections_per_frame": "Detections/Frame"
    }
    
    for key, name in metric_names.items():
        data = summary[key]
        print(f"{name:<25} {data['min']:<10.2f} {data['max']:<10.2f} {data['avg']:<10.2f} {data['std']:<10.2f}")
    
    print("=" * 70)
    
    # Thesis-ready summary
    lat = summary["latency_ms"]
    fps = summary["fps"]
    gpu = summary["gpu_utilization"]
    
    print("\n📊 Summary for Thesis (BAB 5):")
    print(f"   • Average Latency: {lat['avg']:.1f}ms (Target: <500ms) {'✓' if lat['avg'] < 500 else '✗'}")
    print(f"   • Average FPS: {fps['avg']:.1f} (Target: 25-30) {'✓' if fps['avg'] >= 25 else '✗'}")
    print(f"   • GPU Utilization: {gpu['avg']:.1f}%")
    print(f"   • Total Samples: {len(result.latencies)}")


def main():
    """Main benchmark entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="📈 Performance Benchmark Tool - Secure Edge CCTV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔥 COMMON WORKFLOWS & EXAMPLES:

1. Run Standard 1-Minute Benchmark:
   python benchmark.py

2. Run Quick 10-Second Test (for debugging):
   python benchmark.py --duration 10

3. Run Detailed 5-Minute Stress Test:
   python benchmark.py --duration 300 --warmup 10

4. Save Results to a Specific File:
   python benchmark.py --output tests/my_report.csv

💡 These results are formatted for direct inclusion in Chapter 5 (Results) of your thesis.
        """
    )
    parser.add_argument("-d", "--duration", type=int, default=60, help="Benchmark duration (seconds)")
    parser.add_argument("-w", "--warmup", type=int, default=5, help="Warmup duration (seconds)")
    parser.add_argument("-o", "--output", type=str, help="Output CSV file path")
    
    args = parser.parse_args()
    
    # Run benchmark
    result = run_benchmark(
        duration_seconds=args.duration,
        warmup_seconds=args.warmup
    )
    
    if not result.latencies:
        print("Benchmark failed - no results")
        return 1
    
    # Print results
    print_results(result)
    
    # Save to file
    if args.output:
        save_results(result, args.output)
    else:
        # Default output
        output_dir = Path("recordings")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"benchmark_{timestamp}.csv"
        save_results(result, str(output_path))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
