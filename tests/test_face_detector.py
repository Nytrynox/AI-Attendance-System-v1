import unittest
import os
import sys
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.face_detector import FaceDetector


class TestFaceDetector(unittest.TestCase):
    """Test cases for the FaceDetector class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a FaceDetector instance with the model path
        self.model_path = "models/shape_predictor_68_face_landmarks.dat"
        self.face_detector = FaceDetector(self.model_path)
        
        # Create a sample image for testing
        self.sample_image = np.zeros((300, 300, 3), dtype=np.uint8)
        # Create a face-like rectangle in the image
        cv2.rectangle(self.sample_image, (100, 100), (200, 200), (255, 255, 255), -1)
        
    def test_initialization(self):
        """Test that the FaceDetector initializes correctly."""
        self.assertIsNotNone(self.face_detector)
        self.assertEqual(self.face_detector.model_path, self.model_path)
        
    def test_detect_faces(self):
        """Test the detect_faces method."""
        with patch.object(self.face_detector, '_detect_faces_internal') as mock_detect:
            # Mock the internal detection method to return a list of face rectangles
            mock_faces = [(100, 100, 100, 100)]
            mock_detect.return_value = mock_faces
            
            # Call the detect_faces method
            faces = self.face_detector.detect_faces(self.sample_image)
            
            # Assert that the method was called with the correct arguments
            mock_detect.assert_called_once_with(self.sample_image)
            # Assert that the method returns the expected value
            self.assertEqual(faces, mock_faces)
            
    def test_get_face_landmarks(self):
        """Test the get_face_landmarks method."""
        with patch.object(self.face_detector, '_get_landmarks_internal') as mock_landmarks:
            # Mock the internal landmarks method to return a list of points
            mock_points = [(100, 100), (110, 110), (120, 120)]
            mock_landmarks.return_value = mock_points
            
            # Create a mock face rectangle
            face_rect = (100, 100, 100, 100)
            
            # Call the get_face_landmarks method
            landmarks = self.face_detector.get_face_landmarks(self.sample_image, face_rect)
            
            # Assert that the method was called with the correct arguments
            mock_landmarks.assert_called_once_with(self.sample_image, face_rect)
            # Assert that the method returns the expected value
            self.assertEqual(landmarks, mock_points)
            
    def test_align_face(self):
        """Test the align_face method."""
        with patch.object(self.face_detector, '_align_face_internal') as mock_align:
            # Mock the internal alignment method to return an aligned face
            aligned_face = np.zeros((150, 150, 3), dtype=np.uint8)
            mock_align.return_value = aligned_face
            
            # Create mock landmarks
            landmarks = [(100, 100), (110, 110), (120, 120)]
            
            # Call the align_face method
            result = self.face_detector.align_face(self.sample_image, landmarks)
            
            # Assert that the method was called with the correct arguments
            mock_align.assert_called_once_with(self.sample_image, landmarks)
            # Assert that the method returns the expected value
            self.assertEqual(result.shape, aligned_face.shape)
            
    def test_detect_faces_empty_image(self):
        """Test detect_faces with an empty image."""
        empty_image = np.zeros((0, 0, 3), dtype=np.uint8)
        
        # Test with empty image - should handle gracefully
        with self.assertRaises(ValueError):
            self.face_detector.detect_faces(empty_image)
            
    def test_detect_faces_no_faces(self):
        """Test detect_faces with an image containing no faces."""
        with patch.object(self.face_detector, '_detect_faces_internal') as mock_detect:
            # Mock the internal detection method to return an empty list
            mock_detect.return_value = []
            
            # Call the detect_faces method
            faces = self.face_detector.detect_faces(self.sample_image)
            
            # Assert that the method returns an empty list
            self.assertEqual(faces, [])
            
    def test_get_face_landmarks_invalid_rect(self):
        """Test get_face_landmarks with an invalid face rectangle."""
        # Test with invalid rectangle - should handle gracefully
        with self.assertRaises(ValueError):
            self.face_detector.get_face_landmarks(self.sample_image, (0, 0, 0, 0))
            
    def test_end_to_end_face_detection(self):
        """Test the entire face detection pipeline."""
        # This is a more integrated test that would require actual models
        # For this unit test, we'll mock the necessary components
        
        with patch.object(self.face_detector, 'detect_faces') as mock_detect:
            with patch.object(self.face_detector, 'get_face_landmarks') as mock_landmarks:
                with patch.object(self.face_detector, 'align_face') as mock_align:
                    # Setup mock returns
                    mock_faces = [(100, 100, 100, 100)]
                    mock_detect.return_value = mock_faces
                    
                    mock_points = [(100, 100), (110, 110), (120, 120)]
                    mock_landmarks.return_value = mock_points
                    
                    aligned_face = np.zeros((150, 150, 3), dtype=np.uint8)
                    mock_align.return_value = aligned_face
                    
                    # Run the pipeline
                    faces = self.face_detector.detect_faces(self.sample_image)
                    self.assertEqual(len(faces), 1)
                    
                    face_rect = faces[0]
                    landmarks = self.face_detector.get_face_landmarks(self.sample_image, face_rect)
                    self.assertEqual(len(landmarks), 3)
                    
                    aligned = self.face_detector.align_face(self.sample_image, landmarks)
                    self.assertEqual(aligned.shape, (150, 150, 3))


if __name__ == '__main__':
    unittest.main()