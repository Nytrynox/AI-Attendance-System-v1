# Fix for Anti-Spoofing in Registration

# The main fix for the spoof detection issue is to use lenient thresholds during registration.
# Here's a summary of the changes made:

"""
ANTI-SPOOFING FIXES FOR REGISTRATION:

1. Modified src/anti_spoof.py:
   - Added threshold parameter to predict() method
   - Added convenience methods for lenient and aggressive thresholds
   - Lenient threshold: 0.3 (for registration)
   - Aggressive threshold: 0.7 (for attendance)

2. Created src/advanced_liveness_detector.py:
   - Dedicated detector with registration-optimized settings
   - Lenient anti-spoof threshold: 0.3
   - Lenient phone detection threshold: 0.8
   - Reduced blink requirements: 2 (vs 3 for attendance)
   - Reduced head movement requirements: 1 (vs 2 for attendance)

3. Updated registration window:
   - Uses AdvancedLivenessDetector with for_registration=True
   - Final capture uses threshold=0.3 for anti-spoof check
   - Better error messages explaining lenient mode

KEY CHANGES TO PREVENT FALSE POSITIVES ON REAL FACES:

A. Anti-Spoof Model Threshold:
   - Registration: 0.3 (lenient)
   - Attendance: 0.7 (strict)

B. Phone Detection Threshold:
   - Registration: 0.8 (lenient) 
   - Attendance: 0.6 (strict)

C. Liveness Requirements:
   - Registration: 2 blinks, 1 head movement
   - Attendance: 3 blinks, 2 head movements

This prevents real live faces from being incorrectly flagged as spoofs during registration
while maintaining security during attendance checking.
"""

# Usage in registration:
def example_registration_usage():
    from src.advanced_liveness_detector import AdvancedLivenessDetector
    
    # Create detector optimized for registration (lenient)
    detector = AdvancedLivenessDetector(for_registration=True)
    
    # Use in registration flow
    # ... detect faces, get face_crop ...
    
    # Check with lenient threshold
    results = detector.process_frame_for_liveness(frame, face_bounds)
    
    if results['all_passed']:
        print("Liveness verified - safe to register user")
    else:
        print(f"Liveness progress: {results['progress']}%")
        for msg in results['messages']:
            print(f"Status: {msg}")

# Usage in attendance:
def example_attendance_usage():
    from src.advanced_liveness_detector import AdvancedLivenessDetector
    
    # Create detector optimized for attendance (strict)
    detector = AdvancedLivenessDetector(for_registration=False)
    
    # Use in attendance flow with strict security
    # ... similar to above but with stricter thresholds ...

print("Anti-spoofing fixes applied!")
print("Registration now uses lenient thresholds to avoid false positives on real faces.")
print("Run the registration system to test the improvements.")
