# src/utils/data_utils.py

import os
import pickle
import csv
import cv2
from datetime import datetime

REGISTERED_USERS_DIR = "data/registered_users"
ATTENDANCE_DIR = "data/attendance"

def load_registered_users():
    """
    Loads all registered user encodings from .pkl files.
    Supports both old format (direct .pkl files) and new format (subdirectories).
    Returns:
        List of tuples (user_id, name, encoding)
    """
    users = []
    
    if not os.path.exists(REGISTERED_USERS_DIR):
        return users
        
    # Check for files in subdirectories (new format)
    for item in os.listdir(REGISTERED_USERS_DIR):
        item_path = os.path.join(REGISTERED_USERS_DIR, item)
        
        if os.path.isdir(item_path) and not item.startswith('.'):
            # Look for encoding files in subdirectory
            encoding_loaded = False
            user_id = item
            user_name = None
            user_encoding = None
            
            # First try the new format: {user_id}_encoding.pkl
            for filename in os.listdir(item_path):
                if filename.endswith("_encoding.pkl"):
                    try:
                        with open(os.path.join(item_path, filename), "rb") as f:
                            data = pickle.load(f)
                            
                            # Handle both dictionary and raw numpy array formats
                            if isinstance(data, dict):
                                # Dictionary format with metadata
                                user_encoding = data['encoding']
                                user_name = data['name']
                                user_id = data['id']
                                print(f"[INFO] Loaded user: {user_name} (ID: {user_id}) from {filename} (dict format)")
                            else:
                                # Raw numpy array format - need to get name from user_info.txt
                                user_encoding = data
                                user_info_file = os.path.join(item_path, "user_info.txt")
                                if os.path.exists(user_info_file):
                                    try:
                                        with open(user_info_file, 'r') as info_f:
                                            lines = info_f.read().strip().split('\n')
                                            for line in lines:
                                                if line.startswith('Name: '):
                                                    user_name = line.replace('Name: ', '')
                                                elif line.startswith('ID: '):
                                                    user_id = line.replace('ID: ', '')
                                    except Exception:
                                        pass
                                
                                if user_name is None:
                                    user_name = f"User_{user_id}"
                                
                                print(f"[INFO] Loaded user: {user_name} (ID: {user_id}) from {filename} (array format)")
                            
                            users.append((user_id, user_name, user_encoding))
                            encoding_loaded = True
                            break
                            
                    except Exception as e:
                        print(f"[WARNING] Failed to load user data from {filename}: {e}")
            
            # If new format not found, try legacy format: face_encoding.pkl
            if not encoding_loaded:
                legacy_file = os.path.join(item_path, "face_encoding.pkl")
                if os.path.exists(legacy_file):
                    try:
                        with open(legacy_file, "rb") as f:
                            data = pickle.load(f)
                            
                            # Handle both dictionary and raw numpy array formats
                            if isinstance(data, dict):
                                users.append((data['id'], data['name'], data['encoding']))
                                print(f"[INFO] Loaded user: {data['name']} (ID: {data['id']}) from legacy face_encoding.pkl (dict format)")
                            else:
                                # Raw array - get name from user_info.txt
                                user_encoding = data
                                user_name = f"User_{user_id}"
                                user_info_file = os.path.join(item_path, "user_info.txt")
                                if os.path.exists(user_info_file):
                                    try:
                                        with open(user_info_file, 'r') as info_f:
                                            lines = info_f.read().strip().split('\n')
                                            for line in lines:
                                                if line.startswith('Name: '):
                                                    user_name = line.replace('Name: ', '')
                                    except Exception:
                                        pass
                                
                                users.append((user_id, user_name, user_encoding))
                                print(f"[INFO] Loaded user: {user_name} (ID: {user_id}) from legacy face_encoding.pkl (array format)")
                            
                            encoding_loaded = True
                    except Exception as e:
                        print(f"[WARNING] Failed to load legacy user data from face_encoding.pkl: {e}")
            
            if not encoding_loaded:
                print(f"[WARNING] No valid encoding file found in directory: {item}")
        
        elif item.endswith(".pkl"):
            # Legacy format - direct .pkl files in root directory
            try:
                with open(item_path, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        users.append((data['id'], data['name'], data['encoding']))
                        print(f"[INFO] Loaded legacy user: {data['name']} (ID: {data['id']}) from root directory")
                    else:
                        print(f"[WARNING] Unexpected data format in {item}")
            except Exception as e:
                print(f"[WARNING] Failed to load legacy user data from {item}: {e}")
    
    print(f"[INFO] Total registered users loaded: {len(users)}")
    return users

def save_attendance(user_id, name):
    """
    Records attendance with timestamp for a given user.
    Attendance is saved in a daily CSV file.
    """
    os.makedirs(ATTENDANCE_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    file_path = os.path.join(ATTENDANCE_DIR, f"{date_str}.csv")

    # Check if user already marked
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0] == user_id:
                    return  # already marked

    # Write new entry
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, name, time_str])
        print(f"[INFO] Attendance marked: {name} at {time_str}")

