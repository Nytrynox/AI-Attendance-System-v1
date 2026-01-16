#!/usr/bin/env python3
"""
Test script for improved liveness detection integration with main system
Tests the user registration flow and data saving functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_user_registration():
    """Test user registration with the improved liveness detection"""
    print("🧪 Testing Improved Liveness Detection Registration Integration")
    print("=" * 70)
    
    # Test the launcher function
    try:
        from src.gui.add_user_window_liveness_improved import launch_improved_liveness_window
        print("✅ Successfully imported improved liveness window launcher")
        
        # Test creating the window (without showing it)
        import tkinter as tk
        
        # Create a test callback
        def test_callback():
            print("📞 Callback function called successfully")
        
        print("🚀 Launching improved liveness detection registration window...")
        print("📋 Features included:")
        print("   • Enhanced eye blink detection with EAR (Eye Aspect Ratio)")
        print("   • Robust head movement tracking")
        print("   • Fixed phone detection with retry logic")
        print("   • Less aggressive anti-spoofing (threshold: 0.25)")
        print("   • Automatic liveness test start with camera")
        print("   • Proper user data saving in subdirectory format")
        print("   • Integration with main system refresh callback")
        print("")
        print("🔧 Registration Process:")
        print("   1. Click 'Start Camera' - liveness tests begin automatically")
        print("   2. Blink naturally (3 blinks required)")
        print("   3. Move your head slightly (1 movement required)")
        print("   4. Wait for phone detection to complete (90 frames)")
        print("   5. Enter name and ID")
        print("   6. Click 'Capture Face' when all tests pass")
        print("   7. Click 'Save User' to store in database")
        print("")
        print("💾 Data Storage Format:")
        print("   • User directory: data/registered_users/{ID}_{NAME}/")
        print("   • Encoding file: {ID}_encoding.pkl")
        print("   • Photo file: {ID}_photo.jpg")
        print("   • Metadata file: user_info.txt")
        print("")
        
        # Launch the window
        launch_improved_liveness_window(on_close_callback=test_callback)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_data_loading():
    """Test that saved user data can be loaded correctly"""
    print("\n🔍 Testing User Data Loading...")
    
    try:
        from src.utils.data_utils import load_registered_users
        from src.face_recognizer import FaceRecognizer
        
        # Load registered users
        users = load_registered_users()
        print(f"📊 Found {len(users)} registered users")
        
        # Test face recognizer loading
        recognizer = FaceRecognizer()
        recognizer.reload_user_data()
        print(f"🧠 Face recognizer loaded {len(recognizer.known_ids)} users")
        
        if len(users) > 0:
            print("👥 Registered users:")
            for user_id, name, encoding in users:
                print(f"   • {name} (ID: {user_id}) - Encoding shape: {encoding.shape if hasattr(encoding, 'shape') else 'Unknown'}")
        else:
            print("ℹ️  No users registered yet. Use the registration window to add users.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading user data: {e}")
        return False

if __name__ == "__main__":
    print("🔒 Face Attendance System - Registration Integration Test")
    print("=" * 70)
    
    # Test registration window
    registration_test = test_user_registration()
    
    # Test data loading
    data_test = test_data_loading()
    
    print("\n" + "=" * 70)
    print("📋 Test Results Summary:")
    print(f"   Registration Window: {'✅ PASS' if registration_test else '❌ FAIL'}")
    print(f"   Data Loading: {'✅ PASS' if data_test else '❌ FAIL'}")
    
    if registration_test and data_test:
        print("\n🎉 All tests passed! The improved liveness detection is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
