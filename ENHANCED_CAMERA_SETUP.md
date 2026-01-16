# Enhanced Camera Setup Guide
# Face Attendance System with Mobile Camera Support

## Overview
This enhanced version of the Face Attendance System supports both laptop cameras and mobile cameras through DroidCam, giving you flexibility in camera selection and positioning.

## Features
- **Laptop Camera Support**: Use any connected webcam or built-in camera
- **Mobile Camera Support**: Use your smartphone as a high-quality camera via DroidCam
- **Camera Selection Interface**: Easy-to-use interface for choosing camera sources
- **Auto-detection**: Automatically detect available cameras and DroidCam devices
- **Network Scanning**: Scan your local network for DroidCam devices
- **Real-time Processing**: Face detection, recognition, and anti-spoofing
- **Attendance Tracking**: Automatic attendance marking with timestamp logging

## Quick Start

### 1. Launch the Enhanced System
```bash
python launch_enhanced_camera_system.py
```

### 2. Alternative Launch Methods
```bash
# Using main.py with enhanced camera flag
python main.py --enhanced-camera

# Direct GUI launch
python -m src.gui.main_window_enhanced_camera
```

## Camera Setup Instructions

### Laptop Camera Setup
1. Connect your webcam or ensure built-in camera is working
2. Launch the system and click "Select Camera"
3. Choose the "Laptop Camera" tab
4. Select from detected cameras
5. Click "Test Selected Camera" to preview
6. Click "Use This Camera" to proceed

### Mobile Camera Setup (DroidCam)

#### Step 1: Install DroidCam on Your Phone
- **Android**: Download "DroidCam" from Google Play Store
- **iOS**: Download "DroidCam" from App Store

#### Step 2: Connect to Same Network
- Ensure your phone and computer are on the same WiFi network

#### Step 3: Configure DroidCam
1. Open DroidCam app on your phone
2. Note the IP address displayed in the app (e.g., 192.168.1.100)
3. Launch the attendance system
4. Click "Select Camera" → "Mobile Camera" tab
5. Enter the IP address from your phone
6. Click "Test Connection"
7. Click "Test Selected Camera" to preview
8. Click "Use This Camera" to proceed

#### Step 4: Auto-Detection (Optional)
- Click "Auto-detect DroidCam" to scan your network automatically

## System Requirements

### Software Dependencies
```bash
pip install opencv-python pillow numpy requests dlib face-recognition
```

### Model Files Required
Place these files in the `models/` directory:
- `shape_predictor_68_face_landmarks.dat`
- `anti_spoof_model.h5` (optional, for enhanced security)
- `face_recognition_model.h5` (optional, for custom recognition)

## Usage Modes

### Preview Mode
- Live camera feed with basic face detection
- No attendance tracking
- Good for testing camera positioning and quality

### Attendance Mode
- Full face recognition and anti-spoofing
- Automatic attendance marking
- Real-time user identification

## Troubleshooting

### Camera Issues
- **No cameras detected**: Check camera connections and drivers
- **Camera won't start**: Try different camera indices (0, 1, 2, etc.)
- **Poor quality**: Adjust lighting and camera positioning

### DroidCam Issues
- **Connection failed**: Check WiFi network and IP address
- **No video feed**: Restart DroidCam app and try again
- **Slow performance**: Ensure good WiFi signal strength

### Network Issues
- **Can't find DroidCam**: Manual IP entry may be needed
- **Connection timeout**: Check firewall settings
- **Intermittent connection**: Use laptop camera as backup

## Advanced Configuration

### Custom Camera URLs
For other IP camera sources, use the mobile camera option with custom URLs:
- Generic IP camera: `http://192.168.1.100:8080/video`
- Custom streaming URL: `rtsp://192.168.1.100:554/stream`

### Performance Optimization
- Close unnecessary applications
- Use ethernet connection for stability
- Position cameras at eye level for best recognition
- Ensure good lighting conditions

## File Structure
```
face-attendance-system/
├── launch_enhanced_camera_system.py    # Main launcher
├── main.py                            # Alternative launcher
├── src/
│   ├── gui/
│   │   ├── camera_selection_window.py    # Camera selection interface
│   │   └── main_window_enhanced_camera.py # Main application window
│   └── utils/
│       └── camera_utils.py              # Enhanced camera utilities
├── data/
│   ├── attendance/                      # Attendance records
│   ├── registered_users/               # User profiles
│   └── logs/                           # System logs
└── models/                             # AI model files
```

## Tips for Best Results

### Camera Positioning
- Position camera at eye level
- Ensure face is well-lit
- Avoid backlighting
- Keep stable distance (2-4 feet)

### Mobile Camera Advantages
- Higher resolution than most laptop cameras
- Better positioning flexibility
- Superior low-light performance
- Can be mounted or handheld

### Network Setup
- Use 5GHz WiFi for better performance
- Keep phone and computer close to router
- Restart router if connection issues persist

## Support and Maintenance

### Log Files
Check `data/logs/` for system logs and error information.

### User Registration
- Use "Register New User" button in the main interface
- Ensure good lighting during registration
- Capture multiple angles for better recognition

### Data Backup
- Regularly backup `data/registered_users/` directory
- Export attendance records from `data/attendance/`

## Security Features
- Anti-spoofing detection to prevent photo/video attacks
- Real-time liveness detection
- Secure user data storage
- Attendance logging with timestamps

## Compatibility
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+)
- Python 3.7+
- OpenCV 4.5+

For additional support, check the system logs or contact the development team.
