#!/usr/bin/env python3
"""
Debug script to check the format of existing encoding files.
"""

import os
import pickle

def inspect_encoding_file(file_path):
    """Inspect the contents of an encoding file."""
    try:
        with open(file_path, "rb") as f:
            data = pickle.load(f)
        
        print(f"File: {file_path}")
        print(f"Type: {type(data)}")
        print(f"Data: {data}")
        
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            for key, value in data.items():
                print(f"  {key}: {type(value)} - {value}")
        elif isinstance(data, (list, tuple)):
            print(f"Length: {len(data)}")
            for i, item in enumerate(data):
                print(f"  [{i}]: {type(item)} - {item}")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"[ERROR] Failed to load {file_path}: {e}")

def main():
    """Check all encoding files in the registered users directory."""
    registered_users_dir = "data/registered_users"
    
    if not os.path.exists(registered_users_dir):
        print("No registered users directory found.")
        return
    
    for item in os.listdir(registered_users_dir):
        item_path = os.path.join(registered_users_dir, item)
        
        if os.path.isdir(item_path):
            for filename in os.listdir(item_path):
                if filename.endswith(".pkl"):
                    file_path = os.path.join(item_path, filename)
                    inspect_encoding_file(file_path)

if __name__ == "__main__":
    main()
