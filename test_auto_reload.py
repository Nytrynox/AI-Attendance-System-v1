#!/usr/bin/env python3
"""
Test script to verify automatic user data reloading works correctly.
This simulates registering a new user and checking if the face recognizer 
automatically picks up the changes without manual restart.
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from face_recognizer import FaceRecognizer
    from utils.data_utils import trigger_user_reload_notification, save_user_data
    import face_recognition
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please make sure all dependencies are installed and you're in the correct directory")
    sys.exit(1)

def test_auto_reload():
    """Test the automatic reload functionality"""
    print("=== Testing Automatic User Data Reloading ===")
    
    # Initialize face recognizer
    print("\n1. Initializing face recognizer...")
    recognizer = FaceRecognizer()
    
    # Check initial user count
    initial_count = len(recognizer.known_face_encodings)
    print(f"   Initial registered users: {initial_count}")
    
    if initial_count > 0:
        print("   Current users:")
        for i, (user_id, name) in enumerate(zip(recognizer.known_ids, recognizer.known_names)):
            print(f"     - {name} (ID: {user_id})")
    
    # Create a test image (simple synthetic face-like image)
    print("\n2. Creating test user data...")
    test_image = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)
    
    # Use a simple pattern that might be recognizable
    cv2.rectangle(test_image, (50, 50), (100, 100), (255, 255, 255), -1)  # White square for "face"
    cv2.circle(test_image, (70, 70), 5, (0, 0, 0), -1)  # Left eye
    cv2.circle(test_image, (90, 70), 5, (0, 0, 0), -1)  # Right eye
    cv2.ellipse(test_image, (80, 85), (10, 5), 0, 0, 180, (0, 0, 0), 2)  # Smile
    
    test_user_id = f"TEST_{int(datetime.now().timestamp())}"
    test_name = "Test User Auto Reload"
    
    # Try to create test encodings
    try:
        # Convert to RGB for face_recognition
        rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
        
        # This might fail since it's a synthetic image, but let's try
        encodings = face_recognition.face_encodings(rgb_image)
        
        if not encodings:
            print("   Warning: Could not create face encoding from synthetic image")
            print("   Using a mock encoding for testing (this won't work for real recognition)")
            # Create a fake encoding for testing the reload mechanism
            fake_encoding = np.random.random(128).astype(np.float64)
            encodings = [fake_encoding]
        
        print(f"   Created test user: {test_name} (ID: {test_user_id})")
        
        # Test 1: Check recognizer BEFORE new user registration
        print("\n3. Testing recognition BEFORE new user registration...")
        try:
            user_id, name, confidence = recognizer.recognize_face(test_image)
            print(f"   Recognition result: {name} (ID: {user_id}, confidence: {confidence:.3f})")
        except Exception as e:
            print(f"   Recognition failed (expected): {e}")
        
        # Test 2: Save new user data using our data utils function
        print("\n4. Registering new test user...")
        success = save_user_face_data(
            test_user_id, 
            test_name, 
            encodings[0], 
            "test_auto_reload_image.jpg",  # Mock image path
            datetime.now().isoformat()
        )
        
        if success:
            print(f"   ✓ Successfully registered test user")
        else:
            print(f"   ✗ Failed to register test user")
            return False
        
        # Test 3: Check if recognizer automatically reloaded
        print("\n5. Testing automatic reload...")
        
        # The next call to recognize_face should trigger check_and_reload_if_needed
        print("   Calling recognize_face (should trigger auto-reload)...")
        
        try:
            user_id, name, confidence = recognizer.recognize_face(test_image)
            print(f"   Recognition result: {name} (ID: {user_id}, confidence: {confidence:.3f})")
            
            # Check if user count increased
            new_count = len(recognizer.known_face_encodings)
            print(f"   User count after reload: {new_count} (was {initial_count})")
            
            if new_count > initial_count:
                print("   ✓ Automatic reload worked! New user detected.")
                
                # List all users to confirm
                print("   Updated user list:")
                for i, (uid, uname) in enumerate(zip(recognizer.known_ids, recognizer.known_names)):
                    print(f"     - {uname} (ID: {uid})")
                
                return True
            else:
                print("   ✗ Automatic reload did not detect new user")
                return False
                
        except Exception as e:
            print(f"   Recognition failed: {e}")
            return False
            
    except Exception as e:
        print(f"   Failed to create test user: {e}")
        return False

def cleanup_test_user():
    """Clean up test user data"""
    print("\n6. Cleaning up test data...")
    
    try:
        # Find and remove test user directories
        data_dir = "data/registered_users"
        if os.path.exists(data_dir):
            for item in os.listdir(data_dir):
                if item.startswith("TEST_"):
                    test_dir = os.path.join(data_dir, item)
                    if os.path.isdir(test_dir):
                        import shutil
                        shutil.rmtree(test_dir)
                        print(f"   Removed test directory: {test_dir}")
    except Exception as e:
        print(f"   Warning: Could not clean up test data: {e}")

if __name__ == "__main__":
    try:
        success = test_auto_reload()
        
        if success:
            print("\n=== ✓ AUTO RELOAD TEST PASSED ===")
            print("The system successfully detects new user registrations automatically!")
        else:
            print("\n=== ✗ AUTO RELOAD TEST FAILED ===")
            print("The system did not automatically reload user data.")
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_test_user()
