#!/usr/bin/env python3
"""
Test Dual Camera System
------------------------
Simple test script to verify the dual camera functionality works correctly.
"""

import sys
import os
import tkinter as tk

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.gui.dual_camera_window import DualCameraWindow
    
    def test_dual_camera():
        """Test the dual camera window"""
        
        root = tk.Tk()
        
        print("Dual Camera System Test")
        print("=" * 50)
        print("Instructions:")
        print("1. The dual camera window should open")
        print("2. You'll see controls for left and right cameras")
        print("3. Click 'Select Left Camera' for laptop camera")
        print("4. Click 'Select Right Camera' for mobile camera")
        print("5. Start cameras individually or both together")
        print("6. Test in both Preview and Attendance modes")
        print("7. Monitor statistics for both cameras")
        print("8. Close the window when done")
        print()
        print("Features to test:")
        print("- Camera selection for both sides")
        print("- Independent camera controls")
        print("- Side-by-side video displays")
        print("- Dual mode operation (Preview/Attendance)")
        print("- Statistics tracking for both cameras")
        print("- User registration")
        print()
        
        app = DualCameraWindow(root)
        root.protocol("WM_DELETE_WINDOW", app.close_application)
        root.mainloop()
        
    if __name__ == "__main__":
        test_dual_camera()
        
except ImportError as e:
    print(f"Error importing dual camera window: {e}")
    print("Make sure all required dependencies are installed:")
    print("pip install opencv-python pillow numpy requests")
    print()
    print("Also ensure the following files exist:")
    print("- src/gui/dual_camera_window.py")
    print("- src/gui/camera_selection_window.py")
    print("- src/utils/camera_utils.py")
except Exception as e:
    print(f"Error running test: {e}")
