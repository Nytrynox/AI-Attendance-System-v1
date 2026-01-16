import unittest
import os
import sys
import numpy as np
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to allow importing project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.anti_spoof import AntiSpoofingDetector


class TestAntiSpoofingDetector(unittest.TestCase):
    """Unit tests for the AntiSpoofingDetector class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Mock the model loading to avoid actual file dependencies during testing
        with patch('src.anti_spoof.load_model') as mock_load:
            self.mock_model = MagicMock()
            mock_load.return_value = self.mock_model
            self.spoof_detector = AntiSpoofingDetector()
    
    def test_initialization(self):
        """Test the initialization of the AntiSpoofingDetector"""
        self.assertIsNotNone(self.spoof_detector)
        self.assertIsNotNone(self.spoof_detector.model)
        self.assertEqual(self.spoof_detector.model, self.mock_model)
    
    def test_preprocess_image(self):
        """Test image preprocessing function"""
        # Create a fake image
        fake_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Process the image
        processed = self.spoof_detector.preprocess_image(fake_image)
        
        # Check if the preprocessing returns the expected shape based on the model input requirements
        self.assertEqual(processed.shape[-1], 3)  # Should have 3 channels
        self.assertEqual(len(processed.shape), 4)  # Should be 4D tensor (batch, height, width, channels)
        
    def test_predict_real_face_high_confidence(self):
        """Test prediction with a simulated real face (high confidence)"""
        # Mock the model prediction to return high confidence for real face
        self.mock_model.predict.return_value = np.array([[0.05, 0.95]])  # [fake_prob, real_prob]
        
        fake_face_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test the prediction
        is_real, confidence = self.spoof_detector.check_if_real(fake_face_img)
        
        self.assertTrue(is_real)
        self.assertAlmostEqual(confidence, 0.95)
        
    def test_predict_fake_face_high_confidence(self):
        """Test prediction with a simulated fake face (high confidence)"""
        # Mock the model prediction to return high confidence for fake face
        self.mock_model.predict.return_value = np.array([[0.92, 0.08]])  # [fake_prob, real_prob]
        
        fake_face_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test the prediction
        is_real, confidence = self.spoof_detector.check_if_real(fake_face_img)
        
        self.assertFalse(is_real)
        self.assertAlmostEqual(confidence, 0.92)
    
    def test_predict_uncertain_case(self):
        """Test prediction with ambiguous confidence values"""
        # Mock the model prediction to return uncertain confidence
        self.mock_model.predict.return_value = np.array([[0.48, 0.52]])  # [fake_prob, real_prob]
        
        fake_face_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test the prediction
        is_real, confidence = self.spoof_detector.check_if_real(fake_face_img)
        
        # Should be real but with low confidence
        self.assertTrue(is_real)
        self.assertAlmostEqual(confidence, 0.52)
    
    def test_batch_prediction(self):
        """Test batch prediction functionality if implemented"""
        # Create a batch of fake images
        batch_size = 3
        fake_images = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(batch_size)]
        
        # Mock the model prediction to return different values for each image
        self.mock_model.predict.return_value = np.array([
            [0.95, 0.05],  # Fake
            [0.10, 0.90],  # Real
            [0.60, 0.40]   # Fake (lower confidence)
        ])
        
        # Assuming the implementation supports batch prediction
        try:
            results = self.spoof_detector.check_batch(fake_images)
            
            # Verify the results
            self.assertEqual(len(results), batch_size)
            
            # First image should be fake with high confidence
            self.assertFalse(results[0][0])
            self.assertAlmostEqual(results[0][1], 0.95)
            
            # Second image should be real with high confidence
            self.assertTrue(results[1][0])
            self.assertAlmostEqual(results[1][1], 0.90)
            
            # Third image should be fake with medium confidence
            self.assertFalse(results[2][0])
            self.assertAlmostEqual(results[2][1], 0.60)
            
        except (NotImplementedError, AttributeError):
            # If batch prediction is not implemented, this test should be skipped
            pass
    
    def test_threshold_configuration(self):
        """Test configuring different thresholds for real/fake classification"""
        # Create a fake image
        fake_face_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Mock a borderline prediction
        self.mock_model.predict.return_value = np.array([[0.55, 0.45]])  # [fake_prob, real_prob]
        
        # Test with default threshold (assuming 0.5)
        is_real, _ = self.spoof_detector.check_if_real(fake_face_img)
        self.assertFalse(is_real)  # Should be classified as fake
        
        # Change the threshold to 0.6 and test again
        self.spoof_detector.threshold = 0.6
        is_real, _ = self.spoof_detector.check_if_real(fake_face_img)
        self.assertTrue(is_real)  # Now should be classified as real since fake prob < new threshold
    
    def tearDown(self):
        """Clean up after each test method"""
        pass


if __name__ == '__main__':
    unittest.main()