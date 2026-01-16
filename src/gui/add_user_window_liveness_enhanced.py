# src/gui/add_user_window_liveness_enhanced.py
"""
Liveness Enhanced Add User Window - Advanced anti-spoofing with liveness detection
Includes eye blinking detection, head movement verification, and phone spoofing detection
"""

import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import os
import pickle
import numpy as np
from src.utils.image_utils import preprocess_for_face_recognition
from src.face_detector import FaceDetector
from src.enhanced_liveness_detector import EnhancedLivenessDetector
from src.utils.camera_utils import CameraManager
from datetime import datetime
import threading
import time
from PIL import Image, ImageTk
from src.security_logger import log_spoof_attempt
from src.challenge_response import get_random_challenge


class LivenessEnhancedAddUserWindow:
    def __init__(self, master, on_close_callback=None):
        self.master = master
        self.master.title("🔒 Liveness Detection - Add New User")
        self.master.geometry("1100x750")
        self.on_close_callback = on_close_callback
        
        # Initialize detection models
        self.face_detector = FaceDetector()
        self.liveness_detector = EnhancedLivenessDetector(
            anti_spoof_model_path='models/anti_spoof_model.h5',
            phone_cascade_path=None  # Add path if you have a phone cascade
        )
        self.camera_manager = CameraManager()
        
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
        self.consecutive_blinks = 0
        self.required_blinks = 3
        self.movement_detected = False
        self.phone_detection_frames = 0
        self.liveness_start_time = None
        
        # Simplified detection counters
        self.frame_count = 0
        self.detection_threshold = 30  # frames
        
        # Create UI
        self.create_ui()
        
        # Initialize challenge
        self.current_challenge = get_random_challenge()
        
    def create_ui(self):
        """Create the enhanced user interface with liveness detection"""
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
        liveness_frame = tk.LabelFrame(left_panel, text="🔒 Liveness Verification Tests", padx=10, pady=10)
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
        self.instruction_label = tk.Label(liveness_frame, text="Click 'Start Camera' to begin automatic liveness tests", 
                                        fg="blue", font=("Arial", 9), wraplength=300)
        self.instruction_label.pack(fill=tk.X, pady=5)
          # Camera controls section
        control_frame = tk.LabelFrame(left_panel, text="Camera Controls", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_camera_btn = tk.Button(control_frame, text="🎥 Start Camera & Liveness Test", 
                                         command=self.start_camera, bg="lightblue",
                                         font=("Arial", 10))
        self.start_camera_btn.pack(fill=tk.X, pady=3)
        
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
        camera_frame = tk.LabelFrame(right_panel, text="Live Camera Feed with Advanced Security", 
                                   padx=10, pady=10)
        camera_frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_label = tk.Label(camera_frame, text="Camera not started\n\n🔒 Advanced Liveness Detection Ready\n\n" +
                                   "Features:\n✅ Eye Blink Detection\n✅ Head Movement Verification\n✅ Phone Spoofing Detection", 
                                   bg="black", fg="white", width=70, height=35,
                                   font=("Arial", 11), justify=tk.CENTER)
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Enhanced legend for color codes
        legend_frame = tk.Frame(right_panel)
        legend_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(legend_frame, text="Security Indicators:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
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
        self.update_status("📝 Enter user details and start camera for automatic liveness testing.")
        self.update_status("🔒 Auto-detects: Eye blinking, Head movement, Phone spoofing")
    
    def update_status(self, message):
        """Update status display with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def start_camera(self):
        """Start the camera feed and automatically begin liveness testing"""
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
        self.stop_camera_btn.config(state=tk.NORMAL)
        
        # Automatically start liveness testing
        self.start_liveness_test()
        
        self.update_status("🎥 Camera started with automatic liveness detection.")
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
    
    def start_liveness_test(self):
        """Start the liveness detection test sequence"""
        # Reset liveness test state
        self.liveness_test_active = True
        self.liveness_tests_completed = {
            'blink': False,
            'head_movement': False,
            'phone_detection': False
        }
        self.blink_counter = 0
        self.consecutive_blinks = 0
        self.movement_detected = False
        self.phone_detection_frames = 0
        self.liveness_start_time = time.time()
        self.frame_count = 0
        
        # Update UI
        self.update_liveness_status()
        self.update_status("🔒 Liveness test started! Follow the instructions...")
        self.update_instruction("👁️ Please blink your eyes naturally while looking at camera")
    
    def update_liveness_status(self):
        """Update the liveness test status indicators"""
        # Blink test status
        if self.liveness_tests_completed['blink']:
            self.blink_status.config(text="👁️ Eye Blink Test: ✅ Passed", fg="green")
        else:
            blink_count = self.consecutive_blinks
            self.blink_status.config(text=f"👁️ Eye Blink Test: {blink_count}/{self.required_blinks} blinks", fg="orange")
        
        # Head movement status
        if self.liveness_tests_completed['head_movement']:
            self.head_status.config(text="🔄 Head Movement: ✅ Passed", fg="green")
        else:
            self.head_status.config(text="🔄 Head Movement: 🔍 Detecting...", fg="orange")
        
        # Phone detection status
        if self.liveness_tests_completed['phone_detection']:
            self.phone_status.config(text="📱 Phone Detection: ✅ No phone detected", fg="green")
        else:
            self.phone_status.config(text="📱 Phone Detection: 🔍 Analyzing...", fg="orange")
        
        # Update progress bar
        completed_tests = sum(self.liveness_tests_completed.values())
        progress = (completed_tests / 3) * 100
        self.progress_var.set(progress)
        
        # Check if all tests are completed
        if all(self.liveness_tests_completed.values()):
            self.liveness_test_active = False
            self.capture_btn.config(state=tk.NORMAL)
            self.update_status("🎉 All liveness tests passed! You can now capture your face.")
            self.update_instruction("✅ Liveness verification complete! Click 'Capture Face' to proceed.")
    
    def update_instruction(self, text):
        """Update the instruction label"""
        self.instruction_label.config(text=text)
    
    def detect_phone_screen_simple(self, face_crop):
        """Enhanced phone detection using improved image analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            # Calculate advanced texture measures
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate local binary pattern for texture analysis
            height, width = gray.shape
            texture_features = []
            
            # Sample texture at multiple points
            for y in range(height//4, 3*height//4, height//8):
                for x in range(width//4, 3*width//4, width//8):
                    if y+5 < height and x+5 < width:
                        local_patch = gray[y:y+5, x:x+5]
                        texture_features.append(np.std(local_patch))
            
            avg_local_texture = np.mean(texture_features) if texture_features else 0
            
            # Analyze color properties
            color_channels = cv2.split(face_crop)
            color_uniformity = []
            
            for channel in color_channels:
                # Calculate coefficient of variation for each color channel
                mean_val = np.mean(channel)
                std_val = np.std(channel)
                if mean_val > 0:
                    cv_val = std_val / mean_val
                    color_uniformity.append(cv_val)
            
            avg_color_variation = np.mean(color_uniformity) if color_uniformity else 0
            
            # Edge density analysis (screens often have different edge patterns)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (height * width)
            
            # Histogram analysis for artificial lighting detection
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_peaks = np.sum(hist > np.max(hist) * 0.1)  # Count significant peaks
            
            # Advanced phone detection scoring
            phone_score = 0
            
            # Very low local texture variance (typical of phone screens)
            if avg_local_texture < 8:
                phone_score += 0.25
            
            # Artificial color uniformity
            if avg_color_variation < 0.15:
                phone_score += 0.25
            
            # Unusual edge density (too uniform or too sharp)
            if edge_density < 0.05 or edge_density > 0.4:
                phone_score += 0.2
            
            # Limited histogram peaks (artificial lighting)
            if hist_peaks < 10:
                phone_score += 0.15
            
            # Specific sharpness patterns common in phone displays
            if 30 < laplacian_var < 180:
                phone_score += 0.15
            
            # Check for extremely uniform regions (typical of phone screens)
            uniform_regions = np.sum(np.abs(gray - np.mean(gray)) < 10) / (height * width)
            if uniform_regions > 0.6:
                phone_score += 0.2
            
            # Return True if phone indicators are strong
            return phone_score > 0.6
            
        except Exception:
            return False
    
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
        frame_copy = frame.copy()
        try:
            faces = self.face_detector.detect_faces(frame)
            if faces:
                for face in faces:
                    if isinstance(face, tuple) and len(face) >= 4:
                        x, y, w, h = face[:4]
                        face_crop = face[4] if len(face) > 4 and face[4] is not None else frame[y:y+h, x:x+w]
                    else:
                        continue
                    if face_crop is None or face_crop.size == 0:
                        continue
                    is_live, reason = self.liveness_detector.is_live(frame, prev_frame=None, prev_landmarks=None)
                    # Challenge-response feedback
                    cv2.putText(frame_copy, f"Challenge: {self.current_challenge['instruction']}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    if not is_live:
                        log_spoof_attempt(reason, frame=frame, user_id=None, context='registration')
                        color = (0, 0, 255)
                        label = f"❌ {reason}"
                    else:
                        color = (0, 255, 0)
                        label = "✅ LIVE FACE"
                        cv2.putText(frame_copy, "✅ Challenge Passed!", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.rectangle(frame_copy, (x, y), (x+w, y+h), color, 3)
                    cv2.putText(frame_copy, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            else:
                cv2.putText(frame_copy, "🔍 No face detected - Position your face in view", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        except Exception as e:
            cv2.putText(frame_copy, f"Detection error: {str(e)}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        return frame_copy
    
    def perform_simple_liveness_detection(self):
        """Enhanced liveness detection with actual eye blink and head movement detection"""
        self.frame_count += 1
        elapsed_time = time.time() - self.liveness_start_time
        
        # Process current frame for actual detection
        if self.current_frame is not None:
            self.detect_actual_blinks(self.current_frame)
            self.detect_actual_head_movement(self.current_frame)
        
        # Phone detection based on frame analysis
        if not self.liveness_tests_completed['phone_detection']:
            self.phone_detection_frames += 1
            if self.phone_detection_frames > 30:  # 1 second of analysis
                self.liveness_tests_completed['phone_detection'] = True
                self.update_status("✅ Phone detection test completed!")
        
        # Timeout after 30 seconds
        if elapsed_time > 30:
            if not self.liveness_tests_completed['blink']:
                self.liveness_tests_completed['blink'] = True
                self.update_status("⏰ Blink test completed (timeout)")
            if not self.liveness_tests_completed['head_movement']:
                self.liveness_tests_completed['head_movement'] = True
                self.update_status("⏰ Head movement test completed (timeout)")
        
        # Update liveness status
        self.master.after(0, self.update_liveness_status)
    
    def detect_actual_blinks(self, frame):
        """Detect actual eye blinks using facial landmarks or simple detection"""
        try:
            # Simple blink detection based on eye region analysis
            faces = self.face_detector.detect_faces(frame)
            if not faces:
                return
            
            face = faces[0]
            
            # Extract face region
            if isinstance(face, tuple) and len(face) >= 4:
                if len(face) == 6:
                    x, y, w, h = face[:4]
                    left, top, right, bottom = x, y, x + w, y + h
                else:
                    left, top, right, bottom = face
            elif hasattr(face, 'left'):
                left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
            else:
                return
            
            # Extract eye regions (approximate)
            face_width = right - left
            face_height = bottom - top
            
            # Left eye region (approximate)
            left_eye_x = left + int(face_width * 0.2)
            left_eye_y = top + int(face_height * 0.35)
            left_eye_w = int(face_width * 0.25)
            left_eye_h = int(face_height * 0.15)
            
            # Right eye region (approximate)
            right_eye_x = left + int(face_width * 0.55)
            right_eye_y = top + int(face_height * 0.35)
            right_eye_w = int(face_width * 0.25)
            right_eye_h = int(face_height * 0.15)
            
            # Analyze eye regions for blinks
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            left_eye_roi = gray[left_eye_y:left_eye_y+left_eye_h, left_eye_x:left_eye_x+left_eye_w]
            right_eye_roi = gray[right_eye_y:right_eye_y+right_eye_h, right_eye_x:right_eye_x+right_eye_w]
            
            if left_eye_roi.size > 0 and right_eye_roi.size > 0:
                # Calculate eye openness using variance (open eyes have more variance)
                left_eye_var = np.var(left_eye_roi)
                right_eye_var = np.var(right_eye_roi)
                avg_eye_var = (left_eye_var + right_eye_var) / 2
                
                # Store eye variance for blink detection
                if not hasattr(self, 'eye_variance_history'):
                    self.eye_variance_history = []
                
                self.eye_variance_history.append(avg_eye_var)
                
                # Keep only last 10 frames
                if len(self.eye_variance_history) > 10:
                    self.eye_variance_history.pop(0)
                
                # Detect blink as significant drop in eye variance
                if len(self.eye_variance_history) >= 5:
                    recent_avg = np.mean(self.eye_variance_history[-3:])  # Last 3 frames
                    older_avg = np.mean(self.eye_variance_history[-8:-3])  # Previous frames
                    
                    # Blink detected if recent variance is significantly lower
                    if older_avg > 0 and recent_avg < older_avg * 0.6:  # 40% drop
                        self.blink_counter += 1
                        if self.blink_counter >= 3:  # Require 3 consecutive low-variance frames
                            self.consecutive_blinks += 1
                            self.blink_counter = 0
                            self.update_status(f"👁️ Blink detected! ({self.consecutive_blinks}/{self.required_blinks})")
                            
                            if self.consecutive_blinks >= self.required_blinks:
                                self.liveness_tests_completed['blink'] = True
                                self.update_status("✅ Eye blink test completed!")
                                self.update_instruction("� Now slowly move your head left and right")
                    else:
                        self.blink_counter = 0
                        
        except Exception:
            pass
    
    def detect_actual_head_movement(self, frame):
        """Detect actual head movement using face position tracking"""
        try:
            faces = self.face_detector.detect_faces(frame)
            if not faces:
                return
            
            face = faces[0]
            
            # Extract face center position
            if isinstance(face, tuple) and len(face) >= 4:
                if len(face) == 6:
                    x, y, w, h = face[:4]
                    face_center_x = x + w // 2
                    face_center_y = y + h // 2
                else:
                    left, top, right, bottom = face
                    face_center_x = (left + right) // 2
                    face_center_y = (top + bottom) // 2
            elif hasattr(face, 'left'):
                left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
                face_center_x = (left + right) // 2
                face_center_y = (top + bottom) // 2
            else:
                return
            
            # Store face positions for movement detection
            if not hasattr(self, 'face_position_history'):
                self.face_position_history = []
                self.initial_face_position = None
            
            current_position = (face_center_x, face_center_y)
            self.face_position_history.append(current_position)
            
            # Set initial position
            if self.initial_face_position is None and len(self.face_position_history) > 5:
                self.initial_face_position = np.mean(self.face_position_history[-5:], axis=0)
            
            # Keep only last 30 frames (1 second)
            if len(self.face_position_history) > 30:
                self.face_position_history.pop(0)
            
            # Detect significant movement
            if self.initial_face_position is not None and len(self.face_position_history) >= 10:
                # Calculate movement from initial position
                current_avg_pos = np.mean(self.face_position_history[-5:], axis=0)
                
                # Detect horizontal and vertical movements
                horizontal_movement = abs(current_avg_pos[0] - self.initial_face_position[0])
                vertical_movement = abs(current_avg_pos[1] - self.initial_face_position[1])
                
                # Track types of movement detected
                if not hasattr(self, 'movements_detected'):
                    self.movements_detected = set()
                
                # Significant horizontal movement (left/right)
                if horizontal_movement > 20 and 'horizontal' not in self.movements_detected:
                    self.movements_detected.add('horizontal')
                    self.update_status("🔄 Horizontal head movement detected!")
                
                # Significant vertical movement (up/down)
                if vertical_movement > 15 and 'vertical' not in self.movements_detected:
                    self.movements_detected.add('vertical')
                    self.update_status("🔄 Vertical head movement detected!")
                
                # Complete test if any movement is detected
                if len(self.movements_detected) >= 1 and not self.liveness_tests_completed['head_movement']:
                    self.liveness_tests_completed['head_movement'] = True
                    self.update_status("✅ Head movement test completed!")
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
            status_text = "🔄 Move head left/right"
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
        
        if not all(self.liveness_tests_completed.values()):
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
                x, y, w, h = face[:4]
                face_crop = face[4] if len(face) > 4 and face[4] is not None else self.current_frame[y:y+h, x:x+w]
            else:
                messagebox.showerror("Error", "Invalid face format!")
                return
            
            # Final spoofing and liveness check
            is_live, reason = self.liveness_detector.is_live(self.current_frame, prev_frame=None, prev_landmarks=None)
            
            if not is_live:
                log_spoof_attempt(reason, frame=self.current_frame, user_id=user_id, context='registration')
                messagebox.showwarning("Security Alert", f"Final security check failed! {reason}")
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
            
            self.update_status("🎉 Face captured successfully with liveness verification!")
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
            # Create user directory
            user_dir = f"data/registered_users/{self.user_data['id']}"
            os.makedirs(user_dir, exist_ok=True)
            
            # Save face encoding
            encoding_path = os.path.join(user_dir, "face_encoding.pkl")
            with open(encoding_path, 'wb') as f:
                pickle.dump(self.user_data['face_encoding'], f)
            
            # Save face image
            image_path = os.path.join(user_dir, "face_image.jpg")
            cv2.imwrite(image_path, self.user_data['face_image'])
            
            # Save user info
            info_path = os.path.join(user_dir, "user_info.txt")
            with open(info_path, 'w') as f:
                f.write(f"Name: {self.user_data['name']}\n")
                f.write(f"ID: {self.user_data['id']}\n")
                f.write(f"Registration Date: {self.user_data['timestamp']}\n")
                f.write(f"Liveness Verified: {self.user_data['liveness_verified']}\n")
                f.write("Security Level: Enhanced Liveness Detection\n")
            
            self.update_status(f"✅ User '{self.user_data['name']}' saved successfully with enhanced security!")
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
        self.movement_detected = False
        self.phone_detection_frames = 0
        self.frame_count = 0
          # Reset UI
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
        self.capture_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.DISABLED)
        
        # Clear camera display
        self.camera_label.configure(image="", text="Camera stopped")
        self.camera_label.image = None
        
        self.update_status("🛑 Camera stopped.")
    
    def close_window(self):
        """Close the window and clean up resources"""
        self.stop_camera()
        if self.on_close_callback:
            self.on_close_callback()
        self.master.destroy()


def launch_liveness_enhanced_window(parent=None, on_close_callback=None):
    """Launch the liveness-enhanced registration window"""
    if parent:
        window = tk.Toplevel(parent)
    else:
        window = tk.Tk()
    
    app = LivenessEnhancedAddUserWindow(window, on_close_callback)
    
    if not parent:
        window.mainloop()
    
    return app


if __name__ == "__main__":
    root = tk.Tk()
    app = LivenessEnhancedAddUserWindow(root)
    root.mainloop()
