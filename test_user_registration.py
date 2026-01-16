#!/usr/bin/env python3
"""
Test User Registration and Loading - Verify save/load functionality
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_utils import load_registered_users
from src.face_recognizer import FaceRecognizer

def test_user_loading():
    """Test if saved users are properly loaded"""
    print("🧪 Testing User Registration and Loading System")
    print("=" * 60)
    
    # Check registered users directory
    users_dir = "data/registered_users"
    if os.path.exists(users_dir):
        print(f"✅ Users directory exists: {users_dir}")
        
        # List all user directories
        user_dirs = []
        for item in os.listdir(users_dir):
            item_path = os.path.join(users_dir, item)
            if os.path.isdir(item_path):
                user_dirs.append(item)
        
        print(f"📁 Found {len(user_dirs)} user directories:")
        for user_dir in user_dirs:
            print(f"   • {user_dir}")
            
            # Check contents of each user directory
            user_path = os.path.join(users_dir, user_dir)
            files = os.listdir(user_path)
            print(f"     Files: {', '.join(files)}")
            
            # Check for encoding file
            encoding_files = [f for f in files if f.endswith('_encoding.pkl')]
            if encoding_files:
                print(f"     ✅ Encoding file found: {encoding_files[0]}")
            else:
                print(f"     ❌ No encoding file found")
            
            # Check for photo files
            photo_files = [f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))]
            if photo_files:
                print(f"     ✅ Photo files found: {', '.join(photo_files)}")
            else:
                print(f"     ❌ No photo files found")
            print()
    else:
        print(f"❌ Users directory not found: {users_dir}")
        return
    
    # Test loading users
    print("🔄 Testing user loading...")
    try:
        users = load_registered_users()
        print(f"✅ Successfully loaded {len(users)} users")
        
        for user_id, name, encoding in users:
            print(f"   • User: {name} (ID: {user_id})")
            print(f"     Encoding shape: {encoding.shape if hasattr(encoding, 'shape') else 'Unknown'}")
            print(f"     Encoding type: {type(encoding)}")
        
    except Exception as e:
        print(f"❌ Failed to load users: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test face recognizer loading
    print("\n🔄 Testing FaceRecognizer loading...")
    try:
        face_recognizer = FaceRecognizer()
        face_recognizer.reload_user_data()
        
        print(f"✅ FaceRecognizer loaded successfully")
        print(f"   Known users: {len(face_recognizer.known_ids)}")
        print(f"   User IDs: {face_recognizer.known_ids}")
        print(f"   User names: {face_recognizer.known_names}")
        print(f"   Face encodings: {len(face_recognizer.known_face_encodings)}")
        
    except Exception as e:
        print(f"❌ Failed to initialize FaceRecognizer: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 User registration and loading test completed!")
    print("=" * 60)
    print("RECOMMENDATIONS:")
    print("1. Register a user using the improved liveness detection window")
    print("2. Check that all files are saved (PKL, JPG, metadata)")
    print("3. Verify that the user appears in face recognition system")
    print("4. Test attendance recognition with the registered user")

if __name__ == "__main__":
    test_user_loading()
