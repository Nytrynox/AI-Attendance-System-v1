#!/usr/bin/env python3
"""
Production Launcher for Enhanced Liveness Attendance System
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔒 Enhanced Liveness Facial Attendance System")
    print("=" * 60)
    
    try:
        from src.gui.main_window_liveness_attendance import EnhancedLivenessWindow
        import tkinter as tk
        from tkinter import messagebox
        
        print("[INFO] Starting enhanced liveness attendance system...")
        
        root = tk.Tk()
        app = EnhancedLivenessWindow(root)
        
        def on_closing():
            try:
                if hasattr(app, 'camera_running') and app.camera_running:
                    app.stop_attendance_mode()
            except Exception as e:
                print(f"Warning during cleanup: {e}")
            finally:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("[INFO] System ready! Features:")
        print("  • Eye blink detection")
        print("  • Head movement verification")  
        print("  • Phone screen detection")
        print("  • Real-time liveness verification")
        
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return 1
        
    except Exception as e:
        print(f"❌ Application Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
