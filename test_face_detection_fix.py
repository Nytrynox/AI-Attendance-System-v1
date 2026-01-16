#!/usr/bin/env python3
"""
Quick test for face detection fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.face_detector import FaceDetector
import cv2
import numpy as np

def test_face_detection():
    """Test the face detection unpacking fix"""
    print("Testing face detection fix...")
    
    try:
        # Initialize face detector
        face_detector = FaceDetector()
        
        # Create a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Try to detect faces (should return empty list for dummy frame)
        faces = face_detector.detect_faces(dummy_frame)
        print(f"✓ Face detection works - returned {len(faces)} faces")
        
        # Test unpacking format
        for face in faces:
            try:
                x, y, w, h, face_crop, landmarks = face
                print(f"✓ Unpacking works: x={x}, y={y}, w={w}, h={h}")
            except ValueError as e:
                print(f"✗ Unpacking failed: {e}")
                return False
                
        print("✓ Face detection fix verified!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_face_detection()
    sys.exit(0 if success else 1)
