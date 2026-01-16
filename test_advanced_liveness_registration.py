# test_advanced_liveness_registration.py

import cv2
from src.advanced_liveness_detector import AdvancedLivenessDetector
from src.face_detector import FaceDetector

def test_registration_mode():
    """Test the advanced liveness detector in registration mode"""
    
    # Initialize detector with lenient settings for registration
    detector = AdvancedLivenessDetector(for_registration=True)
    face_detector = FaceDetector()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot access camera")
        return
    
    print("Advanced Liveness Detection - Registration Mode")
    print("=" * 50)
    print("This mode uses LENIENT thresholds to avoid false positives on real faces")
    print("Anti-spoof threshold: 0.3 (vs 0.7 for attendance)")
    print("Phone detection threshold: 0.8 (vs 0.6 for attendance)")
    print("Required blinks: 2 (vs 3 for attendance)")
    print("Required head movements: 1 (vs 2 for attendance)")
    print("\nPress 'q' to quit, 's' to start liveness test")
    
    liveness_active = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        # Detect faces
        faces = face_detector.detect_faces(frame)
        
        if faces:
            for face in faces:
                # Extract face coordinates
                if isinstance(face, tuple) and len(face) >= 4:
                    if len(face) == 6:
                        x, y, w, h = face[:4]
                        left, top, right, bottom = x, y, x + w, y + h
                    else:
                        left, top, right, bottom = face
                elif hasattr(face, 'left'):
                    left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
                else:
                    continue
                
                if liveness_active:
                    # Process with advanced liveness detector
                    results = detector.process_frame_for_liveness(frame, (left, top, right, bottom))
                    
                    # Determine color based on results
                    if results['all_passed']:
                        color = (0, 255, 0)  # Green
                        label = "✅ LIVENESS VERIFIED"
                    elif results['progress'] > 0:
                        color = (0, 255, 255)  # Yellow
                        label = f"🔒 LIVENESS: {results['progress']:.0f}%"
                    else:
                        # Check for specific issues
                        messages = results['messages']
                        if any('Phone detected' in msg for msg in messages):
                            color = (0, 0, 255)  # Red
                            label = "📱 PHONE DETECTED!"
                        elif any('Spoof' in msg for msg in messages):
                            color = (0, 0, 255)  # Red
                            label = "🚫 SPOOF DETECTED!"
                        else:
                            color = (255, 0, 0)  # Blue
                            label = "🔒 TESTING..."
                    
                    # Display messages
                    if results['messages']:
                        for i, msg in enumerate(results['messages'][-3:]):  # Show last 3 messages
                            cv2.putText(display_frame, msg, (10, 30 + i * 25), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                else:
                    # Quick check mode
                    face_crop = frame[top:bottom, left:right]
                    is_real, prediction = detector.anti_spoof_detector.predict(face_crop, debug=True, threshold=0.3)
                    is_phone = detector.detect_phone_screen(face_crop)
                    
                    if is_phone:
                        color = (0, 0, 255)  # Red
                        label = "📱 PHONE DETECTED!"
                    elif not is_real:
                        color = (0, 0, 255)  # Red
                        label = f"🚫 SPOOF ({prediction:.2f})"
                    else:
                        color = (0, 255, 0)  # Green
                        label = f"✅ REAL FACE ({prediction:.2f})"
                
                # Draw bounding box and label
                cv2.rectangle(display_frame, (left, top), (right, bottom), color, 3)
                cv2.putText(display_frame, label, (left, top - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Show liveness progress
                if liveness_active:
                    progress = detector.get_completion_percentage()
                    cv2.putText(display_frame, f"Progress: {progress:.0f}%", 
                               (left, bottom + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Instructions
        cv2.putText(display_frame, "Press 's' to start liveness test, 'q' to quit", 
                   (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("Advanced Liveness - Registration Mode", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and not liveness_active:
            liveness_active = True
            detector.reset_liveness_state()
            print("Liveness test started!")
        elif key == ord('r'):
            liveness_active = False
            detector.reset_liveness_state()
            print("Liveness test reset!")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_registration_mode()
