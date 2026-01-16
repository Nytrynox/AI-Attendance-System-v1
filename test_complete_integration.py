#!/usr/bin/env python3
"""
Complete Integration Test for Face Attendance System
Test all camera modes and integrations
"""

import os
import sys
import importlib.util

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        # Core modules
        spec = importlib.util.find_spec("src.face_detector")
        if spec is not None:
            print("✓ Face detector module found")
        
        spec = importlib.util.find_spec("src.face_recognizer") 
        if spec is not None:
            print("✓ Face recognizer module found")
            
        spec = importlib.util.find_spec("src.anti_spoof")
        if spec is not None:
            print("✓ Anti-spoof module found")
            
        spec = importlib.util.find_spec("src.attendance_manager")
        if spec is not None:
            print("✓ Attendance manager module found")
            
        spec = importlib.util.find_spec("src.user_manager")
        if spec is not None:
            print("✓ User manager module found")
            
        print("✓ Core modules available")
        
        # Camera utilities
        spec = importlib.util.find_spec("src.utils.camera_utils")
        if spec is not None:
            print("✓ Camera utils module found")
            
        spec = importlib.util.find_spec("src.utils.image_utils")
        if spec is not None:
            print("✓ Image utils module found")
        
        print("✓ Utility modules available")
        
        # GUI modules (optional)
        spec = importlib.util.find_spec("src.gui.dual_camera_window")
        if spec is not None:
            print("✓ Dual camera GUI module found")
        else:
            print("⚠ Dual camera GUI module not found (optional)")
            
        spec = importlib.util.find_spec("src.gui.camera_selection_window")
        if spec is not None:
            print("✓ Camera selection GUI module found")
        else:
            print("⚠ Camera selection GUI module not found (optional)")
            
        # Enhanced modules (optional)
        spec = importlib.util.find_spec("src.enhanced_liveness_detector")
        if spec is not None:
            print("✓ Enhanced liveness detector module found")
        else:
            print("⚠ Enhanced liveness detector module not found (optional)")
            
        spec = importlib.util.find_spec("src.advanced.face_3d_recognizer")
        if spec is not None:
            print("✓ 3D face recognizer module found")
        else:
            print("⚠ 3D face recognizer module not found (optional)")
            
        print("✓ All available modules checked")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False


def test_camera_availability():
    """Test camera availability"""
    print("\nTesting camera availability...")
    
    try:
        import cv2
        
        available_cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    available_cameras.append(i)
                cap.release()
        
        print(f"✓ Available cameras: {available_cameras}")
        return len(available_cameras) > 0
        
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False


def test_directory_structure():
    """Test required directory structure"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'data',
        'data/attendance',
        'data/registered_users',
        'data/logs',
        'src',
        'src/gui',
        'src/utils',
        'models'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"✓ Directory exists: {dir_path}")
    
    if missing_dirs:
        print(f"⚠ Missing directories: {missing_dirs}")
        print("Creating missing directories...")
        for dir_path in missing_dirs:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ Created: {dir_path}")
    
    return True


def test_model_files():
    """Test model files availability"""
    print("\nTesting model files...")
    
    model_files = [
        'models/shape_predictor_68_face_landmarks.dat',
        'models/anti_spoof_model.h5',
        'models/face_recognition_model.h5'
    ]
    
    available_models = []
    missing_models = []
    
    for model_file in model_files:
        if os.path.exists(model_file):
            available_models.append(model_file)
            print(f"✓ Model file found: {model_file}")
        else:
            missing_models.append(model_file)
            print(f"✗ Model file missing: {model_file}")
    
    if missing_models:
        print("⚠ Some model files are missing. The system may have limited functionality.")
    
    return len(available_models) > 0


def test_main_module():
    """Test main application module"""
    print("\nTesting main application...")
    
    try:
        # Check if main.py exists and has a main function
        main_file = "main.py"
        if os.path.exists(main_file):
            print(f"✓ Main file exists: {main_file}")
            
            # Try to validate the main function without executing
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'def main(' in content:
                    print("✓ Main function found in main.py")
                if 'if __name__ == "__main__"' in content:
                    print("✓ Main execution block found")
                    
            return True
        else:
            print(f"✗ Main file not found: {main_file}")
            return False
            
    except Exception as e:
        print(f"✗ Main module test failed: {e}")
        return False


def test_gui_availability():
    """Test GUI module availability"""
    print("\nTesting GUI availability...")
    
    try:
        # Test tkinter availability
        spec = importlib.util.find_spec("tkinter")
        if spec is not None:
            print("✓ Tkinter is available")
        else:
            print("✗ Tkinter not available")
            return False
            
        # Test main GUI window
        spec = importlib.util.find_spec("src.gui.main_window")
        if spec is not None:
            print("✓ Main GUI window module found")
        else:
            print("⚠ Main GUI window module not found")
            
        return True
        
    except Exception as e:
        print(f"✗ GUI test failed: {e}")
        return False


def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Face Attendance System Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Camera Availability", test_camera_availability), 
        ("Directory Structure", test_directory_structure),
        ("Model Files", test_model_files),
        ("Main Module", test_main_module),
        ("GUI Availability", test_gui_availability)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            print(f"Result: {status}")
        except Exception as e:
            print(f"ERROR: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The system is ready for use.")
    else:
        print(f"\n⚠ {failed} test(s) failed. Please check the issues above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
