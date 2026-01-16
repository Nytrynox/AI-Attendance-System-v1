# demo_liveness_features.py
"""
Demonstration script showing the enhanced liveness detection features
"""

import numpy as np
import time
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.attendance_liveness_detector import AttendanceLivenessDetector
from src.anti_spoof_enhanced import EnhancedAntiSpoofingDetector


def demo_phone_detection():
    """Demonstrate phone screen detection capabilities"""
    print("\n🔒 PHONE DETECTION DEMO")
    print("="*40)
    
    anti_spoof = EnhancedAntiSpoofingDetector()
    
    # Simulate different types of images
    test_cases = [
        "Real face (natural lighting)",
        "Phone screen (uniform lighting)",
        "Photo print (flat texture)",
        "Digital display (pixel patterns)"
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n{i+1}. Testing: {case}")
        
        # Create synthetic test image
        if "real face" in case.lower():
            # Simulate real face with natural variations
            img = np.random.randint(80, 180, (160, 160, 3), dtype=np.uint8)
            # Add noise and texture variations
            noise = np.random.randint(-30, 30, (160, 160, 3), dtype=np.int16)
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
        elif "phone" in case.lower():
            # Simulate phone screen with uniform lighting
            img = np.full((160, 160, 3), [120, 130, 140], dtype=np.uint8)
            # Add minimal variation
            img += np.random.randint(-5, 5, (160, 160, 3), dtype=np.int8)
            
        elif "photo" in case.lower():
            # Simulate printed photo with flat texture
            img = np.full((160, 160, 3), [100, 110, 100], dtype=np.uint8)
            img += np.random.randint(-10, 10, (160, 160, 3), dtype=np.int8)
            
        else:  # digital display
            # Simulate digital display with pixel patterns
            img = np.zeros((160, 160, 3), dtype=np.uint8)
            for y in range(0, 160, 4):
                for x in range(0, 160, 4):
                    color = [120, 130, 125]
                    img[y:y+2, x:x+2] = color
        
        # Test phone detection
        is_phone, confidence, details = anti_spoof.detect_phone_screen(img)
        
        print(f"   Result: {'📱 PHONE DETECTED' if is_phone else '👤 REAL FACE'}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Indicators triggered: {details.get('total_indicators', 0)}")
        
        # Show key detection criteria
        if 'texture_smooth' in details:
            print(f"   - Texture smoothness: {'✓' if details['texture_smooth'] else '✗'}")
        if 'edges_sparse' in details:
            print(f"   - Edge sparsity: {'✓' if details['edges_sparse'] else '✗'}")
        if 'color_uniform' in details:
            print(f"   - Color uniformity: {'✓' if details['color_uniform'] else '✗'}")


def demo_liveness_detection():
    """Demonstrate liveness detection features"""
    print("\n👁️ LIVENESS DETECTION DEMO")
    print("="*40)
    
    liveness_detector = AttendanceLivenessDetector()
    
    print("Liveness Detection Features:")
    print("• Eye blink detection using Eye Aspect Ratio")
    print("• Head movement tracking")
    print("• Multi-frame verification (3 seconds)")
    print("• Automatic phone screen rejection")
    print("• Real-time status feedback")    
    print("\nConfiguration:")
    print(f"• Required blinks: {liveness_detector.required_blinks}")
    print(f"• Blink threshold: {liveness_detector.blink_threshold}")
    print(f"• Movement threshold: {liveness_detector.movement_threshold}")
    print(f"• Verification time: {liveness_detector.liveness_verification_time}s")
    
    # Simulate liveness verification process
    print("\nSimulating verification process for user 'DEMO_USER':")
    
    user_id = "DEMO_USER"
    liveness_detector.initialize_user_tracking(user_id)
    
    # Simulate frames over time
    for frame_num in range(100):
        # Create dummy frame and face data
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_face = (100, 100, 200, 200)  # x, y, w, h
        
        # Simulate blinks every 15-20 frames
        if frame_num % 18 == 0:
            # Simulate a blink by adding to blink count
            data = liveness_detector.user_liveness_data[user_id]
            data['blink_count'] += 1
            data['last_blink_time'] = time.time()
        
        # Simulate movement by varying face position
        if frame_num > 30:
            movement_x = 100 + int(20 * np.sin(frame_num * 0.1))
            movement_y = 100 + int(15 * np.cos(frame_num * 0.08))
            dummy_face = (movement_x, movement_y, 200, 200)
        
        # Check liveness
        is_live, complete, status = liveness_detector.verify_liveness(
            dummy_frame, dummy_face, None, user_id)
        
        # Show progress every 20 frames
        if frame_num % 20 == 0:
            data = liveness_detector.user_liveness_data[user_id]
            elapsed = time.time() - data['start_time']
            print(f"   Frame {frame_num:3d}: Blinks:{data['blink_count']}/2, "
                  f"Movement:{'✓' if data['movement_detected'] else '⏳'}, "
                  f"Time:{elapsed:.1f}s")
        
        if complete:
            print(f"\n{'✅ VERIFICATION SUCCESSFUL' if is_live else '❌ VERIFICATION FAILED'}")
            print(f"Final status: {status}")
            break
        
        time.sleep(0.02)  # Simulate frame rate


def demo_integration_flow():
    """Demonstrate the complete integration flow"""
    print("\n🔄 INTEGRATION FLOW DEMO")
    print("="*40)
    
    print("Complete Attendance Marking Process:")
    print("1. 📷 Face Detection")
    print("2. 🚫 Anti-Spoofing Check (Phone Detection)")
    print("3. 👤 Face Recognition")
    print("4. 👁️ Liveness Verification")
    print("5. ✅ Attendance Marking")
    
    print("\nFlow Details:")
    print("• If phone detected → Immediate rejection with visual feedback")
    print("• If unknown person → No action taken")
    print("• If known person → Start automatic liveness verification")
    print("• During verification → Show progress and status")
    print("• If liveness fails → Reset and allow retry")
    print("• If liveness passes → Mark attendance with success feedback")
    
    print("\nVisual Feedback System:")
    print("🔴 Red border + warnings = Phone/spoof detected")
    print("🟡 Orange border + progress = Liveness verification in progress")
    print("🟢 Green border + checkmark = Attendance marked successfully")
    print("🔵 Blue border + timer = Cooldown period active")


def main():
    """Run all demonstrations"""
    print("🔒 ENHANCED LIVENESS ATTENDANCE SYSTEM DEMO")
    print("="*60)
    print("Demonstrating automatic liveness detection features for attendance marking")
    
    try:
        demo_phone_detection()
        demo_liveness_detection()
        demo_integration_flow()
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETE!")
        print("\nKey Features Demonstrated:")
        print("• 📱 Advanced phone screen detection")
        print("• 👁️ Automatic eye blink verification")
        print("• 🔄 Head movement detection")
        print("• ⏱️ Real-time verification progress")
        print("• 🎯 Complete integration workflow")
        
        print("\nTo use the enhanced system:")
        print("1. Run: python launch_liveness_attendance.py")
        print("2. Click 'Start Attendance Mode'")
        print("3. Look at camera naturally - system handles verification automatically")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        print("Some features may require additional dependencies")


if __name__ == "__main__":
    main()
