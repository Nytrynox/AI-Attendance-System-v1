# Enhanced Liveness Detection - User Registration

## 🔒 Advanced Security Features

The enhanced user registration system now includes comprehensive liveness detection to prevent spoofing attacks and ensure only real, live users can register.

## 🛡️ Security Features

### 1. Eye Blink Detection
- **Purpose**: Verifies the user is a living person, not a photo or video
- **How it works**: Detects natural eye blinking patterns
- **Requirement**: User must blink 3 times naturally during registration
- **Detection method**: Eye Aspect Ratio (EAR) analysis using facial landmarks

### 2. Head Movement Verification
- **Purpose**: Confirms 3D presence and prevents 2D photo attacks
- **How it works**: Tracks head pose changes and movement
- **Requirement**: User must move their head left/right or up/down
- **Detection method**: Head pose estimation using facial landmark geometry

### 3. Phone Screen Detection
- **Purpose**: Prevents registration using phone/tablet screens showing photos
- **How it works**: Analyzes texture patterns and color distribution
- **Detection criteria**:
  - Texture uniformity (screens have different texture patterns)
  - Color distribution analysis
  - Artificial sharpness detection
- **Result**: Displays "📱 PHONE DETECTED - SPOOFING!" in red when phone is detected

### 4. Anti-Spoofing Detection
- **Purpose**: General spoofing attempt detection
- **How it works**: Uses trained machine learning model
- **Model**: `models/anti_spoof_model.h5`
- **Detection**: Analyzes facial features for authenticity

## 🎯 How to Use

### For Users:
1. **Start Camera**: Click "🎥 Start Camera" button
2. **Begin Liveness Test**: Click "🔒 Start Liveness Test" 
3. **Follow Instructions**:
   - 👁️ **Blink naturally** (3 times required)
   - 🔄 **Move your head** left/right or up/down
   - 📱 **Ensure no phone screen** is being used
4. **Complete Registration**: Once all tests pass, capture and save your face

### Visual Indicators:
- 🟢 **Green Box**: Real face detected, all security checks passed
- 🔴 **Red Box**: Spoofing or phone detected
- 🔵 **Blue Box**: Liveness test in progress
- 🟡 **Yellow Box**: Processing/analyzing

## 🚀 Running the Enhanced Registration

### Method 1: Through Main Application
```bash
python launch_complete_system.py
```
Then click "Register New User" button.

### Method 2: Direct Testing
```bash
python test_liveness_registration.py
```

### Method 3: Standalone
```bash
python -c "from src.gui.add_user_window_liveness_enhanced import launch_liveness_enhanced_window; import tkinter as tk; root = tk.Tk(); launch_liveness_enhanced_window(); root.mainloop()"
```

## 📋 System Requirements

### Required Files:
- `models/anti_spoof_model.h5` - Anti-spoofing ML model
- `models/shape_predictor_68_face_landmarks.dat` - Facial landmarks (optional for enhanced detection)

### Dependencies:
- OpenCV (`cv2`)
- NumPy
- PIL (Pillow)
- tkinter
- dlib (optional for advanced landmark detection)

## 🔧 Technical Implementation

### Liveness Detection Pipeline:
1. **Face Detection**: Locate face in camera frame
2. **Anti-spoofing Check**: Verify face authenticity
3. **Phone Detection**: Check for screen artifacts
4. **Liveness Tests**:
   - Eye blink pattern analysis
   - Head movement tracking
   - Texture authenticity verification
5. **Final Verification**: All checks must pass before registration

### Security Levels:
- **Basic Mode**: Time-based completion (when landmarks unavailable)
- **Enhanced Mode**: Full landmark-based detection
- **Advanced Mode**: Complete texture and movement analysis

## 🛠️ Configuration

### Adjustable Parameters:
```python
# In LivenessEnhancedAddUserWindow class
self.required_blinks = 3              # Number of blinks required
self.detection_threshold = 30          # Frame count for detection
self.phone_detection_threshold = 0.7   # Phone detection sensitivity
```

### Phone Detection Sensitivity:
- **Low (0.5)**: More lenient, may miss some phones
- **Medium (0.7)**: Balanced detection (recommended)
- **High (0.9)**: Strict detection, may flag some real faces

## 🚨 Security Alerts

The system will show red alerts for:
- **"📱 PHONE DETECTED - SPOOFING!"**: Phone or tablet screen detected
- **"🚫 SPOOFING DETECTED!"**: General spoofing attempt
- **"Security Alert"**: Final verification failed

## 📈 Success Indicators

Registration is successful when all these are completed:
- ✅ Eye Blink Test: Passed
- ✅ Head Movement: Passed  
- ✅ Phone Detection: No phone detected
- ✅ Face captured with all security checks

## 🔍 Troubleshooting

### Common Issues:

1. **"No face detected"**
   - Ensure good lighting
   - Position face clearly in camera view
   - Remove glasses or reflective objects

2. **"Liveness test not starting"**
   - Start camera first
   - Click "Start Liveness Test" button
   - Ensure camera permissions are granted

3. **"Phone detected" false positive**
   - Ensure natural lighting (avoid artificial screen lighting)
   - Remove reflective backgrounds
   - Adjust phone detection sensitivity

4. **Blink detection not working**
   - Blink naturally and clearly
   - Ensure eyes are clearly visible
   - Good lighting on face

## 📊 Security Benefits

✅ **Prevents Photo Attacks**: Static photos cannot pass liveness tests
✅ **Blocks Video Replays**: Movement patterns distinguish live vs recorded
✅ **Detects Phone Spoofing**: Texture analysis identifies screen displays  
✅ **Multi-layer Security**: Multiple independent verification methods
✅ **Real-time Processing**: Immediate feedback during registration
✅ **User-friendly**: Clear visual guidance and progress indicators

This enhanced system provides enterprise-level security for facial recognition registration while maintaining ease of use.
