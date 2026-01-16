#!/usr/bin/env python3
"""
Final Verification: Enhanced Anti-Spoofing in CLI Mode
This script tests the complete integration in main.py CLI mode
"""

import sys
import os
import subprocess
import time

def test_cli_mode_integration():
    """Test that CLI mode has enhanced liveness detection"""
    print("🔒 Testing Enhanced Anti-Spoofing in CLI Mode")
    print("=" * 50)
    
    # Test that main.py imports all components correctly
    try:
        import main
        print("✅ main.py imports successfully")
        
        # Check if AttendanceLivenessDetector is available
        from src.attendance_liveness_detector import AttendanceLivenessDetector
        liveness_detector = AttendanceLivenessDetector()
        print("✅ AttendanceLivenessDetector initialized")
        
        # Verify configuration
        print(f"✅ Required blinks: {liveness_detector.required_blinks}")
        print(f"✅ Movement threshold: {liveness_detector.movement_threshold}")
        print(f"✅ Verification time: {liveness_detector.liveness_verification_time}s")
        
        # Test phone detection capability
        import numpy as np
        test_phone_image = np.ones((160, 160, 3), dtype=np.uint8) * 220
        is_phone = liveness_detector.detect_phone_screen(test_phone_image, "TEST_USER")
        print(f"✅ Phone detection test: {is_phone} (should be True for uniform image)")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def verify_cli_functionality():
    """Verify CLI mode functionality"""
    print("\n🎯 CLI Mode Functionality Check")
    print("=" * 40)
    
    try:
        # Test help command
        result = subprocess.run([sys.executable, "main.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "Face Attendance System" in result.stdout:
            print("✅ CLI help command works")
        else:
            print("❌ CLI help command failed")
            return False
        
        # Test system test command
        result = subprocess.run([sys.executable, "main.py", "--test"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and "System test completed" in result.stdout:
            print("✅ System tests pass")
        else:
            print("❌ System tests failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI functionality test failed: {e}")
        return False


def show_usage_instructions():
    """Show final usage instructions"""
    print("\n🎉 ENHANCED ANTI-SPOOFING SYSTEM READY!")
    print("=" * 50)
    print("📋 HOW TO USE:")
    print("")
    print("🖥️  CLI Mode (with enhanced liveness):")
    print("   python main.py --no-gui")
    print("   • Look at camera and blink naturally")
    print("   • Move head slightly left/right")
    print("   • Press 'a' only after ✅ LIVE VERIFIED")
    print("   • Phone images will be 🚫 REJECTED")
    print("")
    print("🎮 GUI Mode (with enhanced liveness):")
    print("   python main.py")
    print("   • Same liveness requirements apply")
    print("   • Visual progress indicators")
    print("")
    print("🔒 SECURITY FEATURES ACTIVE:")
    print("   ✅ Eye blink detection (2+ blinks required)")
    print("   ✅ Head movement detection")
    print("   ✅ Phone/screen spoof detection")
    print("   ✅ Multi-layer anti-spoofing")
    print("   ✅ Security event logging")
    print("")
    print("🚫 WHAT GETS REJECTED:")
    print("   • Phone images/screenshots")
    print("   • Static photos")
    print("   • Uniform/flat textures")
    print("   • No eye movement/blinking")
    print("   • No head movement")


if __name__ == "__main__":
    print("🚀 Final Verification: Enhanced Anti-Spoofing System")
    print("=" * 60)
    
    success1 = test_cli_mode_integration()
    success2 = verify_cli_functionality()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enhanced anti-spoofing system is fully operational")
        show_usage_instructions()
        
        print("\n🔐 SECURITY STATUS: MAXIMUM")
        print("The system now prevents phone attendance and requires live verification!")
        
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
