#!/usr/bin/env python3
"""
Minimal test to isolate segfault cause
"""
import sys
print("Starting import test...")

print("1. Importing numpy...")
try:
    import numpy as np
    print(f"   ✅ NumPy {np.__version__}")
except Exception as e:
    print(f"   ❌ NumPy failed: {e}")
    sys.exit(1)

print("2. Importing cv2...")
try:
    import cv2
    print(f"   ✅ OpenCV {cv2.__version__}")
except Exception as e:
    print(f"   ❌ OpenCV failed: {e}")
    sys.exit(1)

print("3. Importing PIL...")
try:
    from PIL import Image
    print("   ✅ PIL imported successfully")
except Exception as e:
    print(f"   ❌ PIL failed: {e}")
    sys.exit(1)

print("4. Importing dlib...")
try:
    import dlib
    print("   ✅ dlib imported successfully")
except Exception as e:
    print(f"   ❌ dlib failed: {e}")
    sys.exit(1)

print("5. Importing face_recognition...")
try:
    import face_recognition
    print("   ✅ face_recognition imported successfully")
except Exception as e:
    print(f"   ❌ face_recognition failed: {e}")
    sys.exit(1)

print("All imports successful!")
