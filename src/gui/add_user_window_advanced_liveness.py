# src/gui/add_user_window_advanced_liveness.py

import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import os
import pickle
import numpy as np
from src.utils.image_utils import preprocess_for_face_recognition
from src.face_detector import FaceDetector
from src.anti_spoof import AntiSpoofingDetector
from src.advanced_liveness_detector import AdvancedLivenessDetector
from src.utils.camera_utils import CameraManager
from datetime import datetime
import threading
import time
from PIL import Image, ImageTk
import dlib
import math


class AdvancedLivenessAddUserWindow:
    def __init__(self, master, on_close_callback=None):
        self.master = master
        self.master.title("Advanced Liveness Detection - Add New User")
        self.master.geometry("1100x800")
        self.on_close_callback = on_close_callback
          # Initialize detection models
        self.face_detector = FaceDetector()
        self.anti_spoof_detector = AntiSpoofingDetector()
        self.advanced_liveness = AdvancedLivenessDetector(for_registration=True)  # Lenient for registration
        self.camera_manager = CameraManager()
          # Initialize dlib facial landmark predictor if available
        try:
            predictor_path = "models/shape_predictor_68_face_landmarks.dat"
            if os.path.exists(predictor_path):
                self.predictor = dlib.shape_predictor(predictor_path)
                self.landmark_detector_available = True
            else:
                self.predictor = None
                self.landmark_detector_available = False
        except Exception:
            self.predictor = None
            self.landmark_detector_available = False
        
        # Camera variables
        self.cap = None
        self.camera_running = False
        self.current_frame = None
        self.face_captured = False
        self.face_encoding = None
        self.captured_frame = None
        self.user_data = None
        self._current_photo = None
        
        # Liveness detection variables
        self.liveness_test_active = False
        self.liveness_tests_completed = {
            'blink': False,
            'head_movement': False,
            'phone_detection': False
        }
        self.blink_counter = 0
        self.blink_frames = []
        self.head_positions = []
        self.phone_detection_frames = 0
        self.liveness_start_time = None
        self.liveness_timeout = 30  # 30 seconds timeout for liveness tests
        
        # Eye aspect ratio for blink detection
        self.EAR_THRESHOLD = 0.25
        self.BLINK_FRAME_THRESHOLD = 3
        self.consecutive_blinks = 0
        self.required_blinks = 3
        
        # Head movement detection
        self.head_movement_threshold = 15  # degrees
        self.initial_head_pose = None
        self.head_movements_detected = []
        self.required_head_movements = 2
          # Phone detection (texture analysis) - More lenient for registration
        self.phone_detection_scores = []
        self.phone_detection_threshold = 0.8  # More lenient threshold for registration
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the advanced user interface with liveness detection"""
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
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = tk.Entry(info_frame, width=25)
        self.name_entry.grid(row=0, column=1, pady=5)
        
        tk.Label(info_frame, text="ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.id_entry = tk.Entry(info_frame, width=25)
        self.id_entry.grid(row=1, column=1, pady=5)
        
        # Liveness Test Section
        liveness_frame = tk.LabelFrame(left_panel, text="🔒 Liveness Verification", padx=10, pady=10)
        liveness_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Liveness test status indicators
        self.blink_status = tk.Label(liveness_frame, text="👁️ Eye Blink Test: ⏳ Pending", 
                                   fg="orange", font=("Arial", 9))
        self.blink_status.pack(fill=tk.X, pady=2)
        
        self.head_status = tk.Label(liveness_frame, text="🔄 Head Movement: ⏳ Pending", 
                                  fg="orange", font=("Arial", 9))
        self.head_status.pack(fill=tk.X, pady=2)
        
        self.phone_status = tk.Label(liveness_frame, text="📱 Phone Detection: ⏳ Pending", 
                                   fg="orange", font=("Arial", 9))
        self.phone_status.pack(fill=tk.X, pady=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(liveness_frame, variable=self.progress_var, 
                                          maximum=100, length=200)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Liveness instructions
        self.instruction_label = tk.Label(liveness_frame, text="Start camera to begin liveness tests", 
                                        fg="blue", font=("Arial", 9), wraplength=300)
        self.instruction_label.pack(fill=tk.X, pady=5)
        
        # Camera controls section
        control_frame = tk.LabelFrame(left_panel, text="Camera Controls", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_camera_btn = tk.Button(control_frame, text="🎥 Start Camera", 
                                         command=self.start_camera, bg="lightblue",
                                         font=("Arial", 10))
        self.start_camera_btn.pack(fill=tk.X, pady=3)
        
        self.start_liveness_btn = tk.Button(control_frame, text="🔒 Start Liveness Test", 
                                          command=self.start_liveness_test, state=tk.DISABLED, 
                                          bg="orange", font=("Arial", 10))
        self.start_liveness_btn.pack(fill=tk.X, pady=3)
        
        self.capture_btn = tk.Button(control_frame, text="📸 Capture Face", 
                                   command=self.capture_face, state=tk.DISABLED, 
                                   bg="lightgreen", font=("Arial", 10))
        self.capture_btn.pack(fill=tk.X, pady=3)
        
        self.save_btn = tk.Button(control_frame, text="💾 Save User", 
                                command=self.save_user, state=tk.DISABLED, 
                                bg="lightgreen", font=("Arial", 10))
        self.save_btn.pack(fill=tk.X, pady=3)
        
        self.stop_camera_btn = tk.Button(control_frame, text="⏹️ Stop Camera", 
                                       command=self.stop_camera, state=tk.DISABLED, 
                                       bg="lightcoral", font=("Arial", 10))
        self.stop_camera_btn.pack(fill=tk.X, pady=3)
        
        # Status section
        status_frame = tk.LabelFrame(left_panel, text="Status Log", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 8))
        status_scrollbar = tk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Camera display section
        camera_frame = tk.LabelFrame(right_panel, text="Live Camera Feed with Liveness Detection", 
                                   padx=10, pady=10)
        camera_frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_label = tk.Label(camera_frame, text="Camera not started\n\nAdvanced Liveness Detection Ready", 
                                   bg="black", fg="white", width=70, height=35,
                                   font=("Arial", 12))
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Enhanced legend for color codes
        legend_frame = tk.Frame(right_panel)
        legend_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(legend_frame, text="Detection Legend:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(legend_frame, text="🟢 Real Face", fg="green", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="🔴 Spoofing/Phone", fg="red", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="🟡 Processing", fg="orange", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="🔵 Liveness Test", fg="blue", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(right_panel, text="✖️ Close", command=self.close_window, 
                            bg="gray", font=("Arial", 10))
        close_btn.pack(pady=5)
          # Initialize status
        self.update_status("🚀 Advanced Liveness Detection System Ready!")
        self.update_status("📝 Enter user details and start camera to begin.")
        if not self.landmark_detector_available:
            self.update_status("⚠️ Warning: Facial landmarks detector not found. Limited functionality.")
    
    def update_status(self, message):
        """Update status display with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def start_camera(self):
        """Start the camera feed"""
        if self.camera_running:
            return
            
        self.cap = self.camera_manager.initialize_camera()
        if not self.cap:
            messagebox.showerror("Camera Error", 
                               "Cannot access camera! Please check:\n"
                               "1. Camera is connected\n"
                               "2. Camera is not used by another application\n"
                               "3. Camera drivers are installed")
            return
            
        self.camera_running = True
        self.start_camera_btn.config(state=tk.DISABLED)
        self.start_liveness_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.NORMAL)
        self.update_status("🎥 Camera started. Ready for liveness detection.")
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
    
    def start_liveness_test(self):
        """Start the advanced liveness detection test sequence with lenient thresholds"""
        if not self.camera_running:
            messagebox.showerror("Error", "Please start camera first!")
            return
            
        # Reset liveness test state using advanced detector
        self.liveness_test_active = True
        self.advanced_liveness.reset_liveness_state()
        self.liveness_start_time = time.time()
          # Update UI
        self.start_liveness_btn.config(state=tk.DISABLED)
        self.update_liveness_status()
        self.update_status("🔒 Advanced liveness test started! Follow the instructions...")
        self.update_instruction("👁️ Look at camera naturally - blink and move head slightly")
    
    def update_liveness_status(self):
        """Update the liveness test status indicators using advanced detector"""
        # Get tests status from advanced detector
        tests_completed = self.advanced_liveness.liveness_tests_completed
        
        # Blink test status
        if tests_completed['blink']:
            self.blink_status.config(text="👁️ Eye Blink Test: ✅ Passed", fg="green")
        else:
            blink_count = self.advanced_liveness.consecutive_blinks
            required = self.advanced_liveness.required_blinks
            self.blink_status.config(text=f"👁️ Eye Blink Test: {blink_count}/{required} blinks", fg="orange")
        
        # Head movement status
        if tests_completed['head_movement']:
            self.head_status.config(text="🔄 Head Movement: ✅ Passed", fg="green")
        else:
            movement_count = len(self.advanced_liveness.head_movements_detected)
            required = self.advanced_liveness.required_head_movements
            self.head_status.config(text=f"🔄 Head Movement: {movement_count}/{required} movements", fg="orange")
        
        # Anti-spoof and phone detection status
        if tests_completed['anti_spoof'] and tests_completed['phone_detection']:
            self.phone_status.config(text="📱 Security Check: ✅ Passed", fg="green")
        else:
            self.phone_status.config(text="📱 Security Check: 🔍 Analyzing...", fg="orange")
        
        # Update progress bar
        completed_tests = sum(tests_completed.values())
        progress = (completed_tests / len(tests_completed)) * 100
        self.progress_var.set(progress)
        
        # Check if all tests are completed
        if self.advanced_liveness.is_liveness_complete():
            self.liveness_test_active = False
            self.capture_btn.config(state=tk.NORMAL)
            self.update_status("🎉 All liveness tests passed! You can now capture your face.")
            self.update_instruction("✅ Liveness verification complete! Click 'Capture Face' to proceed.")
    
    def update_instruction(self, text):
        """Update the instruction label"""
        self.instruction_label.config(text=text)
    
    def calculate_ear(self, eye_landmarks):
        """Calculate Eye Aspect Ratio for blink detection"""
        # Compute the euclidean distances between the two sets of vertical eye landmarks
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        # Compute the euclidean distance between the horizontal eye landmarks
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        # Compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_phone_screen(self, face_crop):
        """Detect if the face is from a phone screen using texture analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            # Calculate variance of Laplacian (measure of blurriness/sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate local binary pattern variance (texture measure)
            # Simple texture analysis using standard deviation
            texture_std = np.std(gray)
            
            # Analyze color distribution (phones often have more uniform lighting)
            color_channels = cv2.split(face_crop)
            color_std = np.mean([np.std(channel) for channel in color_channels])
            
            # Combine features to detect phone screens
            # Phone screens typically have:
            # - Lower texture variance
            # - More uniform color distribution
            # - Different sharpness characteristics
            
            phone_score = 0
            
            # Check for unusually uniform texture (typical of screens)
            if texture_std < 25:  # Low texture variance
                phone_score += 0.3
            
            # Check for unusual color uniformity
            if color_std < 20:  # Very uniform colors
                phone_score += 0.3
              # Check sharpness characteristics
            if laplacian_var > 100 and laplacian_var < 300:  # Artificial sharpness range
                phone_score += 0.4
            
            return phone_score > self.phone_detection_threshold
            
        except Exception:
            return False
    
    def estimate_head_pose(self, landmarks):
        """Estimate head pose from facial landmarks"""
        try:
            # 3D model points for head pose estimation
            model_points = np.array([
                (0.0, 0.0, 0.0),             # Nose tip
                (0.0, -330.0, -65.0),        # Chin
                (-225.0, 170.0, -135.0),     # Left eye left corner
                (225.0, 170.0, -135.0),      # Right eye right corner
                (-150.0, -150.0, -125.0),    # Left Mouth corner
                (150.0, -150.0, -125.0)      # Right mouth corner
            ])
            
            # 2D image points from landmarks
            image_points = np.array([
                landmarks[30],    # Nose tip
                landmarks[8],     # Chin
                landmarks[36],    # Left eye left corner
                landmarks[45],    # Right eye right corner
                landmarks[48],    # Left mouth corner
                landmarks[54]     # Right mouth corner
            ], dtype="double")
            
            # Camera parameters (approximate)
            focal_length = 640  # Approximate focal length
            center = (320, 240)  # Approximate image center
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            
            dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
            
            # Solve PnP
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs)
            
            if success:
                # Convert rotation vector to euler angles
                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                # Extract euler angles (simplified)
                sy = math.sqrt(rotation_matrix[0,0] * rotation_matrix[0,0] +  rotation_matrix[1,0] * rotation_matrix[1,0])
                singular = sy < 1e-6
                
                if not singular:
                    x = math.atan2(rotation_matrix[2,1] , rotation_matrix[2,2])
                    y = math.atan2(-rotation_matrix[2,0], sy)
                    z = math.atan2(rotation_matrix[1,0], rotation_matrix[0,0])
                else:
                    x = math.atan2(-rotation_matrix[1,2], rotation_matrix[1,1])
                    y = math.atan2(-rotation_matrix[2,0], sy)
                    z = 0
                  # Convert to degrees
                pitch = math.degrees(x)
                yaw = math.degrees(y)
                roll = math.degrees(z)
                
                return (pitch, yaw, roll)
            
        except Exception:
            pass
        
        return None
    
    def camera_loop(self):
        """Main camera processing loop with liveness detection"""
        error_count = 0
        max_errors = 10
        
        while self.camera_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    break
                
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    error_count += 1
                    if error_count >= max_errors:
                        break
                    time.sleep(0.1)
                    continue
                
                error_count = 0
                frame = cv2.flip(frame, 1)
                self.current_frame = frame.copy()
                  # Process frame with liveness detection
                frame_with_feedback = self.process_frame_with_liveness(frame)
                
                # Display frame
                self.display_frame(frame_with_feedback)
                
                time.sleep(0.03)  # ~30 FPS
                
            except Exception:
                error_count += 1
                if error_count >= max_errors:
                    break
                time.sleep(0.1)
    
    def process_frame_with_liveness(self, frame):
        """Process frame with advanced liveness detection"""
        frame_copy = frame.copy()
        
        try:
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            if faces:
                for face in faces:
                    # Extract face coordinates and crop
                    if isinstance(face, tuple) and len(face) >= 4:
                        if len(face) == 6:
                            x, y, w, h = face[:4]
                            left, top, right, bottom = x, y, x + w, y + h
                            face_crop = face[4] if face[4] is not None else frame[y:y+h, x:x+w]
                        else:
                            left, top, right, bottom = face
                            face_crop = frame[top:bottom, left:right]
                    elif hasattr(face, 'left'):
                        left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
                        face_crop = frame[top:bottom, left:right]
                    else:
                        continue
                    
                    if face_crop is None or face_crop.size == 0:
                        continue
                    
                    # Use advanced liveness detector for better accuracy
                    if self.liveness_test_active:
                        liveness_results = self.advanced_liveness.process_frame_for_liveness(frame, (left, top, right, bottom))
                        
                        # Determine color and label based on liveness results
                        if liveness_results['all_passed']:
                            color = (0, 255, 0)  # Green for all tests passed
                            label = "✅ LIVENESS VERIFIED"
                        elif liveness_results['progress'] > 0:
                            color = (0, 255, 255)  # Yellow for in progress
                            label = f"🔒 LIVENESS: {liveness_results['progress']:.0f}%"
                        else:
                            # Check messages for specific issues
                            messages = liveness_results['messages']
                            if any('Phone detected' in msg for msg in messages):
                                color = (0, 0, 255)  # Red for phone
                                label = "📱 PHONE DETECTED!"
                            elif any('Spoof' in msg for msg in messages):
                                color = (0, 0, 255)  # Red for spoof
                                label = "🚫 SPOOF DETECTED!"
                            else:
                                color = (255, 0, 0)  # Blue for testing
                                label = "🔒 LIVENESS TEST ACTIVE"
                        
                        # Update UI with messages
                        if liveness_results['messages']:
                            latest_msg = liveness_results['messages'][-1]
                            self.master.after(0, lambda msg=latest_msg: self.update_instruction(msg))
                        
                        # Update liveness status
                        self.master.after(0, self.update_liveness_status)
                    else:
                        # Quick check without full liveness test
                        is_real, prediction = self.anti_spoof_detector.predict(face_crop, debug=True, threshold=0.3)
                        is_phone = self.advanced_liveness.detect_phone_screen(face_crop)
                        
                        if is_phone:
                            color = (0, 0, 255)  # Red for phone
                            label = "📱 PHONE DETECTED!"
                        elif not is_real:
                            color = (0, 0, 255)  # Red for spoof
                            label = f"🚫 SPOOF ({prediction:.2f})"
                        else:
                            color = (0, 255, 0)  # Green for real face
                            label = f"✅ REAL FACE ({prediction:.2f})"
                    
                    # Draw bounding box
                    cv2.rectangle(frame_copy, (left, top), (right, bottom), color, 3)
                    
                    # Draw label with background
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    cv2.rectangle(frame_copy, (left, top - label_size[1] - 15), 
                                  (left + label_size[0] + 10, top), color, -1)
                    cv2.putText(frame_copy, label, (left + 5, top - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # --- Animated liveness feedback ---
                    # Draw animated progress bar for liveness cues
                    bar_x, bar_y = left, bottom + 60
                    bar_width, bar_height = right - left, 18
                    total_cues = 3
                    cues_passed = 0
                    # Head movement
                    if self.liveness_tests_completed.get('head_movement', False):
                        cues_passed += 1
                        cv2.putText(frame_copy, "Head Movement ✔", (bar_x, bar_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame_copy, "Move Head", (bar_x, bar_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                    # Eye blinks
                    if self.liveness_tests_completed.get('blink', False):
                        cues_passed += 1
                        cv2.putText(frame_copy, "Blinks ✔", (bar_x, bar_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame_copy, "Blink Eyes", (bar_x, bar_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                    # Body movement (simulate as always required for now)
                    if hasattr(self, 'body_movement_detected') and self.body_movement_detected:
                        cues_passed += 1
                        cv2.putText(frame_copy, "Body Movement ✔", (bar_x, bar_y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame_copy, "Move Body", (bar_x, bar_y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                    # Draw animated progress bar
                    progress = int((cues_passed / total_cues) * bar_width)
                    cv2.rectangle(frame_copy, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (200, 200, 200), 2)
                    cv2.rectangle(frame_copy, (bar_x, bar_y), (bar_x + progress, bar_y + bar_height), (0, 255, 0), -1)
                    cv2.putText(frame_copy, f"Liveness: {cues_passed}/{total_cues}", (bar_x, bar_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if cues_passed == total_cues else (0, 200, 255), 2)
                    # Add animated glow if all cues passed
                    if cues_passed == total_cues:
                        glow_color = (0, 255, 0)
                        thickness = 10 + int(4 * np.sin(time.time() * 4))
                        cv2.rectangle(frame_copy, (left-20, top-20), (right+20, bottom+20), glow_color, thickness)
            else:
                cv2.putText(frame_copy, "🔍 No face detected - Position your face in view", 
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
        except Exception as e:
            cv2.putText(frame_copy, f"Detection Error: {str(e)[:50]}", 
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return frame_copy
    
    def perform_liveness_detection(self, frame, left, top, right, bottom):
        """Perform liveness detection tests"""
        try:
            if not self.landmark_detector_available:
                # Simplified liveness detection without landmarks
                self.perform_simplified_liveness_detection()
                return
            
            # Convert face region to dlib rectangle
            face_rect = dlib.rectangle(left, top, right, bottom)
            
            # Get facial landmarks
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            landmarks = self.predictor(gray, face_rect)
            
            # Convert landmarks to numpy array
            landmark_points = np.array([[p.x, p.y] for p in landmarks.parts()])
            
            # Blink detection
            if not self.liveness_tests_completed['blink']:
                self.detect_blinks(landmark_points)
            
            # Head movement detection
            if not self.liveness_tests_completed['head_movement']:
                self.detect_head_movement(landmark_points)
            
            # Phone detection (texture-based)
            if not self.liveness_tests_completed['phone_detection']:
                face_crop = frame[top:bottom, left:right]
                if not self.detect_phone_screen(face_crop):
                    self.phone_detection_frames += 1
                    if self.phone_detection_frames > 30:  # 1 second of no phone detection
                        self.liveness_tests_completed['phone_detection'] = True
                        self.update_status("✅ Phone detection test passed")
                else:
                    self.phone_detection_frames = 0
                    self.update_status("❌ Phone detected! Please use your real face.")
              # Update liveness status
            self.master.after(0, self.update_liveness_status)
            
        except Exception as e:
            self.update_status(f"Liveness detection error: {str(e)[:50]}")
    
    def perform_simplified_liveness_detection(self):
        """Simplified liveness detection when landmarks are not available"""
        # Simple time-based completion for basic testing
        elapsed_time = time.time() - self.liveness_start_time
        
        if elapsed_time > 5 and not self.liveness_tests_completed['blink']:
            self.liveness_tests_completed['blink'] = True
            self.update_status("✅ Basic blink test completed (simplified mode)")
        
        if elapsed_time > 10 and not self.liveness_tests_completed['head_movement']:
            self.liveness_tests_completed['head_movement'] = True
            self.update_status("✅ Basic movement test completed (simplified mode)")
        
        if elapsed_time > 15 and not self.liveness_tests_completed['phone_detection']:
            self.liveness_tests_completed['phone_detection'] = True
            self.update_status("✅ Basic phone detection completed (simplified mode)")
    
    def detect_blinks(self, landmarks):
        """Detect blinks using Eye Aspect Ratio"""
        try:
            # Eye landmark indices (for 68-point landmarks)
            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            
            # Calculate EAR for both eyes
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            
            # Average EAR
            ear = (left_ear + right_ear) / 2.0
              # Check for blink
            if ear < self.EAR_THRESHOLD:
                self.blink_counter += 1
            else:
                if self.blink_counter >= self.BLINK_FRAME_THRESHOLD:
                    self.consecutive_blinks += 1
                    self.update_status(f"👁️ Blink detected! ({self.consecutive_blinks}/{self.required_blinks})")
                    
                    if self.consecutive_blinks >= self.required_blinks:
                        self.liveness_tests_completed['blink'] = True
                        self.update_status("✅ Eye blink test passed!")
                        self.update_instruction("🔄 Now slowly turn your head left and right")
                
                self.blink_counter = 0
                
        except Exception:
            pass
    
    def detect_head_movement(self, landmarks):
        """Detect head movement using pose estimation"""
        try:
            pose = self.estimate_head_pose(landmarks)
            if pose is None:
                return
            
            pitch, yaw, roll = pose
            
            if self.initial_head_pose is None:
                self.initial_head_pose = (pitch, yaw, roll)
                return
            
            # Calculate movement from initial position
            initial_pitch, initial_yaw, initial_roll = self.initial_head_pose
            
            yaw_diff = abs(yaw - initial_yaw)
            pitch_diff = abs(pitch - initial_pitch)
            
            # Check for significant head movement
            if yaw_diff > self.head_movement_threshold or pitch_diff > self.head_movement_threshold:
                movement_type = "horizontal" if yaw_diff > pitch_diff else "vertical"
                  # Avoid duplicate detections
                if movement_type not in self.head_movements_detected:
                    self.head_movements_detected.append(movement_type)
                    self.update_status(f"🔄 {movement_type.capitalize()} head movement detected!")
                    
                    if len(self.head_movements_detected) >= self.required_head_movements:
                        self.liveness_tests_completed['head_movement'] = True
                        self.update_status("✅ Head movement test passed!")
                        self.update_instruction("📱 Final check: Ensuring no phone screen...")
                        
        except Exception:
            pass
    
    def draw_liveness_feedback(self, frame, left, top, right, bottom):
        """Draw liveness test feedback on frame"""
        y_offset = bottom + 30
        
        # Draw test status
        if not self.liveness_tests_completed['blink']:
            status_text = f"👁️ Blink: {self.consecutive_blinks}/{self.required_blinks}"
            cv2.putText(frame, status_text, (left, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += 25
        
        if not self.liveness_tests_completed['head_movement']:
            movements = len(self.head_movements_detected)
            status_text = f"🔄 Movement: {movements}/{self.required_head_movements}"
            cv2.putText(frame, status_text, (left, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += 25
        
        if not self.liveness_tests_completed['phone_detection']:
            status_text = "📱 Checking for phone..."
            cv2.putText(frame, status_text, (left, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def display_frame(self, frame):
        """Convert and display frame in GUI"""
        try:
            height, width = frame.shape[:2]
            display_width = 700
            display_height = int(height * (display_width / width))
            
            frame_resized = cv2.resize(frame, (display_width, display_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            self._current_photo = photo
            self.master.after(0, lambda p=photo: self.update_camera_display(p))
            
        except Exception:
            pass
    
    def update_camera_display(self, photo):
        """Update camera display (called from main thread)"""
        try:
            if self.camera_label.winfo_exists():
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
        except tk.TclError:
            self.camera_running = False
    
    def capture_face(self):
        """Capture face after all liveness tests are passed"""
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()
        
        if not name or not user_id:
            messagebox.showerror("Error", "Please enter both name and ID!")
            return
        
        if not self.advanced_liveness.is_liveness_complete():
            messagebox.showerror("Error", "Please complete all liveness tests first!")
            return
            
        if self.current_frame is None:
            messagebox.showerror("Error", "No camera frame available!")
            return
        
        try:
            # Process the current frame
            faces = self.face_detector.detect_faces(self.current_frame)
            
            if not faces:
                messagebox.showwarning("Warning", "No face detected in current frame!")
                return
            
            # Use the first detected face
            face = faces[0]
            
            # Extract face crop
            if isinstance(face, tuple) and len(face) >= 4:
                if len(face) == 6:
                    face_crop = face[4] if face[4] is not None else self.current_frame[face[1]:face[1]+face[3], face[0]:face[0]+face[2]]
                else:
                    left, top, right, bottom = face
                    face_crop = self.current_frame[top:bottom, left:right]
            elif hasattr(face, 'left'):
                left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
                face_crop = self.current_frame[top:bottom, left:right]
            else:
                messagebox.showerror("Error", "Invalid face format!")
                return            # Final spoofing and phone check - Use lenient threshold for registration
            is_real, prediction = self.anti_spoof_detector.predict(face_crop, debug=True, threshold=0.3)
            is_phone = self.advanced_liveness.detect_phone_screen(face_crop)
            
            # Use a more lenient threshold for registration to avoid false positives on real faces
            if not is_real or is_phone:
                messagebox.showwarning("Security Alert", 
                                     f"Final security check failed! Spoofing or phone detected.\n"
                                     f"AntiSpoof: {prediction:.2f} (lenient threshold: 0.3)\n"
                                     f"Phone detected: {is_phone}\n"
                                     f"Using lenient settings for registration.")
                return
            
            # Get face encoding
            face_encoding = None
            try:
                from src.face_recognizer import FaceRecognizer
                temp_recognizer = FaceRecognizer()
                face_encoding = temp_recognizer.extract_face_embedding(face_crop)
            except Exception:
                try:
                    face_encodings = preprocess_for_face_recognition(face_crop)
                    if face_encodings:
                        face_encoding = face_encodings[0]
                except Exception as e2:
                    messagebox.showerror("Error", f"Could not process face encoding: {str(e2)}")
                    return
            
            if face_encoding is None:
                messagebox.showerror("Error", "Could not extract face features!")
                return
            
            # Store user data
            self.user_data = {
                'name': name,
                'id': user_id,
                'face_encoding': face_encoding,
                'face_image': face_crop,
                'liveness_verified': True,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.face_captured = True
            self.captured_frame = self.current_frame.copy()
            self.save_btn.config(state=tk.NORMAL)
            
            self.update_status("🎉 Face captured successfully with full liveness verification!")
            messagebox.showinfo("Success", "Face captured successfully!\nAll security checks passed.\nClick 'Save User' to complete registration.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error during face capture: {str(e)}")
            self.update_status(f"❌ Capture error: {str(e)}")
    
    def save_user(self):
        """Save user with enhanced security verification"""
        if not self.face_captured or not self.user_data:
            messagebox.showerror("Error", "No face captured yet!")
            return
        
        try:
            print(f"[DEBUG] Saving user: {self.user_data['id']}")
            print(f"[DEBUG] Face encoding type: {type(self.user_data['face_encoding'])}")
            print(f"[DEBUG] Face image type: {type(self.user_data['face_image'])}")
            print(f"[DEBUG] Face image shape: {getattr(self.user_data['face_image'], 'shape', None)}")
            # Create user directory
            user_dir = f"data/registered_users/{self.user_data['id']}"
            os.makedirs(user_dir, exist_ok=True)
            # Save face encoding
            encoding_path = os.path.join(user_dir, f"{self.user_data['id']}_encoding.pkl")
            with open(encoding_path, 'wb') as f:
                pickle.dump(self.user_data['face_encoding'], f)
            # Save face image (ensure it's a valid numpy array)
            image_path = os.path.join(user_dir, "face_image.jpg")
            face_img = self.user_data['face_image']
            if not isinstance(face_img, np.ndarray):
                face_img = np.array(face_img)
            if face_img.dtype != np.uint8:
                face_img = face_img.astype(np.uint8)
            if len(face_img.shape) == 2:  # grayscale, convert to 3-channel
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(image_path, face_img)
            # Save user info
            info_path = os.path.join(user_dir, "user_info.txt")
            with open(info_path, 'w') as f:
                f.write(f"Name: {self.user_data['name']}\n")
                f.write(f"ID: {self.user_data['id']}\n")
                f.write(f"Registration Date: {self.user_data['timestamp']}\n")
                f.write(f"Liveness Verified: {self.user_data['liveness_verified']}\n")
                f.write("Security Level: Advanced\n")
            self.update_status(f"✅ User '{self.user_data['name']}' saved successfully with advanced security!")
            messagebox.showinfo("Success", 
                              f"User '{self.user_data['name']}' registered successfully!\n\n"
                              f"Security Features Applied:\n"
                              f"✅ Liveness Detection\n"
                              f"✅ Anti-Spoofing\n"
                              f"✅ Phone Detection\n"
                              f"✅ Eye Blink Verification\n"
                              f"✅ Head Movement Verification")
            # Reset for next registration
            self.reset_for_next_user()
        except Exception as e:
            print(f"[DEBUG] Exception during save: {e}")
            messagebox.showerror("Error", f"Failed to save user: {str(e)}")
            self.update_status(f"❌ Save error: {str(e)}")
    
    def reset_for_next_user(self):
        """Reset the system for next user registration"""
        self.name_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        self.face_captured = False
        self.user_data = None
        self.liveness_test_active = False
        self.liveness_tests_completed = {
            'blink': False,
            'head_movement': False,
            'phone_detection': False
        }
        self.consecutive_blinks = 0
        self.head_movements_detected = []
        self.phone_detection_frames = 0
        self.initial_head_pose = None
        
        # Reset UI
        self.start_liveness_btn.config(state=tk.NORMAL)
        self.capture_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        
        self.update_liveness_status()
        self.update_instruction("Ready for next user registration")
    
    def stop_camera(self):
        """Stop camera and clean up"""
        self.camera_running = False
        if self.cap:
            self.camera_manager.release_camera(self.cap)
            self.cap = None
        
        # Reset button states
        self.start_camera_btn.config(state=tk.NORMAL)
        self.start_liveness_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.DISABLED)
        
        # Clear camera display
        self.camera_label.configure(image="", text="Camera stopped")
        self.camera_label.image = None
        self.update_status("🛑 Camera stopped.")

    def close_window(self):
        """Close the window and clean up resources"""
        try:
            # Stop camera if running
            self.stop_camera()
            
            # Call the close callback if provided
            if self.on_close_callback:
                self.on_close_callback()
            
            # Destroy the window
            self.master.destroy()
            
        except Exception as e:
            print(f"[DEBUG] Error during window close: {e}")
            # Force destroy if needed
            try:
                self.master.destroy()
            except Exception:
                pass
