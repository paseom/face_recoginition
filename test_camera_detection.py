#!/usr/bin/env python3
"""
Test script untuk camera detection
"""

from utils.camera_detector import CameraDetector
from config.settings import Settings


def test_camera_detection():
    """Test camera detection"""
    print("\n=== Camera Detection Test ===\n")
    
    # Test 1: List available cameras
    print("1. Scanning available cameras...")
    available = CameraDetector.get_available_cameras()
    print(f"   Found {len(available)} camera(s): {available}\n")
    
    # Test 2: Find USB camera
    print("2. Finding USB camera (excluding built-in)...")
    usb_idx = CameraDetector.find_usb_camera(exclude_builtin=True)
    if usb_idx != -1:
        print(f"   USB camera found at index {usb_idx}\n")
    else:
        print("   No USB camera found\n")
    
    # Test 3: Print detailed info
    print("3. Camera details:")
    CameraDetector.print_camera_info()
    print()
    
    # Test 4: Test settings auto-detection
    print("4. Settings auto-detection:")
    settings = Settings()
    camera_idx = settings.get_camera_index()
    print(f"   CAMERA_AUTO_DETECT: {settings.CAMERA_AUTO_DETECT}")
    print(f"   PREFER_USB_CAMERA: {settings.PREFER_USB_CAMERA}")
    print(f"   Selected camera index: {camera_idx}\n")
    
    # Test 5: Validate selected camera
    print("5. Validating selected camera...")
    is_valid = CameraDetector.validate_camera(camera_idx)
    if is_valid:
        print(f"   ✓ Camera {camera_idx} is valid and can be opened\n")
    else:
        print(f"   ✗ Camera {camera_idx} cannot be opened\n")


if __name__ == "__main__":
    test_camera_detection()
