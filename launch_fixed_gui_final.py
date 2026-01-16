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
        # Import and run the fixed GUI
        from src.gui.main_window_liveness_attendance import main as run_fixed_gui
        
        print("[INFO] All syntax errors have been fixed!")
        print("[INFO] Starting the enhanced liveness GUI...")
        
        # Run the application
        run_fixed_gui()
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
