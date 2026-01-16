# src/gui/main_window_enhanced_camera.py

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


class EnhancedCameraMainWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Face Attendance System - Enhanced Camera Support")
        self.master.geometry("1400x900")
        
        # Initialize models
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.anti_spoof_detector = AntiSpoofingDetector()
        self.camera_manager = CameraManager()
        
        # Load registered users
        self.registered_users = load_registered_users()
        self.face_recognizer.reload_user_data()
        
        # Camera variables
        self.current_camera = None
        self.camera_config = None
        self.camera_running = False
        self.attendance_mode = False
        self.video_thread = None
        
        # Recognition variables
        self.last_recognition_time = {}
        self.recognition_cooldown = 5  # seconds
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the enhanced user interface"""
        # Main container
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top panel
        top_panel = tk.Frame(main_frame, height=120)
        top_panel.pack(fill=tk.X, pady=(0, 10))
        top_panel.pack_propagate(False)
        
        # Title
        title_label = tk.Label(top_panel, text="Face Attendance System", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=5)
        
        # Camera info
        self.camera_info_label = tk.Label(top_panel, text="No camera selected", 
                                         font=("Arial", 10), fg="gray")
        self.camera_info_label.pack()
        
        # Control buttons frame
        control_frame = tk.Frame(top_panel)
        control_frame.pack(pady=10)
        
        # Camera selection button
        self.select_camera_btn = tk.Button(control_frame, text="📹 Select Camera", 
                                          command=self.open_camera_selection, 
                                          bg="lightblue", font=("Arial", 11, "bold"))
        self.select_camera_btn.pack(side=tk.LEFT, padx=5)
        
        # Start/Stop camera buttons
        self.start_camera_btn = tk.Button(control_frame, text="▶️ Start Camera", 
                                         command=self.start_camera, state=tk.DISABLED,
                                         bg="lightgreen", font=("Arial", 11))
        self.start_camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_camera_btn = tk.Button(control_frame, text="⏹️ Stop Camera", 
                                        command=self.stop_camera, state=tk.DISABLED,
                                        bg="lightcoral", font=("Arial", 11))
        self.stop_camera_btn.pack(side=tk.LEFT, padx=5)
        
        # Mode toggle
        self.mode_var = tk.StringVar(value="preview")
        mode_frame = tk.Frame(control_frame)
        mode_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(mode_frame, text="Mode:", font=("Arial", 10)).pack(side=tk.LEFT)
        
        preview_radio = tk.Radiobutton(mode_frame, text="Preview", variable=self.mode_var, 
                                      value="preview", command=self.on_mode_change)
        preview_radio.pack(side=tk.LEFT, padx=5)
        
        attendance_radio = tk.Radiobutton(mode_frame, text="Attendance", variable=self.mode_var, 
                                         value="attendance", command=self.on_mode_change)
        attendance_radio.pack(side=tk.LEFT, padx=5)
        
        # Register user button
        self.register_btn = tk.Button(control_frame, text="➕ Register New User", 
                                     command=self.open_register_window, 
                                     bg="lightyellow", font=("Arial", 11))
        self.register_btn.pack(side=tk.RIGHT, padx=5)
        
        # Main content area
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Camera display
        camera_panel = tk.LabelFrame(content_frame, text="Camera Feed", padx=10, pady=10)
        camera_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.camera_label = tk.Label(camera_panel, text="No camera feed", 
                                    width=80, height=30, bg="black", fg="white")
        self.camera_label.pack(expand=True)
        
        # Right panel - Information and controls
        info_panel = tk.LabelFrame(content_frame, text="Information", padx=10, pady=10)
        info_panel.pack(side=tk.RIGHT, fill=tk.Y, ipadx=10)
        
        # System status
        status_frame = tk.LabelFrame(info_panel, text="System Status", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_text = tk.Text(status_frame, height=8, width=40, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar to status text
        status_scrollbar = tk.Scrollbar(status_frame)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=status_scrollbar.set)
        status_scrollbar.config(command=self.status_text.yview)
        
        # Recognition results
        recognition_frame = tk.LabelFrame(info_panel, text="Last Recognition", padx=10, pady=10)
        recognition_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.recognition_label = tk.Label(recognition_frame, text="No recognition yet", 
                                         font=("Arial", 12), wraplength=300)
        self.recognition_label.pack()
        
        # Statistics
        stats_frame = tk.LabelFrame(info_panel, text="Statistics", padx=10, pady=10)
        stats_frame.pack(fill=tk.X)
        
        self.stats_text = tk.Text(stats_frame, height=6, width=40)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Initialize status
        self.update_status("System initialized. Please select a camera to begin.")
        self.update_statistics()
        
    def open_camera_selection(self):
        """Open camera selection window"""
        def on_camera_selected(camera_info):
            self.camera_config = camera_info
            self.camera_info_label.config(text=f"Selected: {camera_info['description']}")
            self.start_camera_btn.config(state=tk.NORMAL)
            self.update_status(f"Camera selected: {camera_info['description']}")
            
        selection_window = tk.Toplevel(self.master)
        CameraSelectionWindow(selection_window, callback=on_camera_selected)
        
    def start_camera(self):
        """Start the selected camera"""
        if not self.camera_config:
            messagebox.showerror("Error", "Please select a camera first")
            return
            
        try:
            # Initialize camera using camera manager
            self.current_camera = self.camera_manager.initialize_camera_from_config(self.camera_config)
            
            if not self.current_camera or not self.current_camera.isOpened():
                messagebox.showerror("Error", "Failed to start camera")
                return
                
            self.camera_running = True
            self.start_camera_btn.config(state=tk.DISABLED)
            self.stop_camera_btn.config(state=tk.NORMAL)
            self.select_camera_btn.config(state=tk.DISABLED)
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
            self.video_thread.start()
            
            self.update_status(f"Camera started: {self.camera_config['description']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
            self.update_status(f"Error starting camera: {str(e)}")
            
    def stop_camera(self):
        """Stop the camera"""
        self.camera_running = False
        
        if self.current_camera:
            self.current_camera.release()
            self.current_camera = None
            
        self.camera_label.config(image="", text="Camera stopped")
        self.camera_label.image = None
        
        self.start_camera_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.select_camera_btn.config(state=tk.NORMAL)
        
        self.update_status("Camera stopped")
        
    def on_mode_change(self):
        """Handle mode change between preview and attendance"""
        self.attendance_mode = (self.mode_var.get() == "attendance")
        mode = "Attendance Tracking" if self.attendance_mode else "Preview"
        self.update_status(f"Mode changed to: {mode}")
        
    def video_loop(self):
        """Main video processing loop"""
        while self.camera_running and self.current_camera:
            try:
                ret, frame = self.current_camera.read()
                if not ret:
                    self.update_status("Error: Failed to read from camera")
                    break
                    
                # Process frame
                processed_frame = self.process_frame(frame.copy())
                
                # Convert to display format
                display_frame = cv2.resize(processed_frame, (800, 600))
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                # Update camera display
                self.camera_label.config(image=photo, text="")
                self.camera_label.image = photo
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.update_status(f"Video processing error: {str(e)}")
                break
                
        self.stop_camera()
        
    def process_frame(self, frame):
        """Process frame for face detection and recognition"""
        try:
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
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
                            if (user_id not in self.last_recognition_time or 
                                current_time - self.last_recognition_time[user_id] > self.recognition_cooldown):
                                
                                # Mark attendance
                                self.mark_attendance(user_id, name, confidence)
                                self.last_recognition_time[user_id] = current_time
                                
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
            self.update_status(f"Frame processing error: {str(e)}")
            
        return frame
        
    def mark_attendance(self, user_id, name, confidence):
        """Mark attendance for recognized user"""
        try:
            # Save attendance record
            attendance_data = {
                'user_id': user_id,
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'camera_type': self.camera_config['type'] if self.camera_config else 'unknown'
            }
            
            save_attendance(attendance_data)
            
            # Update UI
            self.recognition_label.config(
                text=f"✅ {name}\nConfidence: {confidence:.2f}\nTime: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            self.update_status(f"Attendance marked: {name} (Confidence: {confidence:.2f})")
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
                    
            # Camera info
            camera_info = "Not selected"
            if self.camera_config:
                camera_info = f"{self.camera_config['type'].title()} Camera"
                
            stats = f"""Registered Users: {registered_count}
Today's Attendance: {today_attendance}
Camera Type: {camera_info}
Mode: {'Attendance' if self.attendance_mode else 'Preview'}
Status: {'Running' if self.camera_running else 'Stopped'}"""

            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats)
            
        except Exception as e:
            self.update_status(f"Error updating statistics: {str(e)}")
            
    def close_application(self):
        """Clean up and close application"""
        self.stop_camera()
        self.master.quit()
        self.master.destroy()


def main():
    """Main function to run the enhanced camera attendance system"""
    root = tk.Tk()
    app = EnhancedCameraMainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.close_application)
    root.mainloop()


if __name__ == "__main__":
    main()
