"""
Facial Attendance System
=======================

This package contains the source code for the Facial Attendance System,
a computer vision application that performs face detection, recognition,
anti-spoofing and attendance tracking.
"""

__version__ = '0.1.0'
__author__ = 'Facial Attendance System Team'

# Make key components available at the package level
from src.face_detector import FaceDetector
from src.face_recognizer import FaceRecognizer
from src.anti_spoof import AntiSpoofingDetector
from src.attendance_manager import AttendanceManager
from src.user_manager import UserManager

# Export public API
__all__ = [
    'FaceDetector',
    'FaceRecognizer', 
    'AntiSpoofingDetector',
    'AttendanceManager',
    'UserManager'
]