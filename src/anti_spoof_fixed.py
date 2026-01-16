# src/anti_spoof.py

import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model
import os

class AntiSpoofingDetector:
    def __init__(self, model_path='models/anti_spoof_model.h5'):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Anti-spoofing model not found at {model_path}")
        self.model_path = model_path
        self.model = load_model(model_path)
        self.input_size = (160, 160)  # Assumed input size for anti-spoof model

    def preprocess(self, face_img):
        """
        Preprocess the face image for anti-spoofing prediction.
        Resize, normalize and expand dims.
        """
        resized_face = cv2.resize(face_img, self.input_size)
        normalized_face = resized_face / 255.0  # Normalize to [0, 1]
        input_tensor = np.expand_dims(normalized_face, axis=0)
        return input_tensor

    def predict(self, face_img):
        """
        Predict whether the given face image is real or spoofed.
        Returns: True (Real), False (Spoof)
        """
        processed_img = self.preprocess(face_img)
        prediction = self.model.predict(processed_img)[0][0]
        
        # Lower threshold to be less aggressive (reduced from 0.5 to 0.25)
        # This makes the system more tolerant and reduces false positives
        return prediction >= 0.25  # True = Real, False = Fake
    
    def check_if_real(self, face_img):
        """Alias for predict method for backward compatibility."""
        return self.predict(face_img)
    
    def get_model_info(self):
        """Return information about the anti-spoofing model."""
        return {
            'model_path': self.model_path,
            'input_size': self.input_size,
            'model_loaded': self.model is not None
        }
