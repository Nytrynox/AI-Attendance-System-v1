#!/usr/bin/env python3
"""
Enhanced Camera Attendance System Launcher
------------------------------------------
Launch the face attendance system with enhanced camera support including
laptop cameras and mobile cameras (DroidCam).

Usage:
    python launch_enhanced_camera_system.py [options]

Features:
- Camera selection window for laptop and mobile cameras
- DroidCam support for using mobile phone as camera
- Auto-detection of available cameras
- Network scanning for DroidCam devices
- Enhanced preview and attendance tracking modes
"""

import os
import sys
import logging
import tkinter as tk
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window_enhanced_camera import EnhancedCameraMainWindow

# Setup logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', f'enhanced_camera_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all required dependencies are available"""
    required_modules = [
        'cv2', 'PIL', 'numpy', 'requests', 'dlib'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("ERROR: Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install missing modules with:")
        print("pip install opencv-python pillow numpy requests dlib")
        return False
    
    return True


def check_models():
    """Check if required model files exist"""
    required_models = [
        'models/shape_predictor_68_face_landmarks.dat',
        'models/anti_spoof_model.h5',
        'models/face_recognition_model.h5'
    ]
    
    missing_models = []
    
    for model_path in required_models:
        if not os.path.exists(model_path):
            missing_models.append(model_path)
    
    if missing_models:
        print("WARNING: Some model files are missing:")
        for model in missing_models:
            print(f"  - {model}")
        print("\nThe system may not work properly without these models.")
        print("Please download the required models and place them in the 'models' directory.")
        
        # Ask user if they want to continue
        response = input("\nDo you want to continue anyway? (y/n): ").strip().lower()
        return response == 'y'
    
    return True


def create_directories():
    """Create necessary directories"""
    directories = [
        'data/attendance',
        'data/registered_users',
        'data/logs',
        'models'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")


def main():
    """Main function to launch the enhanced camera attendance system"""
    print("=" * 60)
    print("Face Attendance System - Enhanced Camera Support")
    print("=" * 60)
    print()
    
    # Check requirements
    print("Checking system requirements...")
    if not check_requirements():
        return 1
    
    # Check models
    print("Checking model files...")
    if not check_models():
        return 1
    
    # Create directories
    print("Setting up directories...")
    create_directories()
    
    print("Starting Enhanced Camera Attendance System...")
    logger.info("Starting Enhanced Camera Attendance System")
    
    try:
        # Create and run the application
        root = tk.Tk()
        app = EnhancedCameraMainWindow(root)
        
        # Center the window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Set up proper closing
        root.protocol("WM_DELETE_WINDOW", app.close_application)
        
        # Show startup message
        print("\nSystem launched successfully!")
        print("Features available:")
        print("  • Laptop camera support")
        print("  • Mobile camera support (DroidCam)")
        print("  • Camera selection interface")
        print("  • Auto-detection of available cameras")
        print("  • Network scanning for DroidCam devices")
        print("  • Enhanced face recognition with anti-spoofing")
        print("  • Real-time attendance tracking")
        print("\nInstructions:")
        print("1. Click 'Select Camera' to choose your camera source")
        print("2. Test your camera in preview mode")
        print("3. Switch to attendance mode for tracking")
        print("4. Register new users as needed")
        print()
        
        # Start the main loop
        root.mainloop()
        
        logger.info("Application closed normally")
        return 0
        
    except Exception as e:
        logger.exception(f"Error starting application: {e}")
        print(f"ERROR: Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
