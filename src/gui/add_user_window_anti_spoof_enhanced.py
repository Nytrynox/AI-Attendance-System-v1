# src/gui/add_user_window_anti_spoof_enhanced.py
"""
Enhanced Add User Window with Advanced Anti-Spoofing Protection
Detects live faces vs phone/photo spoofing attempts
"""

import tkinter as tk
from tkinter import messagebox
import cv2
import os
import pickle
from src.utils.image_utils import resize_image, preprocess_for_face_recognition
from src.utils.data_utils import save_attendance
from src.face_detector import FaceDetector
from src.anti_spoof import AntiSpoofingDetector
from src.utils.camera_utils import CameraManager
from datetime import datetime
import threading
import time
from PIL import Image, ImageTk


class AntiSpoofEnhancedAddUserWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Add New User - Anti-Spoofing Protection")
        self.master.geometry("1000x750")
        
        # Initialize detection models
        self.face_detector = FaceDetector()
        self.anti_spoof_detector = AntiSpoofingDetector()
        self.camera_manager = CameraManager()
        
        # Camera and detection variables
        self.cap = None
        self.camera_running = False
        self.current_frame = None
        self.face_captured = False
        self.face_encoding = None
        self.captured_frame = None
        self.user_data = None
        self._current_photo = None
        self.last_detection_result = None
        self.spoof_detection_count = 0  # Track consecutive spoof detections
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the enhanced user interface with anti-spoofing features"""
        # Main container
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel for controls
        left_panel = tk.Frame(main_frame, width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        # User info section
        info_frame = tk.LabelFrame(left_panel, text="User Information", 
                                 font=("Arial", 12, "bold"), fg="blue")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(info_frame, text="Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=5, pady=8)
        self.name_entry = tk.Entry(info_frame, font=("Arial", 11), width=25)
        self.name_entry.grid(row=0, column=1, padx=5, pady=8)
        
        tk.Label(info_frame, text="ID:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", padx=5, pady=8)
        self.id_entry = tk.Entry(info_frame, font=("Arial", 11), width=25)
        self.id_entry.grid(row=1, column=1, padx=5, pady=8)
        
        # Camera controls
        controls_frame = tk.LabelFrame(left_panel, text="Camera Controls", 
                                     font=("Arial", 12, "bold"), fg="green")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_camera_btn = tk.Button(controls_frame, text="🎥 Start Camera", 
                                        command=self.start_camera, bg="green", fg="white",
                                        font=("Arial", 11, "bold"), height=2)
        self.start_camera_btn.pack(fill=tk.X, padx=8, pady=8)
        
        self.capture_btn = tk.Button(controls_frame, text="📸 Capture Live Face", 
                                   command=self.capture_face, bg="blue", fg="white",
                                   font=("Arial", 11, "bold"), state=tk.DISABLED, height=2)
        self.capture_btn.pack(fill=tk.X, padx=8, pady=8)
        
        self.stop_camera_btn = tk.Button(controls_frame, text="⏹ Stop Camera", 
                                       command=self.stop_camera, bg="red", fg="white",
                                       font=("Arial", 11, "bold"), state=tk.DISABLED, height=2)
        self.stop_camera_btn.pack(fill=tk.X, padx=8, pady=8)
        
        # Anti-spoofing status
        antispoof_frame = tk.LabelFrame(left_panel, text="Anti-Spoofing Status", 
                                      font=("Arial", 12, "bold"), fg="red")
        antispoof_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.antispoof_status = tk.Label(antispoof_frame, text="Camera Off", 
                                       font=("Arial", 11, "bold"), fg="gray", bg="lightgray")
        self.antispoof_status.pack(fill=tk.X, padx=8, pady=8)
        
        # Save controls
        save_frame = tk.LabelFrame(left_panel, text="Save User", 
                                 font=("Arial", 12, "bold"), fg="orange")
        save_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.save_btn = tk.Button(save_frame, text="💾 Save User Registration", 
                                command=self.save_user, bg="orange", fg="white",
                                font=("Arial", 11, "bold"), state=tk.DISABLED, height=2)
        self.save_btn.pack(fill=tk.X, padx=8, pady=8)
        
        # Status section
        status_frame = tk.LabelFrame(left_panel, text="System Log", 
                                   font=("Arial", 12, "bold"))
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_frame, height=10, width=35, wrap=tk.WORD,
                                 font=("Consolas", 9), state=tk.DISABLED)
        status_scrollbar = tk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Right panel for camera feed
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Camera display
        camera_frame = tk.LabelFrame(right_panel, text="Live Camera Feed - Anti-Spoofing Active", 
                                   font=("Arial", 12, "bold"))
        camera_frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_label = tk.Label(camera_frame, text="Camera not started\n\nClick 'Start Camera' to begin", 
                                   bg="black", fg="white", width=50, height=25, 
                                   font=("Arial", 12))
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Enhanced legend
        legend_frame = tk.Frame(right_panel)
        legend_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(legend_frame, text="Detection Status:", font=("Arial", 11, "bold")).pack()
        
        legend_row1 = tk.Frame(legend_frame)
        legend_row1.pack(pady=5)
        tk.Label(legend_row1, text="🟢", font=("Arial", 14)).pack(side=tk.LEFT)
        tk.Label(legend_row1, text="LIVE FACE - Ready to Register", 
               fg="green", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        legend_row2 = tk.Frame(legend_frame)
        legend_row2.pack(pady=2)
        tk.Label(legend_row2, text="🔴", font=("Arial", 14)).pack(side=tk.LEFT)
        tk.Label(legend_row2, text="SPOOF DETECTED - Phone/Photo/Screen", 
               fg="red", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        legend_row3 = tk.Frame(legend_frame)
        legend_row3.pack(pady=2)
        tk.Label(legend_row3, text="🟡", font=("Arial", 14)).pack(side=tk.LEFT)
        tk.Label(legend_row3, text="Processing - Please wait", 
               fg="orange", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(right_panel, text="❌ Close", command=self.close_window, 
                            bg="gray", font=("Arial", 10, "bold"))
        close_btn.pack(pady=10)
        
        # Initialize status
        self.update_status("🚀 System Ready! Enter user details and start camera.")
        self.update_status("🔒 Anti-spoofing protection is ACTIVE")
        
    def update_status(self, message):
        """Update status display with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def start_camera(self):
        """Start the camera with anti-spoofing detection"""
        if self.camera_running:
            return
            
        self.cap = self.camera_manager.initialize_camera()
        if not self.cap:
            messagebox.showerror("Camera Error", 
                               "Cannot access camera!\n\n"
                               "Please check:\n"
                               "• Camera is connected\n"
                               "• Camera is not used by another app\n"
                               "• Camera drivers are installed")
            return
            
        self.camera_running = True
        self.start_camera_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.NORMAL)
        
        self.antispoof_status.config(text="🔒 ANTI-SPOOFING ACTIVE", bg="lightgreen", fg="green")
        
        self.update_status("📹 Camera started - Live anti-spoofing detection active")
        
        # Start camera processing thread
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        
    def camera_loop(self):
        """Main camera processing loop with real-time anti-spoofing"""
        while self.camera_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    break
                    
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    continue
                    
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Process frame with enhanced anti-spoofing feedback
                frame_with_detection = self.process_frame_with_antispoof(frame)
                
                # Display processed frame
                self.display_frame(frame_with_detection)
                
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Camera loop error: {e}")
                break
                
    def process_frame_with_antispoof(self, frame):
        """Process frame with enhanced anti-spoofing visual feedback"""
        frame_copy = frame.copy()
        detection_status = "No Face"
        
        try:
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            if faces:
                for face in faces:
                    # Extract face coordinates and crop
                    face_crop, left, top, right, bottom = self.extract_face_data(face, frame)
                    
                    if face_crop is None:
                        continue
                        
                    # Perform anti-spoofing detection
                    try:
                        is_real = self.anti_spoof_detector.check_if_real(face_crop)
                        self.last_detection_result = is_real
                        
                        if is_real:
                            # LIVE FACE - Green with pulsing effect
                            pulse = int(cv2.getTickCount() / cv2.getTickFrequency() * 3) % 2
                            color = (0, 255, 0) if pulse else (0, 200, 0)
                            label = "✅ LIVE FACE - Ready to Register"
                            detection_status = "Live Face Detected"
                            self.spoof_detection_count = 0
                            
                        else:
                            # SPOOFING DETECTED - Red with blinking effect
                            self.spoof_detection_count += 1
                            blink = int(cv2.getTickCount() / cv2.getTickFrequency() * 5) % 2
                            color = (0, 0, 255) if blink else (0, 0, 150)
                            label = "🚫 SPOOF DETECTED - PHONE/PHOTO"
                            detection_status = "Spoofing Attempt"
                            
                    except Exception:
                        # Processing error
                        color = (0, 165, 255)
                        label = "⚠ Processing... Please wait"
                        detection_status = "Processing"
                    
                    # Draw enhanced bounding box
                    thickness = 8 if not is_real else 5
                    cv2.rectangle(frame_copy, (left, top), (right, bottom), color, thickness)
                    
                    # Draw main label
                    self.draw_label(frame_copy, label, (left, top), color)
                    
                    # Add warning for spoofing
                    if not is_real and self.last_detection_result is not None:
                        warning = "⚠ CANNOT REGISTER SPOOF ⚠"
                        self.draw_label(frame_copy, warning, (left, bottom + 10), (0, 0, 255))
                    
                    # Store frame for capture
                    self.current_frame = frame.copy()
                    
            else:
                # No faces detected
                cv2.putText(frame_copy, "👤 Please position your face in camera", 
                          (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                detection_status = "No Face"
                self.last_detection_result = None
                
        except Exception as e:
            cv2.putText(frame_copy, f"Error: {str(e)[:40]}", (30, 50), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            detection_status = "Error"
            
        # Update anti-spoofing status
        self.update_antispoof_status(detection_status)
        
        return frame_copy
    
    def extract_face_data(self, face, frame):
        """Extract face crop and coordinates from detected face"""
        try:
            if isinstance(face, tuple) and len(face) >= 4:
                if len(face) == 6:  # (x, y, w, h, face_crop, landmarks)
                    x, y, w, h = face[:4]
                    left, top, right, bottom = x, y, x + w, y + h
                    face_crop = face[4] if face[4] is not None else frame[y:y+h, x:x+w]
                else:  # (left, top, right, bottom)
                    left, top, right, bottom = face
                    face_crop = frame[top:bottom, left:right]
            elif hasattr(face, 'left'):  # dlib rectangle
                left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
                face_crop = frame[top:bottom, left:right]
            else:
                return None, 0, 0, 0, 0
                
            return face_crop, left, top, right, bottom
        except Exception:
            return None, 0, 0, 0, 0
    
    def draw_label(self, frame, text, position, color):
        """Draw enhanced label with background"""
        x, y = position
        font_scale = 0.8
        thickness = 2
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # Draw background rectangle
        cv2.rectangle(frame, (x, y - text_height - 10), 
                     (x + text_width + 10, y + 5), color, -1)
        
        # Draw text
        cv2.putText(frame, text, (x + 5, y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    def update_antispoof_status(self, detection_status):
        """Update the anti-spoofing status display"""
        if detection_status == "Live Face Detected":
            self.antispoof_status.config(text="🟢 LIVE FACE DETECTED", bg="lightgreen", fg="green")
        elif detection_status == "Spoofing Attempt":
            self.antispoof_status.config(text="🔴 SPOOFING DETECTED", bg="lightcoral", fg="red")
        elif detection_status == "Processing":
            self.antispoof_status.config(text="🟡 PROCESSING...", bg="lightyellow", fg="orange")
        else:
            self.antispoof_status.config(text="⚪ NO FACE DETECTED", bg="lightgray", fg="gray")
    
    def display_frame(self, frame):
        """Convert and display frame in GUI"""
        try:
            # Resize for display
            height, width = frame.shape[:2]
            display_width = 680
            display_height = int(height * (display_width / width))
            
            frame_resized = cv2.resize(frame, (display_width, display_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            self._current_photo = photo
            self.master.after(0, lambda p=photo: self.update_camera_display(p))
            
        except Exception as e:
            print(f"Display error: {e}")
            
    def update_camera_display(self, photo):
        """Update camera display safely"""
        try:
            if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
        except tk.TclError:
            self.camera_running = False
    
    def capture_face(self):
        """Capture face with enhanced anti-spoofing validation"""
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()
        
        if not name or not user_id:
            messagebox.showerror("Input Error", "Please enter both Name and ID!")
            return
            
        if self.current_frame is None:
            messagebox.showerror("Camera Error", "No camera frame available!")
            return
            
        # Validate current detection result
        if self.last_detection_result is None:
            messagebox.showwarning("No Face", "No face detected! Please position your face in the camera.")
            self.update_status("❌ Capture failed - No face detected")
            return
            
        if not self.last_detection_result:
            # SPOOFING DETECTED - Show detailed message
            spoof_message = (
                "🚫 SPOOFING DETECTED - REGISTRATION BLOCKED! 🚫\n\n"
                "The system detected you are using:\n"
                "• 📱 Phone/tablet photo\n"
                "• 🖼 Printed image\n"
                "• 💻 Screen/video display\n"
                "• 🎭 Other spoofing method\n\n"
                "❌ This is NOT allowed for security reasons!\n\n"
                "To register successfully:\n"
                "✅ Use your REAL LIVE FACE\n"
                "✅ Ensure good lighting\n"
                "✅ Look directly at camera\n"
                "✅ Remove glasses/masks if needed\n"
                "✅ Wait for GREEN status indicator"
            )
            messagebox.showerror("🚫 Spoofing Blocked", spoof_message)
            self.update_status(f"🚫 SPOOFING BLOCKED - User {user_id} registration denied for security")
            
            # Log spoofing attempt
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_status(f"⚠ [{timestamp}] Spoofing attempt logged - Count: {self.spoof_detection_count}")
            return
            
        try:
            # Process face for registration
            faces = self.face_detector.detect_faces(self.current_frame)
            if not faces:
                messagebox.showwarning("No Face", "No face detected in current frame!")
                return
                
            # Extract face crop
            face_crop, _, _, _, _ = self.extract_face_data(faces[0], self.current_frame)
            if face_crop is None:
                messagebox.showerror("Error", "Could not extract face data!")
                return
                
            # Final anti-spoofing check
            final_check = self.anti_spoof_detector.check_if_real(face_crop)
            if not final_check:
                messagebox.showerror("Final Check Failed", 
                                   "Final anti-spoofing check failed! Please try again with your live face.")
                return
                
            # Get face encoding
            face_encodings = preprocess_for_face_recognition(face_crop)
            if not face_encodings:
                messagebox.showerror("Error", "Could not extract face features!")
                return
                
            # Success - face captured
            self.face_encoding = face_encodings[0]
            self.captured_frame = self.current_frame.copy()
            self.face_captured = True
            
            success_message = (
                f"✅ LIVE FACE CAPTURED SUCCESSFULLY! ✅\n\n"
                f"👤 User: {name}\n"
                f"🆔 ID: {user_id}\n\n"
                f"✅ Anti-spoofing: PASSED\n"
                f"✅ Face validation: PASSED\n"
                f"✅ Feature extraction: COMPLETED\n\n"
                f"Ready to save registration!"
            )
            
            self.update_status(f"✅ Live face captured for {name} (ID: {user_id})")
            self.save_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("🎉 Capture Success", success_message)
            
        except Exception as e:
            error_msg = f"Capture failed: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status(f"❌ {error_msg}")
    
    def save_user(self):
        """Save the captured user with anti-spoofing verification"""
        if not self.face_captured:
            messagebox.showerror("Error", "No face captured yet!")
            return
            
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()
        
        try:
            # Create user directory
            user_dir = os.path.join("data/registered_users", user_id)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
                
            # Save image with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = os.path.join(user_dir, f"{user_id}_{timestamp}.jpg")
            
            resized_frame = resize_image(self.captured_frame)
            cv2.imwrite(image_path, resized_frame)
            
            # Save user info with anti-spoof verification marker
            user_info = {
                'id': user_id,
                'name': name,
                'encoding': self.face_encoding,
                'image_path': image_path,
                'timestamp': timestamp,
                'anti_spoof_verified': True,  # Mark as anti-spoof verified
                'registration_method': 'enhanced_anti_spoof'
            }
            
            # Save encoding
            encoding_file = os.path.join(user_dir, f"{user_id}_encoding.pkl")
            with open(encoding_file, "wb") as f:
                pickle.dump(user_info, f)
                
            self.user_data = user_info
            
            # Update attendance system
            save_attendance(user_id, name)
            
            success_msg = (
                f"🎉 USER REGISTERED SUCCESSFULLY! 🎉\n\n"
                f"👤 Name: {name}\n"
                f"🆔 ID: {user_id}\n"
                f"🔒 Anti-spoofing: VERIFIED\n"
                f"📅 Registered: {timestamp}\n\n"
                f"✅ User can now use the attendance system!"
            )
            
            self.update_status(f"🎉 User {name} registered successfully with anti-spoof protection")
            messagebox.showinfo("🎉 Registration Complete", success_msg)
            
            # Reset for next user
            self.reset_for_next_user()
            
        except Exception as e:
            error_msg = f"Failed to save user: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status(f"❌ {error_msg}")
    
    def reset_for_next_user(self):
        """Reset interface for next user registration"""
        self.name_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        self.face_captured = False
        self.face_encoding = None
        self.captured_frame = None
        self.user_data = None
        self.last_detection_result = None
        self.spoof_detection_count = 0
        self.save_btn.config(state=tk.DISABLED)
        self.update_status("🔄 Ready for next user registration")
        
    def stop_camera(self):
        """Stop camera and cleanup"""
        self.camera_running = False
        
        if self.cap:
            self.camera_manager.release_camera(self.cap)
            self.cap = None
            
        self.start_camera_btn.config(state=tk.NORMAL)
        self.capture_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.DISABLED)
        
        self.camera_label.configure(image="", text="Camera stopped\n\nClick 'Start Camera' to begin")
        self.camera_label.image = None
        
        self.antispoof_status.config(text="Camera Off", bg="lightgray", fg="gray")
        
        self.update_status("📹 Camera stopped")
        
    def close_window(self):
        """Close window with cleanup"""
        self.stop_camera()
        
        # Call callback if provided
        if hasattr(self, 'on_close_callback') and self.on_close_callback:
            try:
                self.on_close_callback()
            except Exception:
                pass
    
        if self.master.winfo_class() == 'Tk':
            self.master.quit()
        self.master.destroy()


def launch_anti_spoof_enhanced_window(parent=None, on_close_callback=None):
    """Launch the enhanced anti-spoofing registration window"""
    if parent:
        window = tk.Toplevel(parent)
        window.transient(parent)
        window.grab_set()
    else:
        window = tk.Tk()
    
    app = AntiSpoofEnhancedAddUserWindow(window)
    
    if on_close_callback:
        app.on_close_callback = on_close_callback
    
    window.protocol("WM_DELETE_WINDOW", app.close_window)
    
    if not parent:
        window.mainloop()
    
    return app


if __name__ == "__main__":
    # Test the enhanced anti-spoofing window
    print("Testing Enhanced Anti-Spoofing Registration Window")
    launch_anti_spoof_enhanced_window()
