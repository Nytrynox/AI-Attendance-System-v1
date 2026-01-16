#!/usr/bin/env python3
"""
Migration script to convert legacy face_encoding.pkl files to new {user_id}_encoding.pkl format.
This handles both legacy formats: plain numpy arrays and dictionary formats.
"""

import os
import pickle
import shutil
import numpy as np

def migrate_legacy_encodings():
    """
    Migrate legacy face_encoding.pkl files to new {user_id}_encoding.pkl format.
    """
    registered_users_dir = "data/registered_users"
    
    if not os.path.exists(registered_users_dir):
        print("[INFO] No registered users directory found. Nothing to migrate.")
        return
    
    migrated_count = 0
    error_count = 0
    
    for item in os.listdir(registered_users_dir):
        item_path = os.path.join(registered_users_dir, item)
        
        if os.path.isdir(item_path):
            legacy_file = os.path.join(item_path, "face_encoding.pkl")
            
            if os.path.exists(legacy_file):
                try:
                    # Load the legacy file
                    with open(legacy_file, "rb") as f:
                        data = pickle.load(f)
                    
                    # Check if data is a dictionary (new format) or numpy array (legacy format)
                    if isinstance(data, dict):
                        # Already in new format with metadata
                        user_id = data.get('id', item)
                        user_name = data.get('name', f'User_{item}')
                        encoding = data.get('encoding')
                    else:
                        # Legacy format - just the numpy array
                        # Try to read metadata from user_info.txt
                        user_info_file = os.path.join(item_path, "user_info.txt")
                        user_id = item  # Default to directory name
                        user_name = f"User_{item}"  # Default name
                        
                        if os.path.exists(user_info_file):
                            try:
                                with open(user_info_file, "r") as f:
                                    lines = f.readlines()
                                    for line in lines:
                                        if line.startswith("Name:"):
                                            user_name = line.split(":", 1)[1].strip()
                                        elif line.startswith("ID:"):
                                            user_id = line.split(":", 1)[1].strip()
                            except Exception as e:
                                print(f"[WARNING] Could not read user_info.txt for {item}: {e}")
                        
                        # Create the new format data structure
                        data = {
                            'id': user_id,
                            'name': user_name,
                            'encoding': data  # The numpy array
                        }
                        encoding = data['encoding']
                    
                    # Create new filename
                    new_filename = f"{user_id}_encoding.pkl"
                    new_file_path = os.path.join(item_path, new_filename)
                    
                    # Check if new file already exists
                    if os.path.exists(new_file_path):
                        print(f"[INFO] New format file already exists for user {user_name}, skipping migration.")
                    else:
                        # Save in new format
                        with open(new_file_path, "wb") as f:
                            pickle.dump(data, f)
                        
                        print(f"[INFO] Migrated {user_name} (ID: {user_id}): face_encoding.pkl -> {new_filename}")
                        migrated_count += 1
                    
                    # Optionally backup and remove the legacy file
                    backup_file = os.path.join(item_path, "face_encoding.pkl.backup")
                    if not os.path.exists(backup_file):
                        shutil.copy2(legacy_file, backup_file)
                        print(f"[INFO] Created backup: {backup_file}")
                    
                    # Remove the legacy file after successful migration
                    os.remove(legacy_file)
                    print(f"[INFO] Removed legacy file: {legacy_file}")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to migrate {legacy_file}: {e}")
                    error_count += 1
    
    print(f"\n[MIGRATION COMPLETE]")
    print(f"Successfully migrated: {migrated_count} users")
    print(f"Errors encountered: {error_count}")
    
    if migrated_count > 0:
        print(f"\nLegacy files have been backed up with .backup extension.")
        print(f"You can safely delete the .backup files after confirming the system works correctly.")

if __name__ == "__main__":
    print("=== Face Encoding Migration Tool ===")
    print("This script will migrate legacy face_encoding.pkl files to the new {user_id}_encoding.pkl format.")
    
    migrate_legacy_encodings()
