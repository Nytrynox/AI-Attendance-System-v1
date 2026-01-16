#!/usr/bin/env python3
"""
Test dual camera system with threading fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import DualCameraWindow
import tkinter as tk

def test_dual_camera():
    """Test the dual camera window"""
    print("Testing dual camera window...")
    
    root = tk.Tk()
    root.title("Test Dual Camera")
    
    try:
        app = DualCameraWindow(root)
        print("✅ Dual camera window created successfully")
        print("📷 Laptop camera should be initializing...")
        print("📱 DroidCam connection will be attempted...")
        print("💡 If DroidCam fails, you'll see a help dialog")
        
        # Run for just a few seconds for testing
        root.after(5000, root.quit)  # Close after 5 seconds
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    test_dual_camera()
