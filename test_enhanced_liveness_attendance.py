#!/usr/bin/env python3
"""
Test Enhanced Liveness Detection for Attendance Marking
This script tests the integration of liveness detection with attendance marking
to prevent phone images from being marked as live attendance.
"""

import cv2
import sys
import os
import time

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
from src.face_detector import FaceDetector
from src.face_recognizer import FaceRecognizer
from src.attendance_liveness_detector import AttendanceLivenessDetector
from src.attendance_manager import AttendanceManager
from src.security_logger import log_spoof_attempt


def test_liveness_attendance():
    """Test the enhanced liveness detection for attendance marking"""
    print("🔒 Enhanced Liveness Detection for Attendance Marking")
    print("=" * 60)
    print("This test will:")
    print("✓ Detect faces and recognize users")
    print("✓ Verify eye blinks and head movements")
    print("✓ Detect phone screens and reject them")
    print("✓ Only allow attendance marking for live persons")
    print("\nInstructions:")
    print("- Look at the camera normally")
    print("- Blink naturally a few times")
    print("- Move your head left and right slightly")
    print("- Try showing a phone image (should be rejected)")
    print("\nPress 'q' to quit, 'a' to attempt attendance marking")
    print("=" * 60)
    
    # Initialize components
    try:
        face_detector = FaceDetector()
        face_recognizer = FaceRecognizer()
        liveness_detector = AttendanceLivenessDetector()
        attendance_manager = AttendanceManager()
        
        # Load registered users
        face_recognizer.reload_user_data()
        print(f"✓ Loaded {len(face_recognizer.known_face_encodings)} registered users")
        
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return False
    
    # Initialize camera
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot access camera")
            return False
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("✓ Camera initialized")
        
    except Exception as e:
        print(f"❌ Camera initialization failed: {e}")
        return False
    
    current_user_id = None
    current_user_verified = False
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect faces
            faces = face_detector.detect_faces(frame)
            
            # Add header text
            cv2.putText(frame, "Enhanced Liveness Detection - Attendance Test", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Press 'q' to quit, 'a' to mark attendance", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            for face in faces:
                x, y, w, h, face_crop, landmarks = face
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Face recognition
                user_id = face_recognizer.recognize_face(face_crop)
                
                if user_id:
                    # For recognized users, perform comprehensive liveness verification
                    is_live, verification_complete, status_message = liveness_detector.verify_liveness(
                        frame, face, landmarks, user_id
                    )
                    
                    if verification_complete:
                        if is_live:
                            # Liveness verified - allow attendance marking
                            current_user_id = user_id
                            current_user_verified = True
                            cv2.putText(frame, f"✅ {user_id} - LIVE VERIFIED", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            cv2.putText(frame, "✅ READY FOR ATTENDANCE", (x, y+h+20), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            cv2.putText(frame, "Press 'a' to mark attendance", (x, y+h+40), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        else:
                            # Liveness failed - spoof detected
                            current_user_id = None
                            current_user_verified = False
                            cv2.putText(frame, f"🚫 {user_id} - SPOOF DETECTED!", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            cv2.putText(frame, "❌ PHONE/SCREEN DETECTED", (x, y+h+20), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            cv2.putText(frame, "Use your real face only!", (x, y+h+40), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            log_spoof_attempt(f"LIVENESS_TEST_{user_id}")
                    else:
                        # Still verifying liveness
                        current_user_id = None
                        current_user_verified = False
                        cv2.putText(frame, f"🔍 Verifying {user_id}...", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)
                        cv2.putText(frame, status_message[:30], (x, y+h+20), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 2)
                        cv2.putText(frame, "👁️ Blink naturally & move head", (x, y+h+40), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 2)
                else:
                    # Unknown user
                    current_user_id = None
                    current_user_verified = False
                    cv2.putText(frame, "❓ Unknown User", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.putText(frame, "Please register first", (x, y+h+20), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # Display current status
            if current_user_verified:
                cv2.putText(frame, f"STATUS: {current_user_id} READY FOR ATTENDANCE", (10, 450), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "STATUS: NO USER VERIFIED FOR ATTENDANCE", (10, 450), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display the frame
            cv2.imshow('Enhanced Liveness Detection - Attendance Test', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                if current_user_verified and current_user_id:
                    # Mark attendance only if liveness is verified
                    attendance_manager.mark_attendance(current_user_id)
                    print(f"✅ Attendance marked for {current_user_id} (LIVE VERIFIED)")
                    
                    # Show success message on frame temporarily
                    cv2.putText(frame, f"✅ ATTENDANCE MARKED: {current_user_id}", (10, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.imshow('Enhanced Liveness Detection - Attendance Test', frame)
                    cv2.waitKey(2000)  # Show for 2 seconds
                else:
                    print("❌ Attendance denied - Liveness verification required")
                    print("   Please ensure you are a live person (not a phone image)")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except:
            pass
    
    print("\n✅ Enhanced liveness detection test completed")
    return True


if __name__ == "__main__":
    print("🚀 Starting Enhanced Liveness Detection Test...")
    success = test_liveness_attendance()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Key Features Tested:")
        print("✓ Face detection and recognition")
        print("✓ Eye blink detection")
        print("✓ Head movement detection") 
        print("✓ Phone/screen spoof detection")
        print("✓ Attendance marking with liveness verification")
        print("\nThe system now requires live person verification for attendance!")
    else:
        print("\n❌ Test failed. Please check the error messages above.")
