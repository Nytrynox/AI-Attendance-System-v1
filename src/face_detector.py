# src/face_detector.py

import dlib
import cv2
import numpy as np
import os

class FaceDetector:
    def __init__(self, predictor_path='models/shape_predictor_68_face_landmarks.dat'):
        if not os.path.exists(predictor_path):
            raise FileNotFoundError(f"Landmark predictor not found at {predictor_path}")
        
        # Use HOG face detector (replace with cnn_face_detector if GPU support and speed needed)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)

    def detect_faces(self, image):
        """
        Detect faces in the image.
        Returns a list of tuples: (x, y, w, h, face_crop, landmarks)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        results = []

        for rect in faces:
            x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()
            face_crop = image[y:y+h, x:x+w]
            shape = self.predictor(gray, rect)
            landmarks = [(pt.x, pt.y) for pt in shape.parts()]
            results.append((x, y, w, h, face_crop, landmarks))

        return results
