"""
Utilities for the Facial Attendance System
========================================

This package contains utility functions and helper classes
used throughout the Facial Attendance System.
"""

from src.utils.image_utils import (
    load_image, 
    save_image, 
    resize_image, 
    crop_face,
    convert_to_rgb,
    preprocess_for_face_recognition,
    show_image,
    setup_camera
)

from src.utils.data_utils import (
    load_registered_users,
    save_attendance,
    has_marked_attendance,
    ensure_directories,
    get_datetime_string
)

# Export public API
__all__ = [
    # Image utilities
    'load_image',
    'save_image', 
    'resize_image',
    'crop_face',
    'convert_to_rgb',
    'preprocess_for_face_recognition',
    'show_image',
    'setup_camera',
    
    # Data utilities
    'load_registered_users',
    'save_attendance',
    'has_marked_attendance',
    'ensure_directories',
    'get_datetime_string'
]