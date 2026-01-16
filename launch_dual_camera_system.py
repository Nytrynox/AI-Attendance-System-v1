#!/usr/bin/env python3
"""
Dual Camera Attendance System Launcher
--------------------------------------
Launch the face attendance system with dual camera support - 
both laptop and mobile cameras working simultaneously side by side.

Usage:
    python launch_dual_camera_system.py

Features:
- Simultaneous laptop and mobile camera operation
- Side-by-side camera displays
- Independent camera controls for each side
- Dual camera attendance tracking
- Real-time face recognition on both cameras
- Enhanced statistics and monitoring
"""

import os
import sys
import logging
import tkinter as tk
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.dual_camera_window import DualCameraWindow

# Setup logging
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', f'dual_camera_{datetime.now().strftime("%Y%m%d")}.log')),
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
    """Main function to launch the dual camera attendance system"""
    print("=" * 70)
    print("Face Attendance System - Dual Camera Mode")
    print("=" * 70)
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
    
    print("Starting Dual Camera Attendance System...")
    logger.info("Starting Dual Camera Attendance System")
    
    try:
        # Create and run the application
        root = tk.Tk()
        app = DualCameraWindow(root)
        
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
        print("\nDual Camera System launched successfully!")
        print("Features available:")
        print("  • Simultaneous laptop and mobile camera operation")
        print("  • Side-by-side camera displays")
        print("  • Independent camera controls")
        print("  • Dual camera face recognition")
        print("  • Real-time attendance tracking")
        print("  • Enhanced statistics and monitoring")
        print()
        print("Setup Instructions:")
        print("1. Select Left Camera (typically laptop camera)")
        print("2. Select Right Camera (typically mobile/DroidCam)")
        print("3. Start both cameras individually or together")
        print("4. Switch between Preview and Attendance modes")
        print("5. Monitor both camera feeds simultaneously")
        print()
        print("DroidCam Setup:")
        print("- Install DroidCam app on your phone")
        print("- Connect phone and computer to same WiFi")
        print("- Note IP address in DroidCam app")
        print("- Enter IP in right camera selection")
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
