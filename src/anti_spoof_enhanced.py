# src/anti_spoof_enhanced.py
"""
Enhanced Anti-Spoofing Detector with Phone Detection
Combines traditional anti-spoofing with advanced phone screen detection
"""

import numpy as np
import cv2
from tensorflow.keras.models import load_model
import os


class EnhancedAntiSpoofingDetector:
    def __init__(self, model_path='models/anti_spoof_model.h5'):
        """Initialize enhanced anti-spoofing detector"""
        self.model_path = model_path
        self.model = None
        self.input_size = (160, 160)
        
        # Load anti-spoofing model if available
        if os.path.exists(model_path):
            try:
                self.model = load_model(model_path)
                print(f"[INFO] Anti-spoofing model loaded from {model_path}")
            except Exception as e:
                print(f"[WARNING] Failed to load anti-spoofing model: {e}")
                self.model = None
        else:
            print(f"[WARNING] Anti-spoofing model not found at {model_path}")
        
        # Phone detection parameters
        self.phone_texture_threshold = 50
        self.phone_edge_threshold = 0.05
        self.phone_color_std_threshold = 15
        self.phone_brightness_std_threshold = 20
        self.phone_score_threshold = 3  # Number of phone indicators needed
        
    def preprocess(self, face_img):
        """Preprocess the face image for anti-spoofing prediction"""
        if face_img is None or face_img.size == 0:
            return None
        
        try:
            resized_face = cv2.resize(face_img, self.input_size)
            normalized_face = resized_face / 255.0
            input_tensor = np.expand_dims(normalized_face, axis=0)
            return input_tensor
        except Exception as e:
            print(f"Preprocessing error: {e}")
            return None
    
    def predict_with_model(self, face_img):
        """Use ML model for anti-spoofing prediction"""
        if self.model is None:
            return 0.5  # Neutral score if no model
        
        processed_img = self.preprocess(face_img)
        if processed_img is None:
            return 0.0
        
        try:
            prediction = self.model.predict(processed_img, verbose=0)[0][0]
            return prediction
        except Exception as e:
            print(f"Model prediction error: {e}")
            return 0.0
    
    def detect_phone_screen(self, face_img):
        """
        Advanced phone screen detection using multiple techniques
        Returns: (is_phone, confidence_score, detection_details)
        """
        if face_img is None or face_img.size == 0:
            return True, 1.0, "Empty image"
        
        try:
            # Convert to grayscale and get dimensions
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            detection_details = {}
            phone_indicators = 0
            
            # 1. Texture analysis - phones have very uniform/smooth textures
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            detection_details['texture_variance'] = laplacian_var
            if laplacian_var < self.phone_texture_threshold:
                phone_indicators += 1
                detection_details['texture_smooth'] = True
            else:
                detection_details['texture_smooth'] = False
            
            # 2. Edge density - real faces have more natural, varied edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            detection_details['edge_density'] = edge_density
            if edge_density < self.phone_edge_threshold:
                phone_indicators += 1
                detection_details['edges_sparse'] = True
            else:
                detection_details['edges_sparse'] = False
            
            # 3. Color uniformity - phone screens often have very uniform colors
            if len(face_img.shape) == 3:
                color_std = np.std(face_img.reshape(-1, 3), axis=0)
                avg_color_std = np.mean(color_std)
                detection_details['color_uniformity'] = avg_color_std
                if avg_color_std < self.phone_color_std_threshold:
                    phone_indicators += 1
                    detection_details['color_uniform'] = True
                else:
                    detection_details['color_uniform'] = False
            
            # 4. Brightness uniformity - phone screens have uniform lighting
            brightness_std = np.std(gray)
            detection_details['brightness_uniformity'] = brightness_std
            if brightness_std < self.phone_brightness_std_threshold:
                phone_indicators += 1
                detection_details['brightness_uniform'] = True
            else:
                detection_details['brightness_uniform'] = False
            
            # 5. Rectangular pattern detection - phone screens have rectangular borders
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rectangular_count = 0
            for contour in contours:
                if cv2.contourArea(contour) > 100:
                    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                    if len(approx) == 4:
                        rectangular_count += 1
            
            detection_details['rectangular_patterns'] = rectangular_count
            if rectangular_count > 2:
                phone_indicators += 1
                detection_details['has_rectangular_patterns'] = True
            else:
                detection_details['has_rectangular_patterns'] = False
            
            # 6. Frequency domain analysis - phone screens have specific frequency patterns
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.log(np.abs(f_shift))
            
            # Check for periodic patterns typical of digital displays
            spectrum_std = np.std(magnitude_spectrum)
            detection_details['spectrum_pattern'] = spectrum_std
            if spectrum_std < 2.5:  # Very regular pattern
                phone_indicators += 1
                detection_details['digital_pattern'] = True
            else:
                detection_details['digital_pattern'] = False
            
            # 7. Pixel grid detection - digital displays have visible pixel grids at close range
            # Check for repeating patterns that suggest pixel structure
            if min(h, w) > 64:  # Only for larger images
                # Look for regular patterns in small regions
                sample_region = gray[h//4:3*h//4, w//4:3*w//4]
                if sample_region.size > 0:
                    # Autocorrelation to find repeating patterns
                    autocorr = cv2.matchTemplate(sample_region, sample_region[:sample_region.shape[0]//2, :sample_region.shape[1]//2], cv2.TM_CCOEFF_NORMED)
                    max_corr = np.max(autocorr) if autocorr.size > 0 else 0
                    detection_details['pixel_grid_correlation'] = max_corr
                    if max_corr > 0.9:  # Very high correlation suggests pixel grid
                        phone_indicators += 1
                        detection_details['has_pixel_grid'] = True
                    else:
                        detection_details['has_pixel_grid'] = False
            
            # Final decision
            detection_details['total_indicators'] = phone_indicators
            detection_details['threshold'] = self.phone_score_threshold
            
            is_phone = phone_indicators >= self.phone_score_threshold
            confidence = min(1.0, phone_indicators / 7.0)  # Normalize to 0-1
            
            return is_phone, confidence, detection_details
            
        except Exception as e:
            print(f"Phone detection error: {e}")
            return False, 0.0, {"error": str(e)}
    
    def check_if_real(self, face_img):
        """
        Main anti-spoofing check combining model prediction and phone detection
        Returns: True if real face, False if spoofed/phone
        """
        if face_img is None or face_img.size == 0:
            return False
        
        # 1. Phone detection (immediate rejection if phone detected)
        is_phone, phone_confidence, phone_details = self.detect_phone_screen(face_img)
        
        if is_phone:
            print(f"[ANTI-SPOOF] Phone screen detected! Confidence: {phone_confidence:.2f}")
            print(f"[ANTI-SPOOF] Detection details: {phone_details}")
            return False
        
        # 2. Traditional anti-spoofing model prediction
        if self.model is not None:
            model_score = self.predict_with_model(face_img)
            # Use adaptive threshold based on phone detection confidence
            # If phone detection found some indicators but not enough, be more strict
            adaptive_threshold = 0.4 + (phone_confidence * 0.3)
            
            is_real = model_score >= adaptive_threshold
            
            if not is_real:
                print(f"[ANTI-SPOOF] Model rejected face! Score: {model_score:.3f}, Threshold: {adaptive_threshold:.3f}")
            
            return is_real
        else:
            # Fallback: only rely on phone detection if no model
            print("[ANTI-SPOOF] No model available, using phone detection only")
            return not is_phone
    
    def get_detailed_analysis(self, face_img):
        """
        Get detailed analysis of the face image for debugging
        Returns: Dictionary with all analysis results
        """
        if face_img is None or face_img.size == 0:
            return {"error": "Empty or invalid image"}
        
        analysis = {}
        
        # Phone detection analysis
        is_phone, phone_confidence, phone_details = self.detect_phone_screen(face_img)
        analysis['phone_detection'] = {
            'is_phone': is_phone,
            'confidence': phone_confidence,
            'details': phone_details
        }
        
        # Model prediction if available
        if self.model is not None:
            model_score = self.predict_with_model(face_img)
            analysis['model_prediction'] = {
                'score': model_score,
                'threshold_used': 0.4 + (phone_confidence * 0.3),
                'is_real': model_score >= (0.4 + (phone_confidence * 0.3))
            }
        else:
            analysis['model_prediction'] = {"error": "Model not available"}
        
        # Final decision
        analysis['final_decision'] = {
            'is_real': self.check_if_real(face_img),
            'primary_reason': 'phone_detected' if is_phone else 'model_prediction'
        }
        
        return analysis
    
    def get_model_info(self):
        """Return information about the anti-spoofing system"""
        return {
            'model_path': self.model_path,
            'model_loaded': self.model is not None,
            'input_size': self.input_size,
            'phone_detection_enabled': True,
            'phone_detection_threshold': self.phone_score_threshold
        }
