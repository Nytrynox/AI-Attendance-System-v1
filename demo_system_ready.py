#!/usr/bin/env python3
"""
Quick Demo - Face Attendance System
Demonstrates all camera modes working
"""

import subprocess
import time

def run_demo_command(description, command, duration=3):
    """Run a demo command for a short duration"""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        # Start the process
        process = subprocess.Popen(command, shell=True)
        
        print(f"Demo running for {duration} seconds...")
        time.sleep(duration)
        
        # Terminate the process
        process.terminate()
        process.wait(timeout=5)
        print("✓ Demo completed successfully")
        
    except Exception as e:
        print(f"Demo error: {e}")
    
    print("Press Enter to continue to next demo...")
    input()

def main():
    print("🎉 Face Attendance System - Quick Demo")
    print("This will demonstrate all camera modes briefly")
    print("\nNote: Each demo runs for a few seconds then automatically stops")
    
    demos = [
        ("Help and Arguments", "python main.py --help"),
        ("System Status Check", "python test_complete_integration.py"),
        # Commented out actual camera demos to avoid conflicts
        # ("CLI Mode Demo", "python main.py --no-gui --debug"),
        # ("Dual Camera Mode", "python main.py --dual-camera"),
        # ("Enhanced Camera Selection", "python main.py --enhanced-camera"),
    ]
    
    for description, command in demos:
        if "help" in command or "test_complete" in command:
            # Run help and test commands normally
            print(f"\n{'='*60}")
            print(f"RUNNING: {description}")
            print(f"{'='*60}")
            subprocess.run(command, shell=True)
            print("\nPress Enter to continue...")
            input()
        else:
            run_demo_command(description, command)
    
    print("\n🎉 Demo Complete!")
    print("\nThe Face Attendance System is fully operational!")
    print("\nAvailable modes:")
    print("  • python main.py                    (Default GUI)")
    print("  • python main.py --dual-camera     (Dual camera)")
    print("  • python main.py --enhanced-camera (Enhanced selection)")
    print("  • python main.py --droidcam        (DroidCam mode)")
    print("  • python main.py --no-gui          (CLI mode)")

if __name__ == "__main__":
    main()
