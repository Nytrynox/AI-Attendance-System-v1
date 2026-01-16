#!/usr/bin/env python3
"""
Clean Launcher for Enhanced Liveness Attendance System
This is a production-ready launcher with proper error handling
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main launcher function"""
    print("🔒 Enhanced Liveness Facial Attendance System")
    print("=" * 60)
    
    try:
        # Import required modules
        from src.gui.main_window_liveness_attendance import EnhancedLivenessWindow
        import tkinter as tk
        from tkinter import messagebox
        
        print("[INFO] Starting enhanced liveness attendance system...")
        
        # Create root window
        root = tk.Tk()
        
        # Initialize the application
        app = EnhancedLivenessWindow(root)
        
        def on_closing():
            """Handle window closing"""
            try:
                if hasattr(app, 'camera_running') and app.camera_running:
                    app.stop_attendance_mode()
            except Exception as e:
                print(f"Warning during cleanup: {e}")
            finally:
                root.destroy()
        
        # Set close handler
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("[INFO] Enhanced liveness attendance system ready!")
        print("[INFO] Features:")
        print("  • Automatic eye blink detection")
        print("  • Head movement verification")  
        print("  • Advanced phone screen detection")
        print("  • Real-time liveness verification")
        print("  • Secure attendance marking")
        print("")
        print("Press Ctrl+C to exit")
        
        # Start the application
        root.mainloop()
    except ImportError as e:
        error_msg = f"Failed to import required modules: {e}"
        print(f"❌ {error_msg}")
        try:
            messagebox.showerror("Import Error", error_msg)
        except Exception:
            pass
        return 1
        
    except Exception as e:
        error_msg = f"Failed to start application: {e}"
        print(f"❌ {error_msg}")
        try:
            messagebox.showerror("Application Error", error_msg)
        except:
            pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
