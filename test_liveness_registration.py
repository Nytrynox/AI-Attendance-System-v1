# test_liveness_registration.py
"""
Test script for the enhanced liveness detection registration system
"""

import tkinter as tk
from src.gui.add_user_window_liveness_enhanced import launch_liveness_enhanced_window

def main():
    """Test the enhanced liveness detection registration window"""
    print("🔒 Testing Advanced Liveness Detection Registration System")
    print("=" * 60)
    print("Features being tested:")
    print("✅ Eye blink detection")
    print("✅ Head movement verification") 
    print("✅ Phone spoofing detection")
    print("✅ Enhanced anti-spoofing")
    print("=" * 60)
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    def on_close():
        print("Registration window closed.")
        root.quit()
    
    # Launch the liveness enhanced registration window
    try:
        launch_liveness_enhanced_window(parent=root, on_close_callback=on_close)
        root.mainloop()
        
    except Exception as e:
        print(f"Error launching liveness detection window: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
