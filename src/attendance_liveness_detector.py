# src/attendance_liveness_detector.py
"""
Enhanced Attendance Liveness Detector
Automatic liveness detection for attendance marking with:
- Eye blink detection
- Head/body movement detection  
- Phone screen detection and anti-spoofing
- Real-time verification without user interaction
"""

import cv2
import numpy as np
import dlib
import time
from collections import deque
import os


class AttendanceLivenessDetector:
    def __init__(self, predictor_path="models/shape_predictor_68_face_landmarks.dat"):
        """Initialize the attendance liveness detector"""
        self.predictor_path = predictor_path
        self.use_landmarks = False
        self.predictor = None
        
        # Initialize dlib predictor if available
        try:
            if os.path.exists(predictor_path):
                self.predictor = dlib.shape_predictor(predictor_path)
                self.use_landmarks = True
                print("[INFO] Dlib landmark predictor loaded for liveness detection")
            else:
                print("[WARNING] Landmark predictor not found, using simplified detection")
        except Exception as e:
            print(f"[WARNING] Failed to load landmark predictor: {e}")
        
        # Liveness tracking for each user
        self.user_liveness_data = {}
        
        # Blink detection parameters
        self.blink_threshold = 0.26
        self.blink_frames_threshold = 2
        self.required_blinks = 2
        
        # Movement detection parameters
        self.movement_threshold = 25
        self.required_movement_frames = 10
        
        # Phone detection parameters
        self.phone_detection_threshold = 0.15
        self.max_phone_score = 3
        
        # Timing parameters
        self.liveness_verification_time = 3.0  # seconds
        self.min_frames_for_verification = 30  # minimum frames
        
    def initialize_user_tracking(self, user_id):
        """Initialize liveness tracking for a specific user"""
        self.user_liveness_data[user_id] = {
            'start_time': time.time(),
            'frame_count': 0,
            'blink_count': 0,
            'blink_counter': 0,
            'ear_history': deque(maxlen=10),
            'face_positions': deque(maxlen=20),
            'initial_position': None,
            'movement_detected': False,
            'phone_score': 0,
            'liveness_verified': False,
            'verification_complete': False,
            'last_blink_time': 0,
            'movement_variance': 0
        }
    
    def calculate_eye_aspect_ratio(self, eye_points):
        """Calculate Eye Aspect Ratio (EAR) for blink detection"""
        try:
            # Vertical eye landmarks
            A = np.linalg.norm(eye_points[1] - eye_points[5])
            B = np.linalg.norm(eye_points[2] - eye_points[4])
            # Horizontal eye landmark
            C = np.linalg.norm(eye_points[0] - eye_points[3])
              # Eye aspect ratio
            ear = (A + B) / (2.0 * C)
            return ear
        except Exception:
            return 0.3
    
    def detect_blinks(self, frame, face_landmarks, user_id):
        """Detect blinks using Eye Aspect Ratio"""
        if user_id not in self.user_liveness_data:
            return False
        
        data = self.user_liveness_data[user_id]
        current_time = time.time()
        
        try:
            if self.use_landmarks and face_landmarks is not None:
                # Extract eye landmarks (dlib 68-point model)
                left_eye = face_landmarks[36:42]
                right_eye = face_landmarks[42:48]
                
                # Calculate EAR for both eyes
                left_ear = self.calculate_eye_aspect_ratio(left_eye)
                right_ear = self.calculate_eye_aspect_ratio(right_eye)
                ear = (left_ear + right_ear) / 2.0
            else:
                # Fallback to simplified detection
                ear = self.detect_blinks_simplified(frame)
            
            # Store EAR history
            data['ear_history'].append(ear)
            
            # Detect blink
            if len(data['ear_history']) >= 3:
                if ear < self.blink_threshold:
                    data['blink_counter'] += 1
                else:
                    if data['blink_counter'] >= self.blink_frames_threshold:
                        # Valid blink detected
                        if current_time - data['last_blink_time'] > 0.3:  # Avoid double counting
                            data['blink_count'] += 1
                            data['last_blink_time'] = current_time
                            print(f"[DEBUG] Blink detected for {user_id}: {data['blink_count']}/{self.required_blinks}")
                    
                    data['blink_counter'] = 0
            
            return data['blink_count'] >= self.required_blinks
            
        except Exception as e:
            print(f"Blink detection error: {e}")
            return False
    
    def detect_blinks_simplified(self, frame):
        """Simplified blink detection without landmarks"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Simple variance-based approach
            # Lower variance in eye region indicates potential blink
            h, w = gray.shape
            eye_region = gray[int(h*0.3):int(h*0.6), int(w*0.2):int(w*0.8)]
            
            if eye_region.size > 0:
                variance = np.var(eye_region)
                # Normalize variance to EAR-like scale
                ear = max(0.1, min(0.4, variance / 1000.0))
                return ear            
            return 0.3
            
        except Exception:
            return 0.3
    
    def detect_movement(self, face_bbox, user_id):
        """Detect head/body movement"""
        if user_id not in self.user_liveness_data:
            return False
        
        data = self.user_liveness_data[user_id]
        
        try:
            # Extract face center from bbox
            if isinstance(face_bbox, tuple) and len(face_bbox) >= 4:
                if len(face_bbox) == 6:
                    x, y, w, h = face_bbox[:4]
                else:
                    x, y, w, h = face_bbox
                
                face_center = (x + w//2, y + h//2)
                data['face_positions'].append(face_center)
                
                # Set initial position after stabilization
                if data['initial_position'] is None and len(data['face_positions']) >= 5:
                    positions = list(data['face_positions'])[-5:]
                    data['initial_position'] = np.mean(positions, axis=0)
                    return False
                
                # Calculate movement variance
                if data['initial_position'] is not None and len(data['face_positions']) >= self.required_movement_frames:
                    recent_positions = np.array(list(data['face_positions'])[-10:])
                    movement_variance = np.var(recent_positions, axis=0)
                    total_variance = np.sum(movement_variance)
                    
                    data['movement_variance'] = total_variance
                    
                    # Check if sufficient movement detected
                    if total_variance > self.movement_threshold:
                        data['movement_detected'] = True
                        print(f"[DEBUG] Movement detected for {user_id}: variance={total_variance:.2f}")
                        return True
            
            return data['movement_detected']
            
        except Exception as e:
            print(f"Movement detection error: {e}")
            return False
    
    def detect_phone_screen(self, face_crop, user_id):
        """Enhanced phone screen detection"""
        if user_id not in self.user_liveness_data:
            return True  # Assume phone if no data
        
        data = self.user_liveness_data[user_id]
        
        try:
            if face_crop is None or face_crop.size == 0:
                return True
            
            # Convert to grayscale
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Multiple phone detection methods
            phone_indicators = 0
            
            # 1. Texture uniformity (phones have very uniform textures)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 50:  # Very smooth texture
                phone_indicators += 1
            
            # 2. Edge density (real faces have more natural edges)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            if edge_density < 0.05:  # Too few edges
                phone_indicators += 1
            
            # 3. Color uniformity check
            if len(face_crop.shape) == 3:
                color_std = np.std(face_crop.reshape(-1, 3), axis=0)
                avg_color_std = np.mean(color_std)
                if avg_color_std < 15:  # Very uniform colors
                    phone_indicators += 1
            
            # 4. Brightness uniformity (phone screens often have uniform lighting)
            brightness_std = np.std(gray)
            if brightness_std < 20:
                phone_indicators += 1
            
            # 5. Check for rectangular patterns (phone screen borders)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rectangular_contours = 0
            for contour in contours:
                if cv2.contourArea(contour) > 100:
                    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                    if len(approx) == 4:
                        rectangular_contours += 1
            
            if rectangular_contours > 2:
                phone_indicators += 1
            
            # Update phone score
            data['phone_score'] += phone_indicators
            
            # Phone detected if too many indicators
            is_phone = data['phone_score'] > self.max_phone_score
            
            if is_phone:
                print(f"[DEBUG] Phone detected for {user_id}: score={data['phone_score']}, indicators={phone_indicators}")
            
            return is_phone
            
        except Exception as e:
            print(f"Phone detection error: {e}")
            return False
    
    def verify_liveness(self, frame, face_bbox, face_landmarks, user_id):
        """
        Main liveness verification function for attendance
        Returns: (is_live, verification_complete, status_message)
        """
        if user_id not in self.user_liveness_data:
            self.initialize_user_tracking(user_id)
        
        data = self.user_liveness_data[user_id]
        current_time = time.time()
        elapsed_time = current_time - data['start_time']
        data['frame_count'] += 1
          # Extract face crop for phone detection
        try:
            if isinstance(face_bbox, tuple) and len(face_bbox) >= 4:
                if len(face_bbox) == 6:
                    x, y, w, h = face_bbox[:4]
                    face_crop = face_bbox[4] if face_bbox[4] is not None else frame[y:y+h, x:x+w]
                else:
                    x, y, w, h = face_bbox
                    face_crop = frame[y:y+h, x:x+w]
            else:
                return False, False, "Invalid face detection"
        except Exception:
            return False, False, "Face extraction failed"
        
        # 1. Phone detection (immediate rejection)
        if self.detect_phone_screen(face_crop, user_id):
            return False, True, "🚫 PHONE/SCREEN DETECTED - Use real face only!"
        
        # 2. Liveness checks
        blink_verified = self.detect_blinks(frame, face_landmarks, user_id)
        movement_verified = self.detect_movement(face_bbox, user_id)
        
        # Status messages
        status_parts = []
        if blink_verified:
            status_parts.append("👁️ Blinks:✅")
        else:
            status_parts.append(f"👁️ Blinks:{data['blink_count']}/{self.required_blinks}")
        
        if movement_verified:
            status_parts.append("🔄 Movement:✅")
        else:
            status_parts.append("🔄 Movement:⏳")
        
        # Check if verification is complete
        if elapsed_time >= self.liveness_verification_time and data['frame_count'] >= self.min_frames_for_verification:
            # Final verification
            liveness_verified = blink_verified and movement_verified
            data['liveness_verified'] = liveness_verified
            data['verification_complete'] = True
            
            if liveness_verified:
                status_message = "✅ LIVENESS VERIFIED - Attendance can be marked"
            else:
                missing = []
                if not blink_verified:
                    missing.append("eye blinks")
                if not movement_verified:
                    missing.append("head movement")
                status_message = f"❌ LIVENESS FAILED - Missing: {', '.join(missing)}"
            
            return liveness_verified, True, status_message
        
        # In progress
        time_left = max(0, self.liveness_verification_time - elapsed_time)
        status_message = f"🔍 Verifying liveness... {' | '.join(status_parts)} | {time_left:.1f}s"
        
        return False, False, status_message
    
    def reset_user_verification(self, user_id):
        """Reset liveness verification for a user"""
        if user_id in self.user_liveness_data:
            del self.user_liveness_data[user_id]
    
    def cleanup_old_tracking(self, max_age=30):
        """Clean up old tracking data"""
        current_time = time.time()
        to_remove = []
        
        for user_id, data in self.user_liveness_data.items():
            if current_time - data['start_time'] > max_age:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.user_liveness_data[user_id]
    
    def get_user_verification_status(self, user_id):
        """Get current verification status for a user"""
        if user_id not in self.user_liveness_data:
            return "Not started"
        
        data = self.user_liveness_data[user_id]
        if data['verification_complete']:
            return "Completed" if data['liveness_verified'] else "Failed"
        else:
            return "In progress"
