#!/usr/bin/env python3
"""
Launch the Fixed Enhanced Liveness Attendance System
This launcher tests the corrected main_window_liveness_attendance.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 Launching Fixed Enhanced Liveness Attendance System...")
    print("="*60)
    
    try:
        # Import the class directly instead of main function
        from src.gui.main_window_liveness_attendance import EnhancedLivenessWindow
        import tkinter as tk
        from tkinter import messagebox
        
        print("[INFO] All syntax errors have been fixed!")
        print("[INFO] Starting the enhanced liveness GUI...")
        
        # Create and run the application directly
        print("🔒 Starting Enhanced Liveness Facial Attendance System...")
        print("="*60)
        
        root = tk.Tk()
        
        try:
            app = EnhancedLivenessWindow(root)
            
            def on_closing():
                if hasattr(app, 'camera_running') and app.camera_running:
                    app.stop_attendance_mode()
                root.destroy()
            
            root.protocol("WM_DELETE_WINDOW", on_closing)
            
            print("[INFO] Enhanced liveness attendance system ready!")
            print("[INFO] Features:")
            print("  • Automatic eye blink detection")
            print("  • Head movement verification")  
            print("  • Advanced phone screen detection")
            print("  • Real-time liveness verification")
            print("  • Secure attendance marking")
            
            root.mainloop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start application: {e}")
            print(f"App Error: {e}")
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
