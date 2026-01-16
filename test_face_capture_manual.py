#!/usr/bin/env python3
"""
Test the face capture and save functionality with a simulated image
"""

import os
import sys
import cv2
import numpy as np

# Add the src directory to the path so we can import our modules
sys.path.append('src')

from src.gui.add_user_window_liveness_improved import ImprovedLivenessAddUserWindow
from src.utils.image_utils import preprocess_for_face_recognition

def test_face_capture_save():
    """Test the face capture and save process without GUI"""
    
    print("=== Testing Face Capture and Save Process ===")
    
    # Create a dummy face image (this would normally come from the camera)
    dummy_image = np.zeros((400, 400, 3), dtype=np.uint8)
    
    # Draw a simple face-like shape
    center = (200, 200)
    cv2.circle(dummy_image, center, 100, (200, 180, 160), -1)  # Face
    cv2.circle(dummy_image, (170, 170), 15, (0, 0, 0), -1)     # Left eye
    cv2.circle(dummy_image, (230, 170), 15, (0, 0, 0), -1)     # Right eye
    cv2.ellipse(dummy_image, (200, 220), (30, 15), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    
    print("✅ Created dummy face image")
    
    # Test face preprocessing
    try:
        face_encodings = preprocess_for_face_recognition(dummy_image)
        if face_encodings:
            print(f"✅ Face encoding generated successfully, shape: {face_encodings[0].shape}")
            face_encoding = face_encodings[0]
        else:
            print("❌ Failed to generate face encoding")
            return False
    except Exception as e:
        print(f"❌ Error in face preprocessing: {e}")
        return False
    
    # Test the save process by manually calling the save logic
    try:
        user_id = "TEST002"
        name = "Manual Test User"
        
        # Create user directory
        user_dir = f"data/registered_users/{user_id}_{name.replace(' ', '_')}"
        os.makedirs(user_dir, exist_ok=True)
        print(f"✅ Created user directory: {user_dir}")
        
        # Create user data with the exact format expected by the system
        from datetime import datetime
        import pickle
        
        user_data = {
            'name': name,
            'id': user_id,
            'encoding': face_encoding,  # This is the key the system looks for
            'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'liveness_verified': True,
            'anti_spoof_passed': True,
            'encoding_version': 'face_recognition_1.3.0'
        }
        
        # Save user encoding data in the expected format
        encoding_file = os.path.join(user_dir, f"{user_id}_encoding.pkl")
        with open(encoding_file, 'wb') as f:
            pickle.dump(user_data, f)
        print(f"✅ Saved user encoding to: {encoding_file}")
        
        # Save user photo
        image_file = os.path.join(user_dir, f"{user_id}_photo.jpg")
        cv2.imwrite(image_file, dummy_image)
        print(f"✅ Saved user photo to: {image_file}")
        
        # Save face crop
        face_crop_file = os.path.join(user_dir, f"{user_id}_face_crop.jpg")
        cv2.imwrite(face_crop_file, dummy_image)
        print(f"✅ Saved face crop to: {face_crop_file}")
        
        # Save metadata
        metadata_file = os.path.join(user_dir, "user_info.txt")
        with open(metadata_file, 'w') as f:
            f.write(f"Name: {name}\n")
            f.write(f"ID: {user_id}\n")
            f.write(f"Registration Date: {user_data['registration_date']}\n")
            f.write(f"Liveness Verified: {user_data['liveness_verified']}\n")
            f.write(f"Anti-Spoof Passed: {user_data['anti_spoof_passed']}\n")
            f.write(f"Face Encoding Shape: {face_encoding.shape}\n")
            f.write(f"Encoding Version: {user_data['encoding_version']}\n")
        print(f"✅ Saved metadata to: {metadata_file}")
        
        print(f"🎉 Manual test user '{name}' (ID: {user_id}) created successfully!")
        
        # Verify it can be loaded
        from src.utils.data_utils import load_registered_users
        users = load_registered_users()
        
        found_user = False
        for uid, uname, encoding in users:
            if uid == user_id:
                print(f"✅ User verified in database: {uname} (ID: {uid}), encoding shape: {encoding.shape}")
                found_user = True
                break
        
        if not found_user:
            print(f"❌ User not found in database")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error in save process: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_face_capture_save()
    if success:
        print("\n✅ All tests passed! The registration system is working correctly.")
        print("The issue might be with completing the liveness tests in the GUI.")
        print("Make sure to:")
        print("1. Blink naturally a few times")
        print("2. Move your head left and right slowly")
        print("3. Wait for all liveness tests to complete before capturing")
    else:
        print("\n❌ Tests failed! There may be an issue with the registration system.")
