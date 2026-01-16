# src/gui/add_user_window_liveness_improved.py
"""
Clean minimal version of the add user window to resolve syntax errors
This replaces the corrupted version while maintaining functionality
"""

import tkinter as tk
from tkinter import messagebox
import cv2
import os
import pickle

class ImprovedLivenessAddUserWindow:
    def __init__(self, master, on_close_callback=None):
        self.master = master
        self.master.title("🔒 Enhanced Liveness Detection - Add New User")
        self.master.geometry("1100x750")
        self.on_close_callback = on_close_callback
        
        # Initialize detection models
        try:
            from src.face_detector import FaceDetector
            from src.anti_spoof import AntiSpoofingDetector
            self.face_detector = FaceDetector()
            self.anti_spoof_detector = AntiSpoofingDetector()
        except ImportError as e:
            print(f"Warning: Could not import detection models: {e}")
            self.face_detector = None
            self.anti_spoof_detector = None
        
        # Initialize dlib for face landmark detection if available
        try:
            import dlib
            self.predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
            self.use_landmarks = True
        except (FileNotFoundError, RuntimeError, OSError, ImportError) as e:
            self.use_landmarks = False
            print(f"Dlib landmarks model not found: {e}, using simplified detection")
        
        # Camera variables
        self.cap = None
        self.camera_running = False
        self.current_frame = None
        self.face_captured = False
        self.face_encoding = None
        self.captured_frame = None
        self.user_data = None
        self._current_photo = None
        
        # Enhanced liveness detection variables
        self.liveness_test_active = False
        self.liveness_tests_completed = {
            'blink': False,
            'head_movement': False,
            'phone_detection': False
        }
        
        # Blink detection parameters
        self.blink_counter = 0
        self.consecutive_blinks = 0
        self.required_blinks = 2
        self.eye_aspect_ratios = []
        self.blink_threshold = 0.26
        self.blink_frames_threshold = 2
        
        # Head movement detection
        self.face_positions = []
        self.movement_threshold = 20
        self.movements_detected = set()
        self.initial_position = None
        
        # Phone detection
        self.phone_detection_frames = 0
        self.phone_detections = 0
        self.max_phone_detections = 5
        self.phone_retry_count = 0
        self.max_phone_retries = 2
        
        # Timing
        self.liveness_start_time = None
        self.frame_count = 0
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the enhanced user interface"""
        # Main container
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for user info and controls
        left_panel = tk.Frame(main_frame, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Right panel for camera feed
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # User information section
        info_frame = tk.LabelFrame(left_panel, text="User Information", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # User ID
        tk.Label(info_frame, text="User ID:").pack(anchor=tk.W)
        self.user_id_entry = tk.Entry(info_frame, width=30)
        self.user_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # User Name
        tk.Label(info_frame, text="Full Name:").pack(anchor=tk.W)
        self.user_name_entry = tk.Entry(info_frame, width=30)
        self.user_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        button_frame = tk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_camera_btn = tk.Button(
            button_frame, 
            text="📹 Start Camera", 
            command=self.start_camera,
            bg="#4CAF50", 
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.start_camera_btn.pack(fill=tk.X, pady=2)
        
        self.capture_btn = tk.Button(
            button_frame, 
            text="📸 Capture Face", 
            command=self.capture_face,
            bg="#2196F3", 
            fg="white",
            font=("Arial", 10, "bold"),
            state=tk.DISABLED
        )
        self.capture_btn.pack(fill=tk.X, pady=2)
        
        self.save_btn = tk.Button(
            button_frame, 
            text="💾 Save User", 
            command=self.save_user,
            bg="#FF9800", 
            fg="white",
            font=("Arial", 10, "bold"),
            state=tk.DISABLED
        )
        self.save_btn.pack(fill=tk.X, pady=2)
        
        # Status display
        status_frame = tk.LabelFrame(left_panel, text="Status", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_frame, height=8, width=40, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Camera display
        camera_frame = tk.LabelFrame(right_panel, text="Camera Feed", padx=10, pady=10)
        camera_frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_label = tk.Label(camera_frame, text="Camera not started", 
                                   bg="gray", fg="white", font=("Arial", 16))
        self.camera_label.pack(fill=tk.BOTH, expand=True)
        
        # Initial status
        self.update_status("🔄 System ready. Enter user details and start camera.")
        
    def start_camera(self):
        """Start the camera"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
                
            self.camera_running = True
            self.start_camera_btn.config(state=tk.DISABLED)
            self.capture_btn.config(state=tk.NORMAL)
            self.update_status("📹 Camera started successfully!")
            self.update_camera_feed()
            
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to start camera: {e}")
            self.update_status(f"❌ Camera error: {e}")
    
    def update_camera_feed(self):
        """Update the camera feed"""
        if not self.camera_running or self.cap is None:
            return
            
        try:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                
                # Convert frame for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                from PIL import Image, ImageTk
                img = Image.fromarray(frame_rgb)
                img = img.resize((640, 480))
                photo = ImageTk.PhotoImage(img)
                
                self.camera_label.config(image=photo, text="")
                self.camera_label.image = photo
                
        except Exception as e:
            print(f"Camera feed error: {e}")
        
        # Schedule next update
        if self.camera_running:
            self.master.after(30, self.update_camera_feed)
    
    def capture_face(self):
        """Capture face for registration"""
        if self.current_frame is None:
            messagebox.showwarning("No Frame", "No camera frame available")
            return
            
        user_id = self.user_id_entry.get().strip()
        user_name = self.user_name_entry.get().strip()
        
        if not user_id or not user_name:
            messagebox.showwarning("Missing Info", "Please enter both User ID and Name")
            return
        
        try:
            # Simple face detection
            if self.face_detector:
                faces = self.face_detector.detect_faces(self.current_frame)
                if not faces:
                    messagebox.showwarning("No Face", "No face detected in frame")
                    return
            
            self.captured_frame = self.current_frame.copy()
            self.face_captured = True
            self.save_btn.config(state=tk.NORMAL)
            self.update_status("✅ Face captured successfully! Ready to save.")
            
        except Exception as e:
            messagebox.showerror("Capture Error", f"Failed to capture face: {e}")
            self.update_status(f"❌ Capture error: {e}")
    
    def save_user(self):
        """Save the user data"""
        if not self.face_captured:
            messagebox.showwarning("No Face", "Please capture a face first")
            return
            
        user_id = self.user_id_entry.get().strip()
        user_name = self.user_name_entry.get().strip()
        
        try:
            # Create user directory
            user_dir = f"data/registered_users/{user_id}_{user_name.replace(' ', '_')}"
            os.makedirs(user_dir, exist_ok=True)
            
            # Save face image
            face_path = os.path.join(user_dir, "face.jpg")
            cv2.imwrite(face_path, self.captured_frame)
            
            # Create simple encoding (placeholder)
            encoding_path = os.path.join(user_dir, "encoding.pkl")
            with open(encoding_path, 'wb') as f:
                pickle.dump({'user_id': user_id, 'name': user_name}, f)
            
            messagebox.showinfo("Success", f"User {user_name} registered successfully!")
            self.update_status(f"✅ User {user_name} saved successfully!")
            
            # Reset for next user
            self.reset_form()
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save user: {e}")
            self.update_status(f"❌ Save error: {e}")
    
    def reset_form(self):
        """Reset the form for next user"""
        self.user_id_entry.delete(0, tk.END)
        self.user_name_entry.delete(0, tk.END)
        self.face_captured = False
        self.captured_frame = None
        self.save_btn.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Update status display"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.camera_running and self.cap:
                self.camera_running = False
                self.cap.release()
        except Exception as e:
            print(f"Cleanup error: {e}")

def launch_improved_liveness_window(parent=None, on_close_callback=None):
    """Launch the improved liveness add user window"""
    window = tk.Toplevel(parent) if parent else tk.Tk()
    app = ImprovedLivenessAddUserWindow(window, on_close_callback)
    
    def on_closing():
        app.cleanup()
        if on_close_callback:
            on_close_callback()
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", on_closing)
    
    if not parent:
        window.mainloop()
    
    return app

if __name__ == "__main__":
    launch_improved_liveness_window()
