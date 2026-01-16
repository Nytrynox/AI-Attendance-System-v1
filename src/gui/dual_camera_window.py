# src/gui/dual_camera_window.py

import tkinter as tk
from tkinter import messagebox
import cv2
import os
from datetime import datetime
import threading
import time
from PIL import Image, ImageTk
from src.utils.data_utils import load_registered_users, save_attendance
from src.face_detector import FaceDetector
from src.face_recognizer import FaceRecognizer
from src.anti_spoof import AntiSpoofingDetector
from src.utils.camera_utils import CameraManager
from src.gui.camera_selection_window import CameraSelectionWindow


class DualCameraWindow:
    """Dual camera window for simultaneous laptop and mobile camera operation"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Face Attendance System - Dual Camera Mode")
        self.master.geometry("1600x900")
        
        # Initialize models
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.anti_spoof_detector = AntiSpoofingDetector()
        self.camera_manager = CameraManager()
        
        # Load registered users
        self.registered_users = load_registered_users()
        self.face_recognizer.reload_user_data()
        
        # Camera variables - Left camera (Laptop)
        self.left_camera = None
        self.left_camera_config = None
        self.left_camera_running = False
        self.left_video_thread = None
        
        # Camera variables - Right camera (Mobile)
        self.right_camera = None
        self.right_camera_config = None
        self.right_camera_running = False
        self.right_video_thread = None
        
        # Attendance mode
        self.attendance_mode = False
        
        # Recognition variables
        self.last_recognition_time = {}
        self.recognition_cooldown = 5  # seconds
        
        # Statistics
        self.left_camera_stats = {"faces_detected": 0, "recognitions": 0}
        self.right_camera_stats = {"faces_detected": 0, "recognitions": 0}
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the dual camera interface"""
        # Main container
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        control_panel = tk.Frame(main_frame, height=100)
        control_panel.pack(fill=tk.X, pady=(0, 10))
        control_panel.pack_propagate(False)
        
        # Title
        title_label = tk.Label(control_panel, text="Dual Camera Face Attendance System", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=5)
        
        # Control buttons frame
        control_frame = tk.Frame(control_panel)
        control_frame.pack(pady=10)
        
        # Left camera controls
        left_control_frame = tk.LabelFrame(control_frame, text="Left Camera (Laptop)", padx=10, pady=5)
        left_control_frame.pack(side=tk.LEFT, padx=10)
        
        self.select_left_btn = tk.Button(left_control_frame, text="📹 Select Left Camera", 
                                        command=lambda: self.open_camera_selection("left"), 
                                        bg="lightblue", font=("Arial", 10))
        self.select_left_btn.pack(side=tk.TOP, pady=2)
        
        self.start_left_btn = tk.Button(left_control_frame, text="▶️ Start Left", 
                                       command=lambda: self.start_camera("left"), 
                                       state=tk.DISABLED, bg="lightgreen", font=("Arial", 10))
        self.start_left_btn.pack(side=tk.TOP, pady=2)
        
        self.stop_left_btn = tk.Button(left_control_frame, text="⏹️ Stop Left", 
                                      command=lambda: self.stop_camera("left"), 
                                      state=tk.DISABLED, bg="lightcoral", font=("Arial", 10))
        self.stop_left_btn.pack(side=tk.TOP, pady=2)
        
        # Right camera controls
        right_control_frame = tk.LabelFrame(control_frame, text="Right Camera (Mobile)", padx=10, pady=5)
        right_control_frame.pack(side=tk.LEFT, padx=10)
        
        self.select_right_btn = tk.Button(right_control_frame, text="📱 Select Right Camera", 
                                         command=lambda: self.open_camera_selection("right"), 
                                         bg="lightcyan", font=("Arial", 10))
        self.select_right_btn.pack(side=tk.TOP, pady=2)
        
        self.start_right_btn = tk.Button(right_control_frame, text="▶️ Start Right", 
                                        command=lambda: self.start_camera("right"), 
                                        state=tk.DISABLED, bg="lightgreen", font=("Arial", 10))
        self.start_right_btn.pack(side=tk.TOP, pady=2)
        
        self.stop_right_btn = tk.Button(right_control_frame, text="⏹️ Stop Right", 
                                       command=lambda: self.stop_camera("right"), 
                                       state=tk.DISABLED, bg="lightcoral", font=("Arial", 10))
        self.stop_right_btn.pack(side=tk.TOP, pady=2)
        
        # Global controls
        global_control_frame = tk.LabelFrame(control_frame, text="Global Controls", padx=10, pady=5)
        global_control_frame.pack(side=tk.LEFT, padx=20)
        
        self.start_both_btn = tk.Button(global_control_frame, text="▶️ Start Both", 
                                       command=self.start_both_cameras, 
                                       bg="lime", font=("Arial", 10, "bold"))
        self.start_both_btn.pack(side=tk.TOP, pady=2)
        
        self.stop_both_btn = tk.Button(global_control_frame, text="⏹️ Stop Both", 
                                      command=self.stop_both_cameras, 
                                      bg="red", font=("Arial", 10, "bold"))
        self.stop_both_btn.pack(side=tk.TOP, pady=2)
        
        # Mode toggle
        mode_frame = tk.Frame(global_control_frame)
        mode_frame.pack(side=tk.TOP, pady=5)
        
        self.mode_var = tk.StringVar(value="preview")
        
        preview_radio = tk.Radiobutton(mode_frame, text="Preview", variable=self.mode_var, 
                                      value="preview", command=self.on_mode_change)
        preview_radio.pack(side=tk.TOP)
        
        attendance_radio = tk.Radiobutton(mode_frame, text="Attendance", variable=self.mode_var, 
                                         value="attendance", command=self.on_mode_change)
        attendance_radio.pack(side=tk.TOP)
        
        # Register user button
        self.register_btn = tk.Button(control_frame, text="➕ Register New User", 
                                     command=self.open_register_window, 
                                     bg="lightyellow", font=("Arial", 11))
        self.register_btn.pack(side=tk.RIGHT, padx=20)
        
        # Camera display area
        camera_area = tk.Frame(main_frame)
        camera_area.pack(fill=tk.BOTH, expand=True)
        
        # Left camera panel
        left_panel = tk.LabelFrame(camera_area, text="Left Camera Feed", padx=5, pady=5)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.left_camera_label = tk.Label(left_panel, text="No left camera", 
                                         width=60, height=25, bg="black", fg="white")
        self.left_camera_label.pack(expand=True)
        
        # Left camera info
        self.left_info_label = tk.Label(left_panel, text="Camera: Not selected", 
                                       font=("Arial", 9), fg="gray")
        self.left_info_label.pack()
        
        # Right camera panel
        right_panel = tk.LabelFrame(camera_area, text="Right Camera Feed", padx=5, pady=5)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.right_camera_label = tk.Label(right_panel, text="No right camera", 
                                          width=60, height=25, bg="black", fg="white")
        self.right_camera_label.pack(expand=True)
        
        # Right camera info
        self.right_info_label = tk.Label(right_panel, text="Camera: Not selected", 
                                        font=("Arial", 9), fg="gray")
        self.right_info_label.pack()
        
        # Bottom status area
        status_area = tk.Frame(main_frame)
        status_area.pack(fill=tk.X, pady=(10, 0))
        
        # Status display
        status_frame = tk.LabelFrame(status_area, text="System Status", padx=10, pady=5)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.status_text = tk.Text(status_frame, height=6, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Statistics display
        stats_frame = tk.LabelFrame(status_area, text="Statistics", padx=10, pady=5)
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.stats_text = tk.Text(stats_frame, height=6, width=40)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Initialize status
        self.update_status("Dual camera system initialized. Select cameras to begin.")
        self.update_statistics()
        
    def open_camera_selection(self, side):
        """Open camera selection window for specified side"""
        def on_camera_selected(camera_info):
            if side == "left":
                self.left_camera_config = camera_info
                self.left_info_label.config(text=f"Camera: {camera_info['description']}")
                self.start_left_btn.config(state=tk.NORMAL)
                self.update_status(f"Left camera selected: {camera_info['description']}")
            else:  # right
                self.right_camera_config = camera_info
                self.right_info_label.config(text=f"Camera: {camera_info['description']}")
                self.start_right_btn.config(state=tk.NORMAL)
                self.update_status(f"Right camera selected: {camera_info['description']}")
                
        selection_window = tk.Toplevel(self.master)
        selection_window.title(f"Select {side.title()} Camera")
        CameraSelectionWindow(selection_window, callback=on_camera_selected)
        
    def start_camera(self, side):
        """Start camera for specified side"""
        if side == "left":
            if not self.left_camera_config:
                messagebox.showerror("Error", "Please select left camera first")
                return
                
            try:
                self.left_camera = self.camera_manager.initialize_camera_from_config(self.left_camera_config)
                
                if not self.left_camera or not self.left_camera.isOpened():
                    messagebox.showerror("Error", "Failed to start left camera")
                    return
                    
                self.left_camera_running = True
                self.start_left_btn.config(state=tk.DISABLED)
                self.stop_left_btn.config(state=tk.NORMAL)
                self.select_left_btn.config(state=tk.DISABLED)
                
                # Start video thread
                self.left_video_thread = threading.Thread(target=self.left_video_loop, daemon=True)
                self.left_video_thread.start()
                
                self.update_status(f"Left camera started: {self.left_camera_config['description']}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start left camera: {str(e)}")
                
        else:  # right
            if not self.right_camera_config:
                messagebox.showerror("Error", "Please select right camera first")
                return
                
            try:
                # Use a separate camera manager instance for right camera
                right_camera_manager = CameraManager()
                self.right_camera = right_camera_manager.initialize_camera_from_config(self.right_camera_config)
                
                if not self.right_camera or not self.right_camera.isOpened():
                    messagebox.showerror("Error", "Failed to start right camera")
                    return
                    
                self.right_camera_running = True
                self.start_right_btn.config(state=tk.DISABLED)
                self.stop_right_btn.config(state=tk.NORMAL)
                self.select_right_btn.config(state=tk.DISABLED)
                
                # Start video thread
                self.right_video_thread = threading.Thread(target=self.right_video_loop, daemon=True)
                self.right_video_thread.start()
                
                self.update_status(f"Right camera started: {self.right_camera_config['description']}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start right camera: {str(e)}")
                
    def stop_camera(self, side):
        """Stop camera for specified side"""
        if side == "left":
            self.left_camera_running = False
            
            if self.left_camera:
                self.left_camera.release()
                self.left_camera = None
                
            self.left_camera_label.config(image="", text="Left camera stopped")
            self.left_camera_label.image = None
            
            self.start_left_btn.config(state=tk.NORMAL)
            self.stop_left_btn.config(state=tk.DISABLED)
            self.select_left_btn.config(state=tk.NORMAL)
            
            self.update_status("Left camera stopped")
            
        else:  # right
            self.right_camera_running = False
            
            if self.right_camera:
                self.right_camera.release()
                self.right_camera = None
                
            self.right_camera_label.config(image="", text="Right camera stopped")
            self.right_camera_label.image = None
            
            self.start_right_btn.config(state=tk.NORMAL)
            self.stop_right_btn.config(state=tk.DISABLED)
            self.select_right_btn.config(state=tk.NORMAL)
            
            self.update_status("Right camera stopped")
            
    def start_both_cameras(self):
        """Start both cameras simultaneously"""
        if self.left_camera_config and not self.left_camera_running:
            self.start_camera("left")
            
        if self.right_camera_config and not self.right_camera_running:
            self.start_camera("right")
            
        if not self.left_camera_config and not self.right_camera_config:
            messagebox.showwarning("Warning", "Please select cameras first")
            
    def stop_both_cameras(self):
        """Stop both cameras simultaneously"""
        if self.left_camera_running:
            self.stop_camera("left")
            
        if self.right_camera_running:
            self.stop_camera("right")
            
    def on_mode_change(self):
        """Handle mode change between preview and attendance"""
        self.attendance_mode = (self.mode_var.get() == "attendance")
        mode = "Attendance Tracking" if self.attendance_mode else "Preview"
        self.update_status(f"Mode changed to: {mode}")
        
    def left_video_loop(self):
        """Video processing loop for left camera"""
        while self.left_camera_running and self.left_camera:
            try:
                ret, frame = self.left_camera.read()
                if not ret:
                    self.update_status("Error: Failed to read from left camera")
                    break
                    
                # Process frame
                processed_frame = self.process_frame(frame.copy(), "left")
                
                # Convert to display format
                display_frame = cv2.resize(processed_frame, (640, 480))
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                # Update camera display
                self.left_camera_label.config(image=photo, text="")
                self.left_camera_label.image = photo
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.update_status(f"Left camera error: {str(e)}")
                break
                
        self.stop_camera("left")
        
    def right_video_loop(self):
        """Video processing loop for right camera"""
        while self.right_camera_running and self.right_camera:
            try:
                ret, frame = self.right_camera.read()
                if not ret:
                    self.update_status("Error: Failed to read from right camera")
                    break
                    
                # Process frame
                processed_frame = self.process_frame(frame.copy(), "right")
                
                # Convert to display format
                display_frame = cv2.resize(processed_frame, (640, 480))
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                # Update camera display
                self.right_camera_label.config(image=photo, text="")
                self.right_camera_label.image = photo
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.update_status(f"Right camera error: {str(e)}")
                break
                
        self.stop_camera("right")
        
    def process_frame(self, frame, camera_side):
        """Process frame for face detection and recognition"""
        try:
            # Add camera identifier to frame
            camera_label = f"{camera_side.upper()} CAMERA"
            cv2.putText(frame, camera_label, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            # Update statistics
            if camera_side == "left":
                self.left_camera_stats["faces_detected"] += len(faces)
            else:
                self.right_camera_stats["faces_detected"] += len(faces)
            
            # Process each detected face
            for face_data in faces:
                # Extract face coordinates
                if isinstance(face_data, tuple) and len(face_data) == 6:
                    x, y, w, h, face_crop, landmarks = face_data
                    left, top, right, bottom = x, y, x + w, y + h
                elif hasattr(face_data, 'left'):  # dlib rectangle
                    left = face_data.left()
                    top = face_data.top()
                    right = face_data.right()
                    bottom = face_data.bottom()
                    face_crop = frame[top:bottom, left:right]
                else:
                    continue
                    
                # Default color (unknown)
                color = (0, 0, 255)  # Red
                label = "Unknown"
                
                if self.attendance_mode:
                    # Full processing for attendance mode
                    
                    # Anti-spoofing check
                    is_real = self.anti_spoof_detector.check_if_real(face_crop)
                    
                    if is_real:
                        # Face recognition
                        recognition_result = self.face_recognizer.recognize_face(face_crop)
                        user_id, name, confidence = recognition_result
                        
                        if user_id and confidence > 0.7:
                            # Check cooldown
                            current_time = time.time()
                            cooldown_key = f"{user_id}_{camera_side}"
                            
                            if (cooldown_key not in self.last_recognition_time or 
                                current_time - self.last_recognition_time[cooldown_key] > self.recognition_cooldown):
                                
                                # Mark attendance
                                self.mark_attendance(user_id, name, confidence, camera_side)
                                self.last_recognition_time[cooldown_key] = current_time
                                
                                # Update statistics
                                if camera_side == "left":
                                    self.left_camera_stats["recognitions"] += 1
                                else:
                                    self.right_camera_stats["recognitions"] += 1
                                
                            color = (0, 255, 0)  # Green
                            label = f"{name} ({confidence:.2f})"
                        else:
                            label = "Unknown Person"
                    else:
                        color = (0, 255, 255)  # Yellow
                        label = "Spoof Detected"
                        
                else:
                    # Preview mode - simple face detection
                    color = (255, 0, 0)  # Blue
                    label = "Face Detected"
                
                # Draw rectangle and label
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                           
        except Exception as e:
            self.update_status(f"Frame processing error ({camera_side}): {str(e)}")
            
        return frame
        
    def mark_attendance(self, user_id, name, confidence, camera_side):
        """Mark attendance for recognized user"""
        try:
            # Save attendance record
            attendance_data = {
                'user_id': user_id,
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'camera_side': camera_side,
                'camera_type': self.left_camera_config['type'] if camera_side == "left" else self.right_camera_config['type']
            }
            
            save_attendance(attendance_data)
            
            self.update_status(f"Attendance marked: {name} (Confidence: {confidence:.2f}, Camera: {camera_side})")
            self.update_statistics()
            
        except Exception as e:
            self.update_status(f"Error marking attendance: {str(e)}")
            
    def open_register_window(self):
        """Open user registration window"""
        try:
            from src.gui.add_user_window_enhanced_fixed import AddUserWindowEnhancedFixed
            
            def on_registration_complete():
                self.face_recognizer.reload_user_data()
                self.registered_users = load_registered_users()
                self.update_status("New user registered successfully")
                self.update_statistics()
                
            register_window = tk.Toplevel(self.master)
            AddUserWindowEnhancedFixed(register_window, callback=on_registration_complete)
            
        except ImportError:
            messagebox.showerror("Error", "Registration window not available")
            
    def update_status(self, message):
        """Update status text"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.master.update_idletasks()
        
    def update_statistics(self):
        """Update statistics display"""
        try:
            # Count registered users
            registered_count = len(self.registered_users)
            
            # Count today's attendance
            today = datetime.now().strftime("%Y-%m-%d")
            attendance_file = os.path.join('data', 'attendance', f'attendance_{today}.json')
            
            today_attendance = 0
            if os.path.exists(attendance_file):
                import json
                with open(attendance_file, 'r') as f:
                    records = json.load(f)
                    today_attendance = len(records)
                    
            # Camera statuses
            left_status = "Running" if self.left_camera_running else "Stopped"
            right_status = "Running" if self.right_camera_running else "Stopped"
            
            stats = f"""Registered Users: {registered_count}
Today's Attendance: {today_attendance}

Left Camera: {left_status}
  Faces Detected: {self.left_camera_stats['faces_detected']}
  Recognitions: {self.left_camera_stats['recognitions']}

Right Camera: {right_status}
  Faces Detected: {self.right_camera_stats['faces_detected']}
  Recognitions: {self.right_camera_stats['recognitions']}

Mode: {'Attendance' if self.attendance_mode else 'Preview'}"""

            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats)
            
        except Exception as e:
            self.update_status(f"Error updating statistics: {str(e)}")
            
    def close_application(self):
        """Clean up and close application"""
        self.stop_both_cameras()
        self.master.quit()
        self.master.destroy()


def main():
    """Main function to run the dual camera attendance system"""
    root = tk.Tk()
    app = DualCameraWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.close_application)
    root.mainloop()


if __name__ == "__main__":
    main()
