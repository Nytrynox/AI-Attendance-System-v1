# src/anti_spoof.py

import numpy as np
import cv2
try:
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except ImportError:
    try:
        from keras.models import load_model
        TENSORFLOW_AVAILABLE = True
    except ImportError:
        TENSORFLOW_AVAILABLE = False
        print("Warning: TensorFlow/Keras not available. Using basic anti-spoofing.")
import os

class AntiSpoofingDetector:
    def __init__(self, model_path='models/anti_spoof_model.h5'):
        self.model_path = model_path
        self.model = None
        self.input_size = (160, 160)  # Assumed input size for anti-spoof model
        
        if TENSORFLOW_AVAILABLE and os.path.exists(model_path):
            try:
                self.model = load_model(model_path)
                print(f"Anti-spoofing model loaded from {model_path}")
            except Exception as e:
                print(f"Failed to load anti-spoofing model: {e}")
                self.model = None
        else:
            print("Using basic anti-spoofing detection (no ML model)")

    def preprocess(self, face_img):
        """
        Preprocess the face image for anti-spoofing prediction.
        Resize, normalize and expand dims.
        """
        resized_face = cv2.resize(face_img, self.input_size)
        normalized_face = resized_face / 255.0  # Normalize to [0, 1]
        input_tensor = np.expand_dims(normalized_face, axis=0)
        return input_tensor

    def predict(self, face_img, debug=False, threshold=None):
        """
        Predict whether the given face image is real or spoofed.
        Returns: True (Real), False (Spoof)
        Args:
            face_img: Input face image
            debug: Whether to print debug information
            threshold: Custom threshold for spoof detection (default: 0.7 for aggressive, 0.3-0.4 for lenient)
        """
        if self.model is not None:
            processed_img = self.preprocess(face_img)
            prediction = self.model.predict(processed_img)[0][0]
            if debug:
                print(f"[AntiSpoof] Prediction value: {prediction}")
            
            # Use provided threshold or default aggressive threshold
            spoof_threshold = threshold if threshold is not None else 0.7
            return prediction >= spoof_threshold, prediction  # True = Real, False = Fake
        else:
            # Basic anti-spoofing without ML model
            return self._basic_anti_spoof_check(face_img, debug), 0.8  # Assume real for basic check

    def _basic_anti_spoof_check(self, face_img, debug=False):
        """
        Basic anti-spoofing check using computer vision techniques
        """
        try:
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Check image quality metrics
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Very blurry images might indicate a photo/screen
            if laplacian_var < 50:
                if debug:
                    print(f"[BasicAntiSpoof] Image too blurry: {laplacian_var}")
                return False
                
            # Check for basic patterns that might indicate a screen
            # This is a very basic check - real ML models would be much more sophisticated
            
            if debug:
                print(f"[BasicAntiSpoof] Sharpness score: {laplacian_var}")
                
            return True  # Default to assuming real face
            
        except Exception as e:
            if debug:
                print(f"[BasicAntiSpoof] Error: {e}")
            return True  # Default to assuming real face

    def check_if_real(self, face_img, debug=False, threshold=None):
        """Check if face is real using specified threshold"""
        is_real, prediction = self.predict(face_img, debug=debug, threshold=threshold)
        return is_real
    
    def is_real_face(self, face_img, debug=False):
        """Main method used by the application - check if face is real"""
        return self.check_if_real(face_img, debug=debug, threshold=0.5)
    
    def check_if_real_lenient(self, face_img, debug=False):
        """Check if face is real using lenient threshold for registration"""
        return self.check_if_real(face_img, debug=debug, threshold=0.3)
    
    def check_if_real_aggressive(self, face_img, debug=False):
        """Check if face is real using aggressive threshold for attendance"""
        return self.check_if_real(face_img, debug=debug, threshold=0.7)
    
    def get_model_info(self):
        """Return information about the anti-spoofing model."""
        return {
            'model_path': self.model_path,
            'input_size': self.input_size,
            'model_loaded': self.model is not None
        }
