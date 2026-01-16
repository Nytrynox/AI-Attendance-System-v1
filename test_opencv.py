#!/usr/bin/env python3
"""
Test OpenCV installation and functionality
"""
import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")
print()

# Test basic imports
try:
    import numpy as np
    print(f"✅ NumPy version: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

try:
    import cv2
    print(f"✅ OpenCV version: {cv2.__version__}")
    print(f"✅ VideoCapture available: {hasattr(cv2, 'VideoCapture')}")
    
    # Test VideoCapture creation
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            print("✅ Camera can be initialized")
            cap.release()
        else:
            print("⚠️  Camera initialization failed")
    except Exception as e:
        print(f"❌ VideoCapture test failed: {e}")
        
except ImportError as e:
    print(f"❌ OpenCV import failed: {e}")

print("\nTesting simple camera initialization without backend specification...")
try:
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("✅ Basic camera initialization works")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Frame capture works: {frame.shape}")
        else:
            print("⚠️  Frame capture failed")
        cap.release()
    else:
        print("❌ Basic camera initialization failed")
except Exception as e:
    print(f"❌ Basic camera test failed: {e}")
