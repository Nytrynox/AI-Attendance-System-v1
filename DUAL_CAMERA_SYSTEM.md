# Dual Camera Face Attendance System

## Overview
The Dual Camera Face Attendance System allows you to operate both laptop and mobile cameras simultaneously, providing enhanced coverage and redundancy for face recognition and attendance tracking.

## Key Features

### 🎥 **Simultaneous Camera Operation**
- **Left Camera**: Typically laptop/webcam
- **Right Camera**: Typically mobile phone via DroidCam
- **Independent Controls**: Start, stop, and configure each camera separately
- **Global Controls**: Start or stop both cameras together

### 📱 **Enhanced Coverage**
- **Multiple Angles**: Capture faces from different positions
- **Redundancy**: Backup camera if one fails
- **Better Recognition**: Multiple viewpoints improve accuracy
- **Flexible Positioning**: Mobile camera can be positioned optimally

### 🔄 **Dual Processing Modes**
- **Preview Mode**: Live video feeds with basic face detection
- **Attendance Mode**: Full face recognition with attendance tracking
- **Real-time Statistics**: Monitor performance of both cameras

## Quick Start Guide

### 1. Launch the System
```bash
# Method 1: Dedicated launcher
python launch_dual_camera_system.py

# Method 2: Via main.py
python main.py --dual-camera

# Method 3: Direct execution
python -m src.gui.dual_camera_window
```

### 2. Setup Left Camera (Laptop)
1. Click "Select Left Camera" button
2. Choose "Laptop Camera" tab
3. Select from detected cameras
4. Click "Test Selected Camera"
5. Click "Use This Camera"
6. Click "Start Left" to begin

### 3. Setup Right Camera (Mobile)
1. Install DroidCam app on your phone
2. Connect phone and computer to same WiFi
3. Click "Select Right Camera" button
4. Choose "Mobile Camera" tab
5. Enter IP address from DroidCam app
6. Click "Test Connection"
7. Click "Test Selected Camera"
8. Click "Use This Camera"
9. Click "Start Right" to begin

### 4. Operation Modes

#### Preview Mode
- Basic face detection on both cameras
- No attendance tracking
- Good for testing setup and positioning

#### Attendance Mode
- Full face recognition on both cameras
- Automatic attendance marking
- Anti-spoofing detection
- Recognition cooldown prevents duplicates

## Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                Dual Camera Face Attendance System               │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ Left Camera     │ Right Camera    │ Global Controls             │
│ (Laptop)        │ (Mobile)        │                             │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────────────┐ │
│ │Select Left  │ │ │Select Right │ │ │ Start Both             │ │
│ │Start Left   │ │ │Start Right  │ │ │ Stop Both              │ │
│ │Stop Left    │ │ │Stop Right   │ │ │ ○ Preview ○ Attendance │ │
│ └─────────────┘ │ └─────────────┘ │ │ Register New User      │ │
└─────────────────┴─────────────────┴─────────────────────────────┘
├───────────────────────┬───────────────────────────────────────────┤
│ Left Camera Feed      │ Right Camera Feed                         │
│ ┌─────────────────────┐│ ┌─────────────────────────────────────┐   │
│ │                     ││ │                                     │   │
│ │    LEFT CAMERA      ││ │          RIGHT CAMERA               │   │
│ │                     ││ │                                     │   │
│ │   [Video Feed]      ││ │        [Video Feed]                 │   │
│ │                     ││ │                                     │   │
│ └─────────────────────┘│ └─────────────────────────────────────┘   │
│ Camera: Not selected   │ Camera: Not selected                      │
├───────────────────────┴───────────────────────────────────────────┤
│ System Status                    │ Statistics                     │
│ [10:30:15] System initialized... │ Registered Users: 5            │
│ [10:30:30] Left camera started.. │ Today's Attendance: 12         │
│ [10:30:45] Right camera started. │                                │
│ [10:31:00] Mode: Attendance      │ Left Camera: Running           │
│                                  │   Faces Detected: 15           │
│                                  │   Recognitions: 3              │
│                                  │                                │
│                                  │ Right Camera: Running          │
│                                  │   Faces Detected: 8            │
│                                  │   Recognitions: 2              │
└──────────────────────────────────┴────────────────────────────────┘
```

## Advanced Features

### 🎯 **Independent Camera Controls**
- Each camera can be started, stopped, and configured independently
- Different camera types (laptop vs mobile) can be used simultaneously
- Separate statistics tracking for each camera

### 📊 **Enhanced Statistics**
- **Per-Camera Metrics**: Faces detected and recognitions for each camera
- **Combined Totals**: Overall system performance
- **Real-time Updates**: Live statistics during operation

### 🔒 **Attendance Security**
- **Anti-Spoofing**: Both cameras use anti-spoofing detection
- **Recognition Cooldown**: Prevents duplicate attendance from same camera
- **Dual Verification**: Both cameras can verify the same person
- **Camera Source Tracking**: Records which camera detected each attendance

### 🌐 **Network Optimization**
- **Efficient Streaming**: Optimized for mobile camera connections
- **Connection Resilience**: Automatic recovery from network issues
- **Bandwidth Management**: Adaptive quality based on connection

## Configuration Options

### Camera Selection
- **Left Camera**: Usually laptop/webcam for primary coverage
- **Right Camera**: Usually mobile for secondary/better quality
- **Flexible Assignment**: Any camera type can be assigned to either side

### Video Quality Settings
- **Resolution**: Automatically optimized for display (640x480)
- **Frame Rate**: ~30 FPS for smooth operation
- **Buffer Management**: Low latency settings for real-time processing

### Recognition Settings
- **Confidence Threshold**: 0.7 for recognition acceptance
- **Cooldown Period**: 5 seconds between recognitions from same camera
- **Anti-Spoofing**: Enabled by default for both cameras

## Troubleshooting

### Camera Issues
**Problem**: Left camera not detecting
- Check USB connections and drivers
- Try different camera indices (0, 1, 2, etc.)
- Restart the application

**Problem**: Right camera connection fails
- Verify WiFi connection on both devices
- Check IP address in DroidCam app
- Ensure firewall allows connections

### Performance Issues
**Problem**: Slow video feed
- Close unnecessary applications
- Use ethernet instead of WiFi for computer
- Reduce video quality in camera settings

**Problem**: High CPU usage
- Run only one camera at a time for testing
- Check system resources
- Restart the application

### Recognition Issues
**Problem**: Poor recognition accuracy
- Improve lighting conditions
- Position cameras at eye level
- Ensure faces are clearly visible
- Re-register users with better photos

**Problem**: Duplicate attendances
- System has cooldown protection
- Check timestamp logs for verification
- Ensure proper mode selection

## File Structure

```
face-attendance-system/
├── launch_dual_camera_system.py          # Main launcher
├── test_dual_camera.py                   # Test script
├── main.py                               # Alternative launcher
├── src/
│   ├── gui/
│   │   ├── dual_camera_window.py         # Main dual camera interface
│   │   ├── camera_selection_window.py    # Camera selection dialog
│   │   └── main_window_enhanced_camera.py # Single camera interface
│   └── utils/
│       └── camera_utils.py               # Enhanced camera utilities
├── data/
│   ├── attendance/                       # Attendance records
│   ├── registered_users/                # User profiles
│   └── logs/                            # System logs
└── models/                              # AI model files
```

## Usage Scenarios

### 🏢 **Office Environment**
- **Left Camera**: Desk-mounted webcam for primary detection
- **Right Camera**: Mobile phone positioned at entrance
- **Benefits**: Complete coverage of entry points

### 🏫 **Classroom Setup**
- **Left Camera**: Laptop camera for teacher area
- **Right Camera**: Mobile camera for student area
- **Benefits**: Monitor both instructor and student attendance

### 🏠 **Home Office**
- **Left Camera**: Built-in laptop camera
- **Right Camera**: Phone positioned for better angle
- **Benefits**: Professional appearance for video calls

### 🚪 **Security Application**
- **Left Camera**: Fixed webcam for main monitoring
- **Right Camera**: Mobile for backup/different angle
- **Benefits**: Redundancy and comprehensive coverage

## Best Practices

### 📍 **Camera Positioning**
- Position cameras at eye level when possible
- Ensure good lighting from front, avoid backlighting
- Keep stable distance (2-4 feet from face)
- Angle cameras slightly downward for optimal face capture

### 🔧 **System Maintenance**
- Regularly clean camera lenses
- Check WiFi signal strength for mobile cameras
- Monitor system logs for errors
- Update DroidCam app regularly

### 📈 **Performance Optimization**
- Use wired connection for computer when possible
- Close unnecessary applications during operation
- Position mobile camera close to WiFi router
- Restart system if performance degrades

## Security Considerations

### 🛡️ **Data Protection**
- All face data stored locally
- Encrypted user profiles
- Secure network communication for mobile cameras
- Access logs for audit trail

### 🔒 **Anti-Spoofing**
- Multiple detection algorithms
- Liveness detection on both cameras
- Photo/video attack prevention
- Real-time verification

### 🌐 **Network Security**
- Local network communication only
- No external data transmission
- Secure DroidCam connections
- Firewall-friendly operation

## Support and Maintenance

### 📋 **Regular Maintenance**
- Check system logs weekly
- Update software components
- Backup user registration data
- Test camera connections regularly

### 🔧 **Troubleshooting Resources**
- System logs in `data/logs/`
- Error messages in status panel
- Performance statistics monitoring
- Network connectivity testing

### 📞 **Support Information**
- Check documentation files
- Review system logs for errors
- Test individual components
- Contact development team if needed

This dual camera system provides professional-grade attendance tracking with enhanced reliability, coverage, and flexibility for various environments and use cases.
