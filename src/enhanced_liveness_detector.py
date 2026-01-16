import cv2
import numpy as np
import dlib
from keras.models import load_model

class EnhancedLivenessDetector:
    def __init__(self, anti_spoof_model_path, phone_cascade_path=None):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')  # Download required
        self.anti_spoof_model = load_model(anti_spoof_model_path)
        self.phone_cascade = cv2.CascadeClassifier(phone_cascade_path) if phone_cascade_path else None

    def detect_eye_blink(self, landmarks):
        # Eye aspect ratio (EAR) for blink detection
        def eye_aspect_ratio(eye):
            A = np.linalg.norm(eye[1] - eye[5])
            B = np.linalg.norm(eye[2] - eye[4])
            C = np.linalg.norm(eye[0] - eye[3])
            return (A + B) / (2.0 * C)
        left_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)])
        right_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)])
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        return ear < 0.21  # Threshold for blink

    def detect_head_movement(self, prev_landmarks, curr_landmarks):
        # Simple head movement detection by comparing nose position
        prev_nose = np.array([prev_landmarks.part(30).x, prev_landmarks.part(30).y])
        curr_nose = np.array([curr_landmarks.part(30).x, curr_landmarks.part(30).y])
        movement = np.linalg.norm(curr_nose - prev_nose)
        return movement > 5  # Threshold for movement

    def detect_body_movement(self, prev_frame, curr_frame):
        # Use frame differencing for body movement
        diff = cv2.absdiff(prev_frame, curr_frame)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        movement = np.sum(thresh) / 255
        return movement > 5000  # Threshold for movement

    def detect_phone(self, frame):
        if self.phone_cascade is None:
            return False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        phones = self.phone_cascade.detectMultiScale(gray, 1.3, 5)
        return len(phones) > 0

    def detect_anti_spoof(self, face_img):
        # Preprocess face_img as required by your model
        img = cv2.resize(face_img, (160, 160))
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)
        pred = self.anti_spoof_model.predict(img)
        return pred[0][0] < 0.5  # 0: real, 1: spoof (adjust threshold as needed)

    def is_live(self, frame, prev_frame=None, prev_landmarks=None):
        faces = self.detector(frame)
        if len(faces) == 0:
            return False, 'No face detected'
        for face in faces:
            landmarks = self.predictor(frame, face)
            # Eye blink
            blinked = self.detect_eye_blink(landmarks)
            # Head movement
            head_moved = False
            if prev_landmarks is not None:
                head_moved = self.detect_head_movement(prev_landmarks, landmarks)
            # Body movement
            body_moved = False
            if prev_frame is not None:
                body_moved = self.detect_body_movement(prev_frame, frame)
            # Phone detection
            phone_present = self.detect_phone(frame)
            # Anti-spoof
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            face_img = frame[y:y+h, x:x+w]
            is_real = self.detect_anti_spoof(face_img)
            if phone_present:
                return False, 'Phone detected (spoof)'
            if not is_real:
                return False, 'Spoof detected'
            if not (blinked and (head_moved or body_moved)):
                return False, 'Liveness cues not detected'
            return True, 'Live human detected'
        return False, 'No valid face found'

# Example usage:
# detector = EnhancedLivenessDetector('models/anti_spoof_model.h5', 'models/phone_cascade.xml')
# live, reason = detector.is_live(frame, prev_frame, prev_landmarks)
# print(live, reason)
