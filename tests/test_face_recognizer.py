import unittest
import os
import numpy as np
import cv2
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from src.face_recognizer import FaceRecognizer
from src.face_detector import FaceDetector


class TestFaceRecognizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test resources that can be shared across tests."""
        # Create a mock face detector to use in the recognizer
        cls.mock_detector = MagicMock(spec=FaceDetector)
        
        # Path to the model file
        cls.model_path = os.path.join('models', 'face_recognition_model.h5')

        # Create test database directory if it doesn't exist
        cls.test_db_path = os.path.join('data', 'test_registered_users')
        os.makedirs(cls.test_db_path, exist_ok=True)
        
        # Sample face embedding for testing
        cls.sample_embedding = np.random.rand(128).astype(np.float32)
    
    def setUp(self):
        """Set up resources before each test."""
        # Initialize the face recognizer with mock detector
        with patch('src.face_recognizer.FaceDetector', return_value=self.mock_detector):
            self.recognizer = FaceRecognizer(model_path=self.model_path, 
                                            database_path=self.test_db_path)
        
        # Set up the mock detector to return a face for detection
        self.mock_detector.detect_faces.return_value = [(0, 0, 100, 100)]  # Mock face bounding box
    
    def test_init(self):
        """Test the initialization of FaceRecognizer."""
        self.assertIsNotNone(self.recognizer)
        self.assertEqual(self.recognizer.database_path, self.test_db_path)
    
    @patch('src.face_recognizer.FaceRecognizer._load_model')
    def test_load_model(self, mock_load_model):
        """Test model loading functionality."""
        # Create a new recognizer to trigger model loading
        recognizer = FaceRecognizer(model_path=self.model_path,
                                   database_path=self.test_db_path)
        mock_load_model.assert_called_once()
    
    @patch('os.listdir')
    @patch('numpy.load')
    def test_load_database(self, mock_np_load, mock_listdir):
        """Test database loading functionality."""
        # Setup mock data
        mock_listdir.return_value = ['user1.npy', 'user2.npy']
        mock_np_load.return_value = self.sample_embedding
        
        # Call load database
        self.recognizer.load_database()
        
        # Verify calls and database state
        self.assertEqual(mock_listdir.call_count, 1)
        self.assertEqual(mock_np_load.call_count, 2)
        self.assertEqual(len(self.recognizer.database), 2)
        self.assertIn('user1', self.recognizer.database)
        self.assertIn('user2', self.recognizer.database)
    
    @patch('numpy.save')
    def test_register_face(self, mock_np_save):
        """Test face registration functionality."""
        # Mock the extract_face_embedding method
        with patch.object(self.recognizer, 'extract_face_embedding', 
                         return_value=self.sample_embedding):
            # Create a dummy image
            test_image = np.zeros((300, 300, 3), dtype=np.uint8)
            
            # Register a new face
            result = self.recognizer.register_face(test_image, "test_user")
            
            # Assertions
            self.assertTrue(result)
            mock_np_save.assert_called_once()
            self.assertIn("test_user", self.recognizer.database)
    
    @patch('cv2.resize')
    @patch('numpy.expand_dims')
    def test_extract_face_embedding(self, mock_expand_dims, mock_resize):
        """Test face embedding extraction."""
        # Set up mocks
        mock_resize.return_value = np.zeros((160, 160, 3))
        mock_expand_dims.return_value = np.zeros((1, 160, 160, 3))
        
        # Mock the model prediction
        self.recognizer.model = MagicMock()
        self.recognizer.model.predict.return_value = np.array([self.sample_embedding])
        
        # Create a dummy image
        test_image = np.zeros((300, 300, 3), dtype=np.uint8)
        
        # Extract embedding
        embedding = self.recognizer.extract_face_embedding(test_image)
        
        # Assertions
        self.recognizer.model.predict.assert_called_once()
        self.assertEqual(embedding.shape, self.sample_embedding.shape)
    
    def test_recognize_face(self):
        """Test face recognition functionality."""
        # Create a mock database
        self.recognizer.database = {
            'user1': self.sample_embedding,
            'user2': np.random.rand(128).astype(np.float32)
        }
        
        # Mock the extract_face_embedding method to return embedding similar to user1
        with patch.object(self.recognizer, 'extract_face_embedding', 
                         return_value=self.sample_embedding + 0.01):  # Similar to user1
                         
            # Create a dummy image
            test_image = np.zeros((300, 300, 3), dtype=np.uint8)
            
            # Recognize face
            user_id, confidence = self.recognizer.recognize_face(test_image)
            
            # Assertions
            self.assertEqual(user_id, 'user1')
            self.assertGreater(confidence, 0.5)  # Assuming threshold is 0.5
    
    def test_recognize_unknown_face(self):
        """Test recognition of unknown face."""
        # Create a mock database
        self.recognizer.database = {
            'user1': np.ones(128, dtype=np.float32),  # Very different from test embedding
            'user2': np.ones(128, dtype=np.float32) * 2
        }
        
        # Mock the extract_face_embedding method
        with patch.object(self.recognizer, 'extract_face_embedding', 
                         return_value=np.zeros(128, dtype=np.float32)):  # Different from both users
                         
            # Create a dummy image
            test_image = np.zeros((300, 300, 3), dtype=np.uint8)
            
            # Recognize face - should not match any known face
            user_id, confidence = self.recognizer.recognize_face(test_image)
            
            # Assertions
            self.assertEqual(user_id, "Unknown")
            self.assertLess(confidence, 0.5)  # Assuming threshold is 0.5
    
    def test_calculate_similarity(self):
        """Test similarity calculation between face embeddings."""
        # Create two embeddings with known similarity
        emb1 = np.ones(128, dtype=np.float32)
        emb2 = np.ones(128, dtype=np.float32) * 0.9
        
        # Calculate similarity - for normalized vectors, this should be close to 0.9
        similarity = self.recognizer.calculate_similarity(emb1, emb2)
        
        # Assertions
        self.assertAlmostEqual(similarity, 0.9, places=1)
    
    def test_no_face_detected(self):
        """Test behavior when no face is detected."""
        # Update mock detector to return no faces
        self.mock_detector.detect_faces.return_value = []
        
        # Create a dummy image
        test_image = np.zeros((300, 300, 3), dtype=np.uint8)
        
        # Attempt recognition with no faces
        with self.assertRaises(ValueError):
            self.recognizer.recognize_face(test_image)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests have run."""
        # Remove test database directory if it exists
        import shutil
        if os.path.exists(cls.test_db_path):
            shutil.rmtree(cls.test_db_path)


if __name__ == '__main__':
    unittest.main()