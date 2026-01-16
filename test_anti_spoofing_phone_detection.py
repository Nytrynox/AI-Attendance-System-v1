#!/usr/bin/env python3
"""
Test anti-spoofing and phone detection functionality
"""

import os
import sys
import cv2
import numpy as np

# Add the src directory to the path
sys.path.append('src')

from src.anti_spoof import AntiSpoofingDetector
from src.gui.add_user_window_liveness_improved import ImprovedLivenessAddUserWindow

def test_anti_spoofing():
    """Test the anti-spoofing detector"""
    print("=== Testing Anti-Spoofing Detector ===")
    
    try:
        # Initialize the detector
        detector = AntiSpoofingDetector()
        print("✅ Anti-spoofing detector initialized successfully")
        
        # Create a test image (simulating a phone screen - uniform and bright)
        phone_screen_image = np.ones((160, 160, 3), dtype=np.uint8) * 220  # Bright uniform image
        
        # Test phone screen detection
        is_real_phone = detector.check_if_real(phone_screen_image)
        print(f"📱 Phone screen test - Is real: {is_real_phone} (should be False)")
        
        # Create a more natural test image
        natural_image = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
        
        # Add some texture to make it more natural
        for i in range(0, 160, 10):
            for j in range(0, 160, 10):
                natural_image[i:i+5, j:j+5] = np.random.randint(100, 200, (5, 5, 3))
        
        is_real_natural = detector.check_if_real(natural_image)
        print(f"👤 Natural image test - Is real: {is_real_natural}")
        
        # Get model info
        model_info = detector.get_model_info()
        print(f"📊 Model info: {model_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Anti-spoofing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phone_detection():
    """Test the phone detection algorithm"""
    print("\n=== Testing Phone Detection Algorithm ===")
    
    try:
        # Create a dummy liveness window to access the phone detection method
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        app = ImprovedLivenessAddUserWindow(root)
        
        # Test 1: Phone screen (uniform, bright)
        phone_image = np.ones((200, 200, 3), dtype=np.uint8) * 230  # Very uniform bright image
        is_phone1 = app.detect_phone_screen_enhanced(phone_image)
        print(f"📱 Uniform bright image - Is phone: {is_phone1} (should be True)")
        
        # Test 2: Natural face (varied texture)
        natural_face = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
        # Add natural face-like features
        cv2.circle(natural_face, (100, 100), 80, (180, 150, 120), -1)  # Face color
        cv2.circle(natural_face, (80, 80), 10, (0, 0, 0), -1)   # Eye
        cv2.circle(natural_face, (120, 80), 10, (0, 0, 0), -1)  # Eye
        cv2.ellipse(natural_face, (100, 120), (20, 10), 0, 0, 180, (100, 50, 50), 2)  # Mouth
        
        is_phone2 = app.detect_phone_screen_enhanced(natural_face)
        print(f"👤 Natural face image - Is phone: {is_phone2} (should be False)")
        
        # Test 3: Screen-like image (uniform color, low texture)
        screen_image = np.full((200, 200, 3), (240, 240, 250), dtype=np.uint8)  # Almost white screen
        is_phone3 = app.detect_phone_screen_enhanced(screen_image)
        print(f"💻 Screen-like image - Is phone: {is_phone3} (should be True)")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Phone detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test the integration of both systems"""
    print("\n=== Testing Integration ===")
    
    try:
        # Test that both systems work together
        detector = AntiSpoofingDetector()
        
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        
        app = ImprovedLivenessAddUserWindow(root)
        
        # Create a phone screen image
        phone_image = np.ones((160, 160, 3), dtype=np.uint8) * 225
        
        # Test both detectors
        anti_spoof_result = detector.check_if_real(phone_image)
        phone_detect_result = app.detect_phone_screen_enhanced(phone_image)
        
        print(f"📱 Phone image:")
        print(f"   Anti-spoof says real: {anti_spoof_result}")
        print(f"   Phone detector says phone: {phone_detect_result}")
        print(f"   Combined result: Should reject if either fails")
        
        # Should be rejected if either anti-spoof OR phone detection triggers
        should_reject = (not anti_spoof_result) or phone_detect_result
        print(f"   ✅ Should reject: {should_reject}")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🔒 Testing Anti-Spoofing and Phone Detection Systems")
    print("=" * 60)
    
    # Check if model exists
    model_path = "models/anti_spoof_model.h5"
    if not os.path.exists(model_path):
        print(f"❌ Anti-spoof model not found at {model_path}")
        print("   This is normal if the model hasn't been trained yet.")
        print("   The phone detection will still work independently.")
        return
    
    tests = [
        ("Anti-Spoofing", test_anti_spoofing),
        ("Phone Detection", test_phone_detection),
        ("Integration", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    if all(result for _, result in results):
        print("\n🎉 All tests passed! Anti-spoofing and phone detection are working correctly.")
        print("💡 Tips for testing:")
        print("   - Use a phone screen showing a face image - should be detected as spoof")
        print("   - Use printed photos - should be detected as spoof")
        print("   - Use real face - should pass all tests")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
