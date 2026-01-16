# test_improved_liveness.py
"""
Test script for the improved liveness detection registration system
"""

import tkinter as tk
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Test the improved liveness detection registration window"""
    print("🔒 Testing Improved Liveness Detection Registration System")
    print("=" * 70)
    print("🆕 NEW FEATURES:")
    print("✅ Enhanced Eye Aspect Ratio (EAR) based blink detection")
    print("✅ Improved head movement tracking with position analysis")
    print("✅ Less aggressive anti-spoofing (threshold reduced to 0.25)")
    print("✅ Multi-criteria phone screen detection")
    print("✅ Real-time feedback and progress indicators")
    print("✅ Automatic liveness test start when camera begins")
    print("=" * 70)
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    def on_close():
        print("Registration window closed.")
        root.quit()
    
    # Launch the improved liveness enhanced registration window
    try:
        from src.gui.add_user_window_liveness_improved import ImprovedLivenessAddUserWindow
        
        window = tk.Toplevel(root)
        app = ImprovedLivenessAddUserWindow(window, on_close_callback=on_close)
        window.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error launching improved liveness detection window: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
