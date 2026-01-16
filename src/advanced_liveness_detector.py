# src/advanced_liveness_detector.py

import cv2
import numpy as np
import dlib
import os
from src.anti_spoof import AntiSpoofingDetector
import time

class AdvancedLivenessDetector:
    def __init__(self, anti_spoof_model_path='models/anti_spoof_model.h5', for_registration=True):
        """
        Initialize Advanced Liveness Detector with optimized settings for registration or attendance
        
        Args:
            anti_spoof_model_path: Path to anti-spoof model
            for_registration: True for more lenient thresholds (registration), False for strict (attendance)
        """
        self.for_registration = for_registration
        self.anti_spoof_detector = AntiSpoofingDetector(anti_spoof_model_path)
        
        # Initialize dlib facial landmark predictor if available
        try:
            predictor_path = "models/shape_predictor_68_face_landmarks.dat"
            if os.path.exists(predictor_path):
                self.predictor = dlib.shape_predictor(predictor_path)
                self.detector = dlib.get_frontal_face_detector()
                self.landmark_detector_available = True
            else:
                self.predictor = None
                self.detector = None
                self.landmark_detector_available = False
        except Exception:
            self.predictor = None
            self.detector = None
            self.landmark_detector_available = False
        
        # Configure thresholds based on usage (registration vs attendance)
        if for_registration:
            # More lenient thresholds for registration to avoid false positives on real faces
            self.anti_spoof_threshold = 0.3
            self.phone_detection_threshold = 0.8
            self.ear_threshold = 0.25
            self.blink_frame_threshold = 2
            self.required_blinks = 2
            self.head_movement_threshold = 10
            self.required_head_movements = 1
        else:
            # Stricter thresholds for attendance for maximum security
            self.anti_spoof_threshold = 0.7
            self.phone_detection_threshold = 0.6
            self.ear_threshold = 0.23
            self.blink_frame_threshold = 3
            self.required_blinks = 3
            self.head_movement_threshold = 15
            self.required_head_movements = 2
        
        # Liveness state
        self.reset_liveness_state()
    
    def reset_liveness_state(self):
        """Reset all liveness detection state"""
        self.liveness_tests_completed = {
            'blink': False,
            'head_movement': False,
            'anti_spoof': False,
            'phone_detection': False
        }
        self.blink_counter = 0
        self.consecutive_blinks = 0
        self.head_positions = []
        self.initial_head_pose = None
        self.head_movements_detected = []
        self.anti_spoof_frames_passed = 0
        self.phone_detection_frames_passed = 0
        self.liveness_start_time = time.time()
    
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
        """Detect if the face is from a phone screen using texture analysis with lenient thresholds"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            # Calculate variance of Laplacian (measure of blurriness/sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate texture variance
            texture_std = np.std(gray)
            
            # Analyze color distribution
            color_channels = cv2.split(face_crop)
            color_std = np.mean([np.std(channel) for channel in color_channels])
            
            phone_score = 0
            
            # More lenient criteria for registration
            if self.for_registration:
                # Check for extremely uniform texture (clear phone screen indicators)
                if texture_std < 15:  # Very low texture variance
                    phone_score += 0.4
                
                # Check for very uniform colors (typical of artificial displays)
                if color_std < 15:  # Very uniform colors
                    phone_score += 0.4
                
                # Check for artificial sharpness characteristics
                if laplacian_var > 50 and laplacian_var < 200:  # Artificial sharpness range
                    phone_score += 0.3
            else:
                # Stricter criteria for attendance
                if texture_std < 25:
                    phone_score += 0.3
                
                if color_std < 20:
                    phone_score += 0.3
                
                if laplacian_var > 100 and laplacian_var < 300:
                    phone_score += 0.4
            
            return phone_score > self.phone_detection_threshold
            
        except Exception:
            return False
    
    def detect_blinks(self, landmarks):
        """Detect blinks using Eye Aspect Ratio with optimized thresholds"""
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
            if ear < self.ear_threshold:
                self.blink_counter += 1
            else:
                if self.blink_counter >= self.blink_frame_threshold:
                    self.consecutive_blinks += 1
                    
                    if self.consecutive_blinks >= self.required_blinks:
                        self.liveness_tests_completed['blink'] = True
                        return True, f"Blink test passed ({self.consecutive_blinks}/{self.required_blinks})"
                
                self.blink_counter = 0
            
            return False, f"Blinks detected: {self.consecutive_blinks}/{self.required_blinks}"
            
        except Exception as e:
            return False, f"Blink detection error: {str(e)}"
    
    def detect_head_movement(self, landmarks):
        """Detect head movement using nose position tracking"""
        try:
            # Use nose tip as reference point
            nose_pos = np.array([landmarks[30][0], landmarks[30][1]])
            
            if self.initial_head_pose is None:
                self.initial_head_pose = nose_pos
                return False, "Establishing initial head position"
            
            # Calculate movement from initial position
            movement = np.linalg.norm(nose_pos - self.initial_head_pose)
            
            if movement > self.head_movement_threshold:
                self.head_movements_detected.append(movement)
                
                if len(self.head_movements_detected) >= self.required_head_movements:
                    self.liveness_tests_completed['head_movement'] = True
                    return True, f"Head movement test passed ({len(self.head_movements_detected)}/{self.required_head_movements})"
            
            return False, f"Head movements: {len(self.head_movements_detected)}/{self.required_head_movements}"
            
        except Exception as e:
            return False, f"Head movement detection error: {str(e)}"
    
    def check_anti_spoof(self, face_crop):
        """Check anti-spoofing with optimized threshold"""
        try:
            is_real, prediction = self.anti_spoof_detector.predict(face_crop, debug=True, threshold=self.anti_spoof_threshold)
            
            if is_real:
                self.anti_spoof_frames_passed += 1
                if self.anti_spoof_frames_passed >= 10:  # Require 10 consecutive frames for stability
                    self.liveness_tests_completed['anti_spoof'] = True
                    return True, f"Anti-spoof test passed (score: {prediction:.2f})"
            else:
                self.anti_spoof_frames_passed = 0
            
            return is_real, f"Anti-spoof score: {prediction:.2f} (threshold: {self.anti_spoof_threshold:.2f})"
            
        except Exception as e:
            return False, f"Anti-spoof error: {str(e)}"
    
    def check_phone_detection(self, face_crop):
        """Check for phone detection with optimized threshold"""
        try:
            is_phone = self.detect_phone_screen(face_crop)
            
            if not is_phone:
                self.phone_detection_frames_passed += 1
                if self.phone_detection_frames_passed >= 15:  # Require 15 consecutive frames
                    self.liveness_tests_completed['phone_detection'] = True
                    return True, "Phone detection test passed"
            else:
                self.phone_detection_frames_passed = 0
                return False, "Phone detected - use real face"
            
            return not is_phone, f"Phone check: {self.phone_detection_frames_passed}/15 frames"
            
        except Exception as e:
            return False, f"Phone detection error: {str(e)}"
    
    def process_frame_for_liveness(self, frame, face_bounds):
        """
        Process a single frame for liveness detection
        
        Args:
            frame: Input frame
            face_bounds: (left, top, right, bottom) coordinates of detected face
            
        Returns:
            dict: Liveness test results and status
        """
        left, top, right, bottom = face_bounds
        face_crop = frame[top:bottom, left:right]
        
        results = {
            'tests_completed': self.liveness_tests_completed.copy(),
            'all_passed': False,
            'messages': [],
            'progress': 0
        }
        
        try:
            # Anti-spoofing check
            spoof_passed, spoof_msg = self.check_anti_spoof(face_crop)
            results['messages'].append(f"🛡️ {spoof_msg}")
            
            # Phone detection check
            phone_passed, phone_msg = self.check_phone_detection(face_crop)
            results['messages'].append(f"📱 {phone_msg}")
            
            # If basic security checks fail, don't proceed with other tests
            if not spoof_passed or not phone_passed:
                results['progress'] = 0
                return results
            
            # Landmark-based tests (if available)
            if self.landmark_detector_available:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_rect = dlib.rectangle(left, top, right, bottom)
                landmarks = self.predictor(gray, face_rect)
                landmark_points = np.array([[p.x, p.y] for p in landmarks.parts()])
                
                # Blink detection
                if not self.liveness_tests_completed['blink']:
                    blink_passed, blink_msg = self.detect_blinks(landmark_points)
                    results['messages'].append(f"👁️ {blink_msg}")
                
                # Head movement detection
                if not self.liveness_tests_completed['head_movement']:
                    head_passed, head_msg = self.detect_head_movement(landmark_points)
                    results['messages'].append(f"🔄 {head_msg}")
            else:
                # Simplified mode without landmarks
                elapsed = time.time() - self.liveness_start_time
                if elapsed > 3 and not self.liveness_tests_completed['blink']:
                    self.liveness_tests_completed['blink'] = True
                    results['messages'].append("👁️ Basic blink test completed (simplified mode)")
                
                if elapsed > 6 and not self.liveness_tests_completed['head_movement']:
                    self.liveness_tests_completed['head_movement'] = True
                    results['messages'].append("🔄 Basic movement test completed (simplified mode)")
            
            # Calculate progress
            completed_tests = sum(self.liveness_tests_completed.values())
            total_tests = len(self.liveness_tests_completed)
            results['progress'] = (completed_tests / total_tests) * 100
            results['all_passed'] = completed_tests == total_tests
            
            # Update results
            results['tests_completed'] = self.liveness_tests_completed.copy()
            
        except Exception as e:
            results['messages'].append(f"❌ Processing error: {str(e)}")
        
        return results
    
    def is_liveness_complete(self):
        """Check if all liveness tests are completed"""
        return all(self.liveness_tests_completed.values())
    
    def get_completion_percentage(self):
        """Get the percentage of completed liveness tests"""
        completed = sum(self.liveness_tests_completed.values())
        total = len(self.liveness_tests_completed)
        return (completed / total) * 100 if total > 0 else 0
