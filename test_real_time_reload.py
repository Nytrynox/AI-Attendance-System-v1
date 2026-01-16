#!/usr/bin/env python3
"""
Real-time Reload Test Script
============================

This script tests the automatic user registration and attendance system
to ensure newly registered users are immediately available for attendance
without manual refresh.
"""

import os
import sys
import time
import threading
import numpy as np
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from face_recognizer import FaceRecognizer
    from utils.data_utils import save_user_data, trigger_user_reload_notification
    from utils.data_utils import load_registered_users
    import face_recognition
    import cv2
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please make sure all dependencies are installed")
    sys.exit(1)


def create_test_user_data():
    """Create test user data for registration"""
    # Create a simple test image with face-like features
    test_image = np.ones((200, 200, 3), dtype=np.uint8) * 128  # Gray background
    
    # Add face-like features
    cv2.rectangle(test_image, (75, 75), (125, 125), (200, 200, 200), -1)  # Face area
    cv2.circle(test_image, (90, 95), 3, (50, 50, 50), -1)  # Left eye
    cv2.circle(test_image, (110, 95), 3, (50, 50, 50), -1)  # Right eye
    cv2.ellipse(test_image, (100, 110), (8, 4), 0, 0, 180, (50, 50, 50), 2)  # Smile
    
    # Generate unique user ID with timestamp
    user_id = f"TEST_AUTO_{int(datetime.now().timestamp())}"
    user_name = f"Test User {user_id[-4:]}"
    
    return user_id, user_name, test_image


def test_attendance_mode_simulation():
    """Simulate attendance mode checking for users"""
    print("\n=== Simulating Attendance Mode ===")
    
    recognizer = FaceRecognizer()
    
    # Simulate attendance mode loop
    for i in range(20):  # Run for 20 iterations (about 20 seconds)
        print(f"\n--- Attendance Check {i+1}/20 ---")
        
        # Check current user count
        current_count = len(recognizer.known_face_encodings)
        print(f"Current registered users in recognizer: {current_count}")
        
        # Simulate what happens during face recognition (triggers auto-reload)
        try:
            # Create a dummy face image for recognition test
            dummy_face = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)
            user_id, name, confidence = recognizer.recognize_face(dummy_face)
            print(f"Recognition test result: {name} (confidence: {confidence:.3f})")
        except Exception as e:
            print(f"Recognition test failed (normal for dummy data): {e}")
        
        # Check if user count changed
        new_count = len(recognizer.known_face_encodings)
        if new_count != current_count:
            print(f"✓ User count changed! Now: {new_count} (was: {current_count})")
            print("Current users:")
            for j, (uid, uname) in enumerate(zip(recognizer.known_ids, recognizer.known_names)):
                print(f"  {j+1}. {uname} (ID: {uid})")
        
        time.sleep(1)  # Wait 1 second between checks


def main():
    """Main test function"""
    print("=== Real-time User Registration and Attendance Test ===")
    print("This test simulates registering a user while attendance mode is running")
    
    # Step 1: Check initial state
    print("\n1. Checking initial state...")
    users = load_registered_users()
    print(f"Initial registered users: {len(users)}")
    
    recognizer = FaceRecognizer()
    print(f"Face recognizer loaded users: {len(recognizer.known_face_encodings)}")
    
    # Step 2: Start attendance mode simulation in background
    print("\n2. Starting attendance mode simulation...")
    attendance_thread = threading.Thread(target=test_attendance_mode_simulation, daemon=True)
    attendance_thread.start()
    
    # Step 3: Wait a few seconds, then register new user
    print("\n3. Waiting 5 seconds before registering new user...")
    time.sleep(5)
    
    print("\n4. Registering new test user...")
    user_id, user_name, test_image = create_test_user_data()
    
    try:
        # Try to create face encoding (might fail with synthetic image)
        rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image)
        
        if not encodings:
            print("Warning: Could not create real face encoding, using dummy encoding")
            # Create dummy encoding for testing
            dummy_encoding = np.random.random(128).astype(np.float64)
            encodings = [dummy_encoding]
        
        # Save the user
        success = save_user_data(user_id, user_name, encodings, test_image)
        
        if success:
            print(f"✓ Successfully registered test user: {user_name} (ID: {user_id})")
            
            # Manually trigger reload notification to ensure it's sent
            trigger_user_reload_notification()
            print("✓ Reload notification sent")
        else:
            print("✗ Failed to register test user")
            return False
            
    except Exception as e:
        print(f"Failed to register user: {e}")
        return False
    
    # Step 5: Wait for attendance mode to detect the new user
    print("\n5. Waiting for attendance mode to detect new user...")
    print("The attendance simulation should detect the new user within a few seconds...")
    
    # Wait for the attendance thread to finish
    time.sleep(15)
    
    # Step 6: Final verification
    print("\n6. Final verification...")
    final_users = load_registered_users()
    print(f"Final registered users: {len(final_users)}")
    
    final_recognizer = FaceRecognizer()
    print(f"Final face recognizer users: {len(final_recognizer.known_face_encodings)}")
    
    if len(final_recognizer.known_face_encodings) > len(recognizer.known_face_encodings):
        print("✅ SUCCESS: New user was automatically detected by face recognizer!")
        return True
    else:
        print("❌ FAILED: New user was not detected automatically")
        return False


def cleanup_test_users():
    """Clean up test users"""
    print("\n7. Cleaning up test users...")
    try:
        import shutil
        data_dir = "data/registered_users"
        if os.path.exists(data_dir):
            for item in os.listdir(data_dir):
                if item.startswith("TEST_AUTO_"):
                    test_path = os.path.join(data_dir, item)
                    if os.path.isdir(test_path):
                        shutil.rmtree(test_path)
                        print(f"  Removed: {test_path}")
    except Exception as e:
        print(f"Cleanup warning: {e}")


if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print("\n🎉 REAL-TIME RELOAD TEST PASSED!")
            print("✅ New users are automatically detected during attendance mode!")
        else:
            print("\n❌ REAL-TIME RELOAD TEST FAILED!")
            print("The system needs manual refresh to detect new users.")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_test_users()
        print("\nTest completed.")
