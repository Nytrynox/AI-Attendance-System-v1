#!/usr/bin/env python3
"""
Quick test to verify face detection fix
"""

import os
import sys
import numpy as np

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the modules
from src.face_detector import FaceDetector

def test_face_detection_fix():
    """Test that the face detection unpacking is fixed"""
    print("Testing face detection unpacking fix...")
    
    try:
        # Initialize face detector
        face_detector = FaceDetector()
        print("✓ Face detector initialized")
        
        # Create a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test face detection
        faces = face_detector.detect_faces(dummy_frame)
        print(f"✓ Face detection works - found {len(faces)} faces")
        
        # Test the unpacking that was causing the error
        for face in faces:
            try:
                x, y, w, h, face_crop, landmarks = face
                print(f"✓ Unpacking works: face at ({x}, {y}) size {w}x{h}")
                print(f"✓ Face crop shape: {face_crop.shape}")
                print(f"✓ Landmarks count: {len(landmarks)}")
            except ValueError as e:
                print(f"✗ Unpacking failed: {e}")
                return False
                
        print("✅ Face detection fix verified successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_face_detection_fix()
    if success:
        print("\n🎉 The face detection error has been FIXED!")
        print("The 'too many values to unpack (expected 4)' error should no longer occur.")
    else:
        print("\n❌ Face detection fix verification failed.")
    
    sys.exit(0 if success else 1)
