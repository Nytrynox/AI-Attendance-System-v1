# launch_liveness_attendance.py
"""
Launch script for the enhanced liveness attendance system
Uses the existing main window with enhanced liveness detection
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.gui.main_window_complete import CompleteMainWindow
    from src.attendance_liveness_detector import AttendanceLivenessDetector
    from src.anti_spoof_enhanced import EnhancedAntiSpoofingDetector
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)


def enhance_existing_window():
    """
    Enhance the existing CompleteMainWindow with liveness detection
    """
      # Monkey patch the CompleteMainWindow to add liveness detection
    original_init = CompleteMainWindow.__init__
    # original_process_frame = CompleteMainWindow.process_attendance_frame  # Not used
    
    def enhanced_init(self, master):
        # Call original init
        original_init(self, master)
        
        # Add liveness detector
        self.liveness_detector = AttendanceLivenessDetector()
        self.enhanced_anti_spoof = EnhancedAntiSpoofingDetector()
        
        # Update title
        self.master.title("🔒 Enhanced Liveness Facial Attendance System")
        
        print("[INFO] Enhanced liveness detection system initialized")
        print("[INFO] Features enabled:")
        print("  • Automatic eye blink detection")
        print("  • Head movement verification") 
        print("  • Advanced phone screen detection")
        print("  • Real-time liveness verification during attendance")
    
    def enhanced_process_frame(self, frame, last_recognition_time, recognition_cooldown):
        """Enhanced frame processing with automatic liveness detection"""
        frame_copy = frame.copy()
        current_time = __import__('time').time()
        
        try:
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            if not faces:
                # Clean up old tracking data
                self.liveness_detector.cleanup_old_tracking(max_age=10)
                return frame_copy
            
            for face in faces:
                # Extract face data
                if isinstance(face, tuple) and len(face) >= 4:
                    if len(face) == 6:
                        left, top, width, height = face[:4]
                        right = left + width
                        bottom = top + height
                        face_crop = face[4] if face[4] is not None else frame[top:bottom, left:right]
                    else:
                        left, top, right, bottom = face
                        face_crop = frame[top:bottom, left:right]
                else:
                    continue
                
                # Enhanced anti-spoofing check first
                is_real = self.enhanced_anti_spoof.check_if_real(face_crop)
                
                if not is_real:
                    # Enhanced spoof detection feedback
                    import cv2
                    cv2.rectangle(frame_copy, (left, top), (right, bottom), (0, 0, 255), 8)
                    cv2.putText(frame_copy, "🚫 PHONE/SCREEN DETECTED!", 
                              (left, top-60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                    cv2.putText(frame_copy, "📱 Remove phone/photo/screen", 
                              (left, top-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    cv2.putText(frame_copy, "👤 Use real live face only", 
                              (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Blinking red border for extra emphasis
                    blink = int(cv2.getTickCount() / cv2.getTickFrequency() * 8) % 2
                    if blink:
                        cv2.rectangle(frame_copy, (left-20, top-20), (right+20, bottom+20), (0, 0, 200), 12)
                    
                    self.update_status_threadsafe("🚫 SPOOF BLOCKED: Phone/screen detected! Use real face only.")
                    continue
                
                # Recognize face
                recognition_result = self.face_recognizer.recognize_face(face_crop)
                user_id, recognized_name, confidence = recognition_result
                
                if user_id and user_id in [u[0] for u in self.registered_users] and confidence > 0.7:
                    # Check attendance cooldown
                    if user_id in last_recognition_time:
                        time_since_last = current_time - last_recognition_time[user_id]
                        if time_since_last < recognition_cooldown:
                            # Still in cooldown
                            cv2.rectangle(frame_copy, (left, top), (right, bottom), (0, 255, 255), 3)
                            cv2.putText(frame_copy, f"⏳ COOLDOWN: {int(recognition_cooldown - time_since_last)}s", 
                                      (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                            continue
                    
                    # Automatic liveness verification
                    is_live, verification_complete, liveness_status = self.liveness_detector.verify_liveness(
                        frame, face, None, user_id)
                    
                    if not verification_complete:
                        # Liveness verification in progress
                        cv2.rectangle(frame_copy, (left, top), (right, bottom), (255, 165, 0), 4)
                        cv2.putText(frame_copy, "🔍 VERIFYING LIVENESS...", 
                                  (left, top-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
                        cv2.putText(frame_copy, f"{recognized_name}", 
                                  (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
                        
                        # Progress bar
                        progress_width = right - left
                        elapsed_time = current_time - self.liveness_detector.user_liveness_data[user_id]['start_time']
                        progress = min(1.0, elapsed_time / self.liveness_detector.liveness_verification_time)
                        cv2.rectangle(frame_copy, (left, bottom+5), 
                                    (left + int(progress_width * progress), bottom+15), 
                                    (255, 165, 0), -1)
                        
                        # Show detailed liveness status
                        status_parts = []
                        data = self.liveness_detector.user_liveness_data[user_id]
                        if data['blink_count'] >= self.liveness_detector.required_blinks:
                            status_parts.append("👁️ Blinks:✅")
                        else:
                            status_parts.append(f"👁️ Blinks:{data['blink_count']}/2")
                        
                        if data['movement_detected']:
                            status_parts.append("🔄 Movement:✅")
                        else:
                            status_parts.append("🔄 Movement:⏳")
                        
                        cv2.putText(frame_copy, " | ".join(status_parts), 
                                  (left, bottom+35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 165, 0), 1)
                        continue
                    
                    elif not is_live:
                        # Liveness verification failed
                        cv2.rectangle(frame_copy, (left, top), (right, bottom), (0, 140, 255), 4)
                        cv2.putText(frame_copy, "❌ LIVENESS FAILED", 
                                  (left, top-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
                        cv2.putText(frame_copy, "Blink naturally & move head", 
                                  (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 2)
                        
                        # Reset for retry
                        self.liveness_detector.reset_user_verification(user_id)
                        continue
                    
                    # Liveness verified - mark attendance
                    from src.utils.data_utils import save_attendance
                    user_name = next((u[1] for u in self.registered_users if u[0] == user_id), "Unknown")
                    save_attendance(user_id, user_name)
                    last_recognition_time[user_id] = current_time
                    
                    # Reset liveness tracking
                    self.liveness_detector.reset_user_verification(user_id)
                    
                    # Success feedback
                    cv2.rectangle(frame_copy, (left, top), (right, bottom), (0, 255, 0), 6)
                    cv2.putText(frame_copy, "✅ ATTENDANCE MARKED!", 
                              (left, top-60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 3)
                    cv2.putText(frame_copy, "🔒 Liveness Verified", 
                              (left, top-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(frame_copy, f"{user_name} (ID: {user_id})", 
                              (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Success animation
                    pulse = int(abs(cv2.getTickCount() / cv2.getTickFrequency() * 3) % 2)
                    if pulse:
                        cv2.rectangle(frame_copy, (left-5, top-5), (right+5, bottom+5), (0, 200, 0), 3)
                    
                    # Update UI
                    self.update_status_threadsafe(f"✅ Attendance marked for {user_name} - Liveness verified!")
                    
                else:
                    # Unknown face
                    cv2.rectangle(frame_copy, (left, top), (right, bottom), (128, 128, 128), 2)
                    cv2.putText(frame_copy, "❓ Unknown Person", 
                              (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 2)
        
        except Exception as e:
            print(f"Enhanced frame processing error: {e}")
        
        return frame_copy
    
    # Apply enhancements
    CompleteMainWindow.__init__ = enhanced_init
    CompleteMainWindow.process_attendance_frame = enhanced_process_frame


def main():
    """Main function to launch the enhanced attendance system"""
    print("🔒 Starting Enhanced Liveness Facial Attendance System...")
    print("="*60)
    
    # Enhance the existing window class
    enhance_existing_window()
    
    # Create and run the application
    root = tk.Tk()
    
    try:
        app = CompleteMainWindow(root)
        
        # Add additional status info
        app.update_status("🔒 Enhanced Liveness Detection Active!")
        app.update_status("System will automatically verify:")
        app.update_status("• Eye blinks (natural blinking)")
        app.update_status("• Head/body movement")
        app.update_status("• Phone screen detection")
        app.update_status("• Real-time anti-spoofing")
        app.update_status("Simply look at camera - no special actions needed!")
        
        def on_closing():
            if hasattr(app, 'camera_running') and app.camera_running:
                app.stop_attendance_mode()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("[INFO] Enhanced liveness attendance system ready!")
        print("[INFO] Click 'Start Attendance Mode' to begin automatic verification")
        
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
