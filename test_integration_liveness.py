"""
Integration test for the enhanced liveness detection system
Tests the integration with the main attendance system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from src.gui.main_window_complete import MainWindow

def main():
    print("🔗 Testing Enhanced Liveness Detection Integration")
    print("=" * 60)
    print("📋 This test launches the main attendance system to verify")
    print("   that the improved liveness detection integrates properly.")
    print("=" * 60)
    
    # Create and run the main application
    root = tk.Tk()
    app = MainWindow(root)
    
    print("✅ Main window launched successfully!")
    print("💡 To test enhanced liveness detection:")
    print("   1. Click 'Add New User'")
    print("   2. The improved liveness window should open")
    print("   3. Click 'Start Camera' to begin automatic liveness testing")
    print("   4. Follow the real-time instructions for blinking and head movement")
    print("   5. System should handle spoofing detection automatically")
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Integration test completed")

if __name__ == "__main__":
    main()
