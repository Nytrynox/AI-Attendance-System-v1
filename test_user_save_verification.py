#!/usr/bin/env python3
"""
Test user registration and verify the saved data format
"""

import os
import pickle
import cv2
import numpy as np
from src.utils.data_utils import load_registered_users

def test_registration_and_loading():
    """Test the complete registration and loading pipeline"""
    
    print("=== Testing User Registration and Loading ===")
    
    # Check registered users directory
    registered_users_dir = "data/registered_users"
    if not os.path.exists(registered_users_dir):
        print(f"❌ Registered users directory doesn't exist: {registered_users_dir}")
        return False
    
    print(f"✅ Registered users directory exists: {registered_users_dir}")
    
    # List all items in the directory
    items = os.listdir(registered_users_dir)
    print(f"📁 Items in registered_users directory: {items}")
    
    if not items or all(item.startswith('.') for item in items):
        print("⚠️  No user directories found. This is normal if no users have been registered yet.")
        print("   Use the registration window to add a user first.")
        return True
    
    # Try to load registered users
    try:
        users = load_registered_users()
        print(f"📊 Successfully loaded {len(users)} users")
        
        for user_id, name, encoding in users:
            print(f"   - User: {name} (ID: {user_id})")
            print(f"     Encoding shape: {encoding.shape}")
            print(f"     Encoding type: {type(encoding)}")
            
            # Verify the user directory structure
            user_dirs = [d for d in os.listdir(registered_users_dir) 
                        if os.path.isdir(os.path.join(registered_users_dir, d)) 
                        and user_id in d]
            
            if user_dirs:
                user_dir = os.path.join(registered_users_dir, user_dirs[0])
                print(f"     User directory: {user_dir}")
                
                # Check files in user directory
                user_files = os.listdir(user_dir)
                print(f"     Files: {user_files}")
                
                # Verify required files exist
                has_encoding = any(f.endswith('_encoding.pkl') for f in user_files)
                has_photo = any(f.endswith('.jpg') for f in user_files)
                
                print(f"     ✅ Has encoding file: {has_encoding}")
                print(f"     ✅ Has photo file: {has_photo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load users: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_directory_structure():
    """Check and show the current directory structure"""
    print("\n=== Current Directory Structure ===")
    
    data_dir = "data"
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            level = root.replace(data_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("❌ Data directory doesn't exist")

if __name__ == "__main__":
    check_directory_structure()
    test_registration_and_loading()
    
    print("\n=== Instructions ===")
    print("1. If no users are found, run the registration window:")
    print("   python -c \"from src.gui.add_user_window_liveness_improved import launch_improved_liveness_window; launch_improved_liveness_window()\"")
    print("2. Complete the liveness tests (blink, head movement)")
    print("3. Enter a name and ID, then capture and save the user")
    print("4. Run this test again to verify the user was saved correctly")
