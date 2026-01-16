#!/usr/bin/env python3
"""
Direct test launcher for enhanced liveness GUI
This bypasses the import issue by running the file directly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 Direct Launch - Enhanced Liveness Attendance System...")
    print("="*60)
    
    try:
        # Run the GUI file directly as a script
        import subprocess
        result = subprocess.run([
            sys.executable, 
            "src/gui/main_window_liveness_attendance.py"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        print(f"[INFO] Process completed with exit code: {result.returncode}")
        
    except Exception as e:
        print(f"❌ Error running GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
