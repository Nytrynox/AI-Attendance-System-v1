#!/usr/bin/env python3
"""
Test Camera Selection Window
----------------------------
Simple test script to verify the camera selection functionality works correctly.
"""

import sys
import os
import tkinter as tk

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.gui.camera_selection_window import CameraSelectionWindow
    
    def test_camera_selection():
        """Test the camera selection window"""
        def on_camera_selected(camera_info):
            print(f"Camera selected: {camera_info}")
            print(f"Type: {camera_info['type']}")
            print(f"Source: {camera_info['source']}")
            print(f"Description: {camera_info['description']}")
            
        root = tk.Tk()
        root.withdraw()  # Hide main window
          # Create camera selection window
        selection_window = tk.Toplevel(root)
        CameraSelectionWindow(selection_window, callback=on_camera_selected)
        
        print("Camera Selection Window Test")
        print("=" * 40)
        print("Instructions:")
        print("1. The camera selection window should open")
        print("2. Try selecting a laptop camera")
        print("3. Try configuring a mobile camera (DroidCam)")
        print("4. Test the selected camera")
        print("5. Close the window when done")
        print()
        
        selection_window.focus_force()
        root.mainloop()
        
    if __name__ == "__main__":
        test_camera_selection()
        
except ImportError as e:
    print(f"Error importing camera selection window: {e}")
    print("Make sure all required dependencies are installed:")
    print("pip install opencv-python pillow numpy requests")
except Exception as e:
    print(f"Error running test: {e}")