def has_marked_attendance(user_id, date=None):
    """
    Check if a user has already marked attendance for a given date.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    file_path = os.path.join(ATTENDANCE_DIR, f"{date}.csv")
    if not os.path.exists(file_path):
        return False

    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 1 and row[0] == user_id:
                return True
    return False

def ensure_directories(directories):
    """
    Ensure that the specified directories exist, creating them if necessary.
    Args:
        directories (list): List of directory paths to create.
    """
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[INFO] Directory ensured: {directory}")

def get_datetime_string():
    """
    Get current datetime as a formatted string.
    Returns:
        str: Current datetime in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_user_data(user_id, name, face_encodings, face_image):
    """
    Save user registration data including face encodings and image.
    
    Args:
        user_id (str): Unique identifier for the user
        name (str): Full name of the user
        face_encodings (list): List of face encodings for the user
        face_image (numpy.ndarray): Face image/crop
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure registered users directory exists
        os.makedirs(REGISTERED_USERS_DIR, exist_ok=True)
        
        # Create user directory
        user_dir = os.path.join(REGISTERED_USERS_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save face image
        image_path = os.path.join(user_dir, f"{user_id}_{timestamp}.jpg")
        cv2.imwrite(image_path, face_image)
        
        # Prepare user data
        # Use the first encoding if multiple encodings provided
        primary_encoding = face_encodings[0] if isinstance(face_encodings, list) else face_encodings
        
        user_data = {
            'id': user_id,
            'name': name,
            'encoding': primary_encoding,
            'encodings': face_encodings,  # Store all encodings for better accuracy
            'image_path': image_path,
            'timestamp': timestamp,
            'method': 'multiple_captures'  # Indicate this used multiple face captures
        }
        
        # Save user encoding data
        encoding_file = os.path.join(user_dir, f"{user_id}_encoding.pkl")
        with open(encoding_file, 'wb') as f:
            pickle.dump(user_data, f)
        
        print(f"[INFO] User {name} (ID: {user_id}) registered successfully with {len(face_encodings) if isinstance(face_encodings, list) else 1} encodings")
        
        # Create user info file for compatibility
        user_info_file = os.path.join(user_dir, "user_info.txt")
        with open(user_info_file, 'w') as f:
            f.write(f"Name: {name}\n")
            f.write(f"ID: {user_id}\n")
            f.write(f"Registration Date: {timestamp}\n")
            f.write(f"Liveness Verified: True\n")
            f.write(f"Security Level: Advanced\n")
        
        # Trigger automatic reload notification for all active face recognizers
        trigger_user_reload_notification()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save user data for {name} (ID: {user_id}): {str(e)}")
        return False


def trigger_user_reload_notification():
    """
    Create a notification file that signals face recognizers to reload user data.
    This enables real-time user data updates without restarting the application.
    """
    try:
        notification_file = os.path.join(REGISTERED_USERS_DIR, ".reload_trigger")
        with open(notification_file, 'w') as f:
            f.write(f"reload_requested_at_{datetime.now().isoformat()}")
        print("[INFO] User reload notification sent to all active recognizers")
    except Exception as e:
        print(f"[WARNING] Failed to create reload notification: {e}")


def check_reload_notification():
    """
    Check if a user reload notification exists and consume it.
    
    Returns:
        bool: True if reload is needed, False otherwise
    """
    try:
        notification_file = os.path.join(REGISTERED_USERS_DIR, ".reload_trigger")
        if os.path.exists(notification_file):
            os.remove(notification_file)  # Consume the notification
            return True
        return False
    except Exception:
        return False
