#!/usr/bin/env python3
"""
Enhanced Facial Attendance System - Integrated Main Application
--------------------------------------------------------------
Comprehensive main entry point with all camera features integrated:
- Single camera mode
- Enhanced camera selection
- Dual camera mode (laptop + mobile)
- CLI mode
- Complete GUI options
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core system imports
from src.face_detector import FaceDetector
from src.face_recognizer import FaceRecognizer
from src.anti_spoof import AntiSpoofingDetector
from src.attendance_manager import AttendanceManager
from src.user_manager import UserManager
from src.utils.image_utils import setup_camera
from src.utils.data_utils import ensure_directories
from src.enhanced_liveness_detector import EnhancedLivenessDetector
from src.security_logger import log_spoof_attempt

# Setup logging - ensure logs directory exists first
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', f'app_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Enhanced Facial Attendance System')
    
    # Mode selection
    parser.add_argument('--no-gui', action='store_true', help='Run in command-line mode without GUI')
    parser.add_argument('--gui-mode', choices=['basic', 'enhanced', 'dual'], default='enhanced',
                       help='GUI mode: basic (simple), enhanced (single camera selection), dual (dual camera)')
    
    # Camera options
    parser.add_argument('--camera', type=int, default=0, help='Camera index to use (for CLI/basic mode)')
    parser.add_argument('--mobile-camera', type=str, help='Mobile camera URL (e.g., http://192.168.1.100:4747/video)')
    
    # Legacy compatibility
    parser.add_argument('--basic-gui', action='store_true', help='Use basic GUI (legacy)')
    parser.add_argument('--enhanced-gui', action='store_true', help='Use enhanced GUI (legacy)')
    parser.add_argument('--enhanced-camera', action='store_true', help='Use enhanced camera selection (legacy)')
    parser.add_argument('--dual-camera', action='store_true', help='Use dual camera mode (legacy)')
    parser.add_argument('--complete-system', action='store_true', help='Launch complete system (legacy)')
    
    # System options
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test-cameras', action='store_true', help='Test camera availability and exit')
    
    return parser.parse_args()


def resolve_gui_mode(args):
    """Resolve GUI mode from arguments (handle legacy flags)"""
    if args.basic_gui:
        return 'basic'
    elif args.enhanced_gui or args.enhanced_camera:
        return 'enhanced'
    elif args.dual_camera:
        return 'dual'
    elif args.complete_system:
        return 'complete'
    else:
        return args.gui_mode


def initialize_system():
    """Initialize system components and ensure required directories exist."""
    logger.info("Initializing Enhanced Facial Attendance System...")
    
    # Ensure necessary directories exist
    ensure_directories([
        os.path.join('data', 'attendance'),
        os.path.join('data', 'registered_users'),
        os.path.join('data', 'logs')
    ])
    
    # Initialize components
    model_paths = {
        'face_landmarks': os.path.join('models', 'shape_predictor_68_face_landmarks.dat'),
        'anti_spoof': os.path.join('models', 'anti_spoof_model.h5'),
        'face_recognition': os.path.join('models', 'face_recognition_model.h5')
    }
    
    # Check if models exist (warn but don't fail)
    missing_models = []
    for name, path in model_paths.items():
        if not os.path.exists(path):
            missing_models.append(path)
    
    if missing_models:
        logger.warning("Some model files are missing:")
        for model in missing_models:
            logger.warning(f"  - {model}")
        logger.warning("System will work but some features may be limited.")
    
    # Initialize components with error handling
    try:
        face_detector = FaceDetector(model_paths['face_landmarks'])
    except Exception as e:
        logger.warning(f"Face detector initialization failed: {e}. Using basic detection.")
        face_detector = None
        
    try:
        face_recognizer = FaceRecognizer(model_path=model_paths['face_recognition'])
    except Exception as e:
        logger.warning(f"Face recognizer initialization failed: {e}. Recognition disabled.")
        face_recognizer = None
        
    try:
        anti_spoof = AntiSpoofingDetector(model_path=model_paths['anti_spoof'])
    except Exception as e:
        logger.warning(f"Anti-spoof detector initialization failed: {e}. Anti-spoofing disabled.")
        anti_spoof = None
    
    attendance_manager = AttendanceManager()
    user_manager = UserManager()
    
    # Check if there are any registered users
    registered_dir = os.path.join('data', 'registered_users')
    if os.path.exists(registered_dir):
        user_dirs = [d for d in os.listdir(registered_dir) 
                   if os.path.isdir(os.path.join(registered_dir, d)) and not d.startswith('.')]
        if not user_dirs:
            logger.info("No registered users found. System is ready for new registrations.")
            print("NOTE: No registered users found in the database.")
            print("      Use the 'Register New User' button to add users to the system.")
    
    return {
        'face_detector': face_detector,
        'face_recognizer': face_recognizer,
        'anti_spoof': anti_spoof,
        'attendance_manager': attendance_manager,
        'user_manager': user_manager
    }


def test_camera_availability():
    """Test and display available cameras"""
    print("Testing camera availability...")
    print("=" * 50)
    
    # Test laptop cameras
    available_cameras = []
    for i in range(6):  # Test first 6 camera indices
        try:
            import cv2
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    available_cameras.append(i)
                    print(f"✅ Camera {i}: Available")
                else:
                    print(f"❌ Camera {i}: Cannot read frames")
                cap.release()
            else:
                print(f"❌ Camera {i}: Cannot open")
        except Exception as e:
            print(f"❌ Camera {i}: Error - {e}")
    
    print(f"\nFound {len(available_cameras)} working cameras: {available_cameras}")
    
    # Test DroidCam connectivity
    print("\nTesting DroidCam connectivity...")
    try:
        from src.utils.camera_utils import CameraManager
        found_devices = CameraManager.scan_for_droidcam_devices()
        if found_devices:
            print(f"✅ Found DroidCam devices: {found_devices}")
        else:
            print("ℹ️  No DroidCam devices found on network")
    except Exception as e:
        print(f"❌ DroidCam test failed: {e}")
    
    print("\nCamera test completed.")


def run_cli_mode(components, args):
    """Run the system in command-line interface mode."""
    import cv2
    
    logger.info("Starting in CLI mode")
    print("Enhanced Facial Attendance System - CLI Mode")
    print("=" * 50)
    
    # Determine camera source
    camera_source = args.camera
    if args.mobile_camera:
        camera_source = args.mobile_camera
        print(f"Using mobile camera: {camera_source}")
    else:
        print(f"Using laptop camera: {camera_source}")
    
    camera = setup_camera(camera_source)
    if not camera.isOpened():
        logger.error(f"Failed to open camera: {camera_source}")
        print(f"ERROR: Failed to open camera: {camera_source}")
        if isinstance(camera_source, str):
            print("Tip: Make sure DroidCam is running and IP address is correct")
        sys.exit(1)
    
    print("Controls:")
    print("  'q' - Quit")
    print("  'a' - Mark attendance (when face is recognized)")
    print("  'r' - Register new user")
    print("  'p' - Toggle preview mode")
    print()
    
    # Initialize components
    face_detector = components['face_detector']
    face_recognizer = components['face_recognizer']
    attendance_manager = components['attendance_manager']
    user_manager = components['user_manager']
      # Initialize liveness detector if available
    try:
        liveness_detector = EnhancedLivenessDetector(
            anti_spoof_model_path='models/anti_spoof_model.h5',
            phone_cascade_path=None
        )
    except Exception as e:
        logger.warning(f"Liveness detector failed to initialize: {e}")
        liveness_detector = None
    
    current_user_id = None
    preview_mode = False
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                logger.error("Failed to capture frame from camera")
                break
            
            # Add camera info to frame
            camera_info = f"Camera: {camera_source} | Mode: {'Preview' if preview_mode else 'Attendance'}"
            cv2.putText(frame, camera_info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            if face_detector:
                # Detect faces
                faces = face_detector.detect_faces(frame)
                
                # Process each detected face
                for face_data in faces:
                    # Extract face coordinates
                    if isinstance(face_data, tuple) and len(face_data) == 6:
                        x, y, w, h, face_crop, landmarks = face_data
                        left, top, right, bottom = x, y, x + w, y + h
                    elif hasattr(face_data, 'left'):  # dlib rectangle
                        left = face_data.left()
                        top = face_data.top()
                        right = face_data.right()
                        bottom = face_data.bottom()
                        face_crop = frame[top:bottom, left:right]
                    else:
                        continue
                    
                    if preview_mode:
                        # Simple preview mode
                        cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
                        cv2.putText(frame, "Face Detected", (left, top - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                        continue
                    
                    # Full attendance mode processing
                    color = (0, 0, 255)  # Default red
                    label = "Unknown"
                    
                    # Liveness check if available
                    if liveness_detector:
                        is_live, reason = liveness_detector.is_live(frame, prev_frame=None, prev_landmarks=None)
                        if not is_live:
                            log_spoof_attempt(reason, frame=frame, user_id=None, context='cli')
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                            cv2.putText(frame, f"Spoof: {reason}", (left, top - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                            continue
                    
                    # Anti-spoofing check if available
                    if components['anti_spoof']:
                        is_real = components['anti_spoof'].check_if_real(face_crop)
                        if not is_real:
                            color = (0, 255, 255)  # Yellow
                            label = "SPOOF DETECTED"
                            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                            cv2.putText(frame, label, (left, top - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            continue
                    
                    # Face recognition if available
                    if face_recognizer:
                        recognition_result = face_recognizer.recognize_face(face_crop)
                        user_id, name, confidence = recognition_result
                        
                        if user_id and confidence > 0.7:
                            current_user_id = user_id
                            color = (0, 255, 0)  # Green
                            label = f"{name} ({confidence:.2f})"
                        else:
                            current_user_id = None
                            label = "Unknown Person"
                    
                    # Draw results
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(frame, label, (left, top - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Display frame
            cv2.imshow('Enhanced Face Attendance System', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a') and current_user_id:
                attendance_manager.mark_attendance(current_user_id)
                print(f"✅ Attendance marked for {current_user_id}")
            elif key == ord('a') and not current_user_id:
                print("❌ No recognized user to mark attendance for")
            elif key == ord('r'):
                print("\n🔄 Starting user registration...")
                try:
                    user_manager.register_new_user()
                    if face_recognizer:
                        face_recognizer.reload_user_data()
                    print("✅ User registration completed")
                except Exception as e:
                    print(f"❌ Registration failed: {e}")
            elif key == ord('p'):
                preview_mode = not preview_mode
                print(f"🔄 Mode changed to: {'Preview' if preview_mode else 'Attendance'}")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        logger.exception(f"Error in CLI mode: {e}")
        print(f"❌ Error: {e}")
    finally:
        camera.release()
        cv2.destroyAllWindows()


def run_gui_mode(components, args):
    """Run the system with graphical user interface."""
    gui_mode = resolve_gui_mode(args)
    logger.info(f"Starting GUI mode: {gui_mode}")
    
    try:
        import tkinter as tk
        
        # Dual camera mode
        if gui_mode == 'dual':
            try:
                from src.gui.dual_camera_window import DualCameraWindow
                logger.info("Loading Dual Camera GUI")
                
                root = tk.Tk()
                app = DualCameraWindow(root)
                root.protocol("WM_DELETE_WINDOW", app.close_application)
                root.mainloop()
                return
                
            except ImportError as e:
                logger.warning(f"Dual Camera GUI not available: {e}")
                gui_mode = 'enhanced'  # Fallback
        
        # Enhanced camera mode
        if gui_mode == 'enhanced':
            try:
                from src.gui.main_window_enhanced_camera import EnhancedCameraMainWindow
                logger.info("Loading Enhanced Camera GUI")
                
                root = tk.Tk()
                app = EnhancedCameraMainWindow(root)
                root.protocol("WM_DELETE_WINDOW", app.close_application)
                root.mainloop()
                return
                
            except ImportError as e:
                logger.warning(f"Enhanced Camera GUI not available: {e}")
                gui_mode = 'complete'  # Fallback
        
        # Complete system mode
        if gui_mode == 'complete':
            try:
                from src.gui.main_window_complete import CompleteMainWindow
                logger.info("Loading Complete GUI")
                
                root = tk.Tk()
                root.title("Face Attendance System - Complete")
                root.geometry("1200x800")
                
                app = CompleteMainWindow(root)
                root.protocol("WM_DELETE_WINDOW", app.close_application)
                root.mainloop()
                return
                
            except ImportError as e:
                logger.warning(f"Complete GUI not available: {e}")
                gui_mode = 'basic'  # Final fallback
        
        # Basic GUI mode (final fallback)
        try:
            from src.gui.main_window import MainWindow
            logger.info("Loading Basic GUI")
            
            root = tk.Tk()
            app = MainWindow(root)
            root.protocol("WM_DELETE_WINDOW", getattr(app, 'close_application', app.on_closing))
            root.mainloop()
            
        except ImportError as e:
            logger.error(f"No GUI modules available: {e}")
            print("❌ ERROR: GUI modules not available.")
            print("💡 Try running in CLI mode with --no-gui")
            return False
        
    except Exception as e:
        logger.exception(f"Error in GUI mode: {e}")
        print(f"❌ GUI Error: {e}")
        print("💡 Try running in CLI mode with --no-gui")
        return False
    
    return True


def main():
    """Main function to run the Enhanced Facial Attendance System."""
    args = parse_arguments()
    
    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Show startup banner
    print("=" * 70)
    print("Enhanced Facial Attendance System")
    print("=" * 70)
    print("Features:")
    print("  • Single camera support (laptop/mobile)")
    print("  • Dual camera support (laptop + mobile simultaneously)")
    print("  • DroidCam integration for mobile cameras")
    print("  • Enhanced face recognition with anti-spoofing")
    print("  • Multiple GUI modes and CLI mode")
    print("  • Real-time attendance tracking")
    print()
    
    # Test cameras if requested
    if args.test_cameras:
        test_camera_availability()
        return 0
    
    # Handle complete system launcher (legacy)
    if args.complete_system:
        logger.info("Launching complete system via launch_complete_system.py")
        try:
            import launch_complete_system
            return 0 if launch_complete_system.main() else 1
        except Exception as e:
            logger.exception(f"Failed to launch complete system: {e}")
            print(f"❌ ERROR: Failed to launch complete system: {e}")
            return 1
    
    try:
        # Initialize system components
        components = initialize_system()
        
        if args.no_gui:
            # CLI mode
            run_cli_mode(components, args)
        else:
            # GUI mode
            success = run_gui_mode(components, args)
            if not success:
                print("\n🔄 Falling back to CLI mode...")
                run_cli_mode(components, args)
            
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        return 0
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        print(f"❌ ERROR: {e}")
        return 1
    
    logger.info("Application closed normally")
    return 0


if __name__ == "__main__":
    sys.exit(main())
