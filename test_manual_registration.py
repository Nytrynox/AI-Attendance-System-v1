#!/usr/bin/env python3
"""
Simple test to manually register a user and verify the save process
"""

import os
import pickle
import cv2
import numpy as np
import face_recognition
from datetime import datetime

def create_test_user():
    """Create a test user with dummy data to verify the save format"""
    
    print("=== Creating Test User ===")
    
    # Create dummy face encoding (128-dimensional vector)
    dummy_encoding = np.random.rand(128).astype(np.float64)
    
    # Create dummy image
    dummy_image = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.putText(dummy_image, "Test User", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # User data
    user_id = "TEST001"
    name = "Test User"
    
    # Create user directory structure as expected by the system
    user_dir = f"data/registered_users/{user_id}_{name.replace(' ', '_')}"
    os.makedirs(user_dir, exist_ok=True)
    print(f"✅ Created user directory: {user_dir}")
    
    # Create user data in the exact format expected by load_registered_users()
    user_data = {
        'name': name,
        'id': user_id,
        'encoding': dummy_encoding,  # This is the key the system looks for
        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'liveness_verified': True,
        'anti_spoof_passed': True,
        'encoding_version': 'face_recognition_1.3.0'
    }
    
    # Save encoding file with the exact format expected
    encoding_file = os.path.join(user_dir, f"{user_id}_encoding.pkl")
    with open(encoding_file, 'wb') as f:
        pickle.dump(user_data, f)
    print(f"✅ Saved encoding file: {encoding_file}")
    
    # Save image files
    image_file = os.path.join(user_dir, f"{user_id}_photo.jpg")
    cv2.imwrite(image_file, dummy_image)
    print(f"✅ Saved image file: {image_file}")
    
    # Save face crop
    face_crop_file = os.path.join(user_dir, f"{user_id}_face_crop.jpg")
    cv2.imwrite(face_crop_file, dummy_image)
    print(f"✅ Saved face crop: {face_crop_file}")
    
    # Save metadata
    metadata_file = os.path.join(user_dir, "user_info.txt")
    with open(metadata_file, 'w') as f:
        f.write(f"Name: {name}\n")
        f.write(f"ID: {user_id}\n")
        f.write(f"Registration Date: {user_data['registration_date']}\n")
        f.write(f"Liveness Verified: {user_data['liveness_verified']}\n")
        f.write(f"Anti-Spoof Passed: {user_data['anti_spoof_passed']}\n")
        f.write(f"Face Encoding Shape: {dummy_encoding.shape}\n")
        f.write(f"Encoding Version: {user_data['encoding_version']}\n")
    print(f"✅ Saved metadata: {metadata_file}")
    
    print(f"🎉 Test user '{name}' (ID: {user_id}) created successfully!")
    return True

def verify_test_user():
    """Verify the test user can be loaded correctly"""
    print("\n=== Verifying Test User ===")
    
    try:
        from src.utils.data_utils import load_registered_users
        users = load_registered_users()
        
        if users:
            print(f"✅ Successfully loaded {len(users)} users:")
            for user_id, name, encoding in users:
                print(f"   - {name} (ID: {user_id}) - Encoding shape: {encoding.shape}")
        else:
            print("❌ No users were loaded")
            
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_user()
    verify_test_user()
