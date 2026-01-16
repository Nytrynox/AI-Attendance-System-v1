#!/usr/bin/env python3
"""
Facial Attendance System - Complete Integrated Application
---------------------------------------------------------
Complete face attendance system with all camera modes integrated.
Supports single camera, dual camera, DroidCam, and enhanced features.
"""

import os
import sys
import logging
import argparse
import cv2
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from PIL import Image, ImageTk
import requests
import socket

# Add the project root to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
from src.face_detector import FaceDetector
from src.face_recognizer import FaceRecognizer
from src.anti_spoof import AntiSpoofingDetector
from src.attendance_manager import AttendanceManager
from src.user_manager import UserManager
from src.utils.image_utils import setup_camera
from src.utils.data_utils import ensure_directories, load_registered_users, save_attendance
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


class CameraManager:
    """Integrated camera management system"""
    
    def __init__(self):
        self.current_camera = None
        self.camera_type = None
    
    @staticmethod
    def initialize_camera(camera_index=0, max_retries=3, retry_delay=1.0):
        """Initialize camera with proper error handling and retries."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to initialize camera {camera_index} (attempt {attempt + 1}/{max_retries})")
                
                cap = cv2.VideoCapture(camera_index)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        logger.info("Camera initialized successfully")
                        return cap
                    else:
                        logger.warning("Camera returned no frames")
                        cap.release()
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
            except Exception as e:
                logger.error(f"Error initializing camera on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error("Failed to initialize camera after all attempts")
        return None
    
    @staticmethod
    def initialize_mobile_camera(url, max_retries=3, retry_delay=1.0):
        """Initialize mobile camera (DroidCam) connection."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to mobile camera {url} (attempt {attempt + 1}/{max_retries})")
                
                response = requests.get(url, timeout=5, stream=True)
                if response.status_code != 200:
                    logger.warning(f"HTTP error: {response.status_code}")
                    continue
                
                cap = cv2.VideoCapture(url)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        logger.info("Mobile camera initialized successfully")
                        return cap
                    else:
                        logger.warning("Mobile camera returned no frames")
                        cap.release()
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
            except Exception as e:
                logger.error(f"Error connecting to mobile camera on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error("Failed to connect to mobile camera after all attempts")
        return None
    
    @staticmethod
    def test_droidcam_connection(ip, port="4747"):
        """Test DroidCam connection."""
        try:
            url = f"http://{ip}:{port}/video"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    @staticmethod
    def test_camera_availability():
        """Test if any cameras are available on the system"""
        available_cameras = []
        
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    available_cameras.append(i)
                cap.release()
        
        return available_cameras


class DualCameraWindow:
    """Integrated dual camera window for simultaneous laptop and mobile camera operation"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Face Attendance System - Dual Camera Mode")
        self.master.geometry("1600x900")
        
        # Initialize models
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.anti_spoof_detector = AntiSpoofingDetector()
        self.camera_manager = CameraManager()
        
        # Load registered users
        self.registered_users = load_registered_users()
        self.face_recognizer.reload_user_data()
        
        # Camera variables
        self.left_camera = None
        self.right_camera = None
        self.left_camera_running = False
        self.right_camera_running = False
        self.left_video_thread = None
        self.right_video_thread = None
        
        # Attendance mode
        self.attendance_mode = False
        
        # Create GUI
        self.create_widgets()
        
        # Initialize cameras
        self.initialize_cameras()
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Camera frames
        camera_frame = ttk.Frame(main_frame)
        camera_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left camera (Laptop)
        left_frame = ttk.LabelFrame(camera_frame, text="Laptop Camera", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.left_label = ttk.Label(left_frame, text="Camera not initialized")
        self.left_label.pack(expand=True)
        
        left_controls = ttk.Frame(left_frame)
        left_controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(left_controls, text="Start Left Camera", 
                  command=self.start_left_camera).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_controls, text="Stop Left Camera", 
                  command=self.stop_left_camera).pack(side=tk.LEFT)
        
        # Right camera (Mobile)
        right_frame = ttk.LabelFrame(camera_frame, text="Mobile Camera (DroidCam)", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.right_label = ttk.Label(right_frame, text="Camera not initialized")
        self.right_label.pack(expand=True)
        
        right_controls = ttk.Frame(right_frame)
        right_controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(right_controls, text="Start Right Camera", 
                  command=self.start_right_camera).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(right_controls, text="Stop Right Camera", 
                  command=self.stop_right_camera).pack(side=tk.LEFT)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="Toggle Attendance Mode", 
                  command=self.toggle_attendance_mode).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Register New User", 
                  command=self.register_user).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Exit", 
                  command=self.close_application).pack(side=tk.RIGHT)
        
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))
    
    def initialize_cameras(self):
        """Initialize both cameras"""
        # Initialize laptop camera
        self.left_camera = CameraManager.initialize_camera(0)
        if self.left_camera:
            logger.info("Laptop camera initialized")
        else:
            logger.warning("Failed to initialize laptop camera")
        
        # Initialize mobile camera (DroidCam)
        droidcam_url = "http://192.168.29.90:4747/video"
        self.right_camera = CameraManager.initialize_mobile_camera(droidcam_url)
        if self.right_camera:
            logger.info("Mobile camera initialized")
        else:
            logger.warning("Failed to initialize mobile camera")
    
    def start_left_camera(self):
        """Start left camera feed"""
        if self.left_camera and not self.left_camera_running:
            self.left_camera_running = True
            self.left_video_thread = threading.Thread(target=self.update_left_camera)
            self.left_video_thread.daemon = True
            self.left_video_thread.start()
    
    def start_right_camera(self):
        """Start right camera feed"""
        if self.right_camera and not self.right_camera_running:
            self.right_camera_running = True
            self.right_video_thread = threading.Thread(target=self.update_right_camera)
            self.right_video_thread.daemon = True
            self.right_video_thread.start()
    
    def stop_left_camera(self):
        """Stop left camera feed"""
        self.left_camera_running = False
    
    def stop_right_camera(self):
        """Stop right camera feed"""
        self.right_camera_running = False
    
    def update_left_camera(self):
        """Update left camera display"""
        while self.left_camera_running:
            try:
                ret, frame = self.left_camera.read()
                if ret:
                    # Process frame for face detection
                    processed_frame = self.process_frame(frame, "LEFT")
                    
                    # Convert to PhotoImage and update label
                    img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)
                    img = img.resize((400, 300))
                    photo = ImageTk.PhotoImage(img)
                    
                    self.left_label.configure(image=photo)
                    self.left_label.image = photo
                
                time.sleep(0.03)  # ~30 FPS
            except Exception as e:
                logger.error(f"Error in left camera update: {e}")
                break
    
    def update_right_camera(self):
        """Update right camera display"""
        while self.right_camera_running:
            try:
                ret, frame = self.right_camera.read()
                if ret:
                    # Process frame for face detection
                    processed_frame = self.process_frame(frame, "RIGHT")
                    
                    # Convert to PhotoImage and update label
                    img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)
                    img = img.resize((400, 300))
                    photo = ImageTk.PhotoImage(img)
                    
                    self.right_label.configure(image=photo)
                    self.right_label.image = photo
                
                time.sleep(0.03)  # ~30 FPS
            except Exception as e:
                logger.error(f"Error in right camera update: {e}")
                break
    
    def process_frame(self, frame, camera_side):
        """Process frame for face detection and recognition"""
        try:
            # Add camera info
            cv2.putText(frame, f"Camera: {camera_side}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if self.attendance_mode:
                cv2.putText(frame, "ATTENDANCE MODE", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Detect faces
            faces = self.face_detector.detect_faces(frame)
            
            for face_data in faces:
                # Process face detection results
                if isinstance(face_data, tuple) and len(face_data) == 6:
                    x, y, w, h, face_crop, landmarks = face_data
                    left, top, right, bottom = x, y, x + w, y + h
                elif hasattr(face_data, 'left'):
                    left = face_data.left()
                    top = face_data.top()
                    right = face_data.right()
                    bottom = face_data.bottom()
                    face_crop = frame[top:bottom, left:right]
                else:
                    continue
                
                # Check for spoofing
                is_real = self.anti_spoof_detector.check_if_real(face_crop)
                
                if is_real:
                    # Recognize face
                    recognition_result = self.face_recognizer.recognize_face(face_crop)
                    user_id, name, confidence = recognition_result
                    
                    if user_id and confidence > 0.7:
                        # Draw green rectangle for recognized user
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"{name} ({confidence:.2f})", 
                                  (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        # Auto-mark attendance if in attendance mode
                        if self.attendance_mode:
                            self.mark_attendance(user_id)
                    else:
                        # Draw red rectangle for unknown face
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "Unknown", 
                                  (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    # Draw yellow rectangle for spoof detected
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                    cv2.putText(frame, "SPOOF DETECTED", 
                              (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame
    
    def toggle_attendance_mode(self):
        """Toggle attendance mode"""
        self.attendance_mode = not self.attendance_mode
        status = "ON" if self.attendance_mode else "OFF"
        self.status_label.configure(text=f"Attendance Mode: {status}")
        logger.info(f"Attendance mode: {status}")
    
    def mark_attendance(self, user_id):
        """Mark attendance for user"""
        try:
            attendance_manager = AttendanceManager()
            attendance_manager.mark_attendance(user_id)
            logger.info(f"Attendance marked for {user_id}")
        except Exception as e:
            logger.error(f"Error marking attendance: {e}")
    
    def register_user(self):
        """Register new user"""
        try:
            user_manager = UserManager()
            user_manager.register_new_user()
            self.face_recognizer.reload_user_data()
            messagebox.showinfo("Success", "User registered successfully!")
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            messagebox.showerror("Error", f"Registration failed: {e}")
    
    def close_application(self):
        """Close the application"""
        self.stop_left_camera()
        self.stop_right_camera()
        
        if self.left_camera:
            self.left_camera.release()
        if self.right_camera:
            self.right_camera.release()
        
        self.master.destroy()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Facial Attendance System - Complete Integration')
    parser.add_argument('--no-gui', action='store_true', help='Run in command-line mode without GUI')
    parser.add_argument('--dual-camera', action='store_true', help='Use dual camera mode (laptop + mobile)')
    parser.add_argument('--droidcam', action='store_true', help='Use DroidCam at 192.168.29.90')
    parser.add_argument('--camera', type=int, default=0, help='Camera index to use')
    parser.add_argument('--mobile-camera', type=str, default='http://192.168.29.90:4747/video', 
                       help='Mobile camera URL')
    parser.add_argument('--droidcam-ip', type=str, default='192.168.29.90', 
                       help='DroidCam IP address')
    parser.add_argument('--droidcam-port', type=str, default='4747', 
                       help='DroidCam port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test', action='store_true', help='Run system tests')
    return parser.parse_args()


def initialize_system():
    """Initialize system components and ensure required directories exist."""
    logger.info("Initializing Face Attendance System...")
    
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
    
    # Check if models exist
    for name, path in model_paths.items():
        if not os.path.exists(path):
            logger.error(f"Required model not found: {path}")
            print(f"ERROR: Required model not found: {path}")
            print("Please download the required models before running the application.")
            return None
    
    # Initialize components
    face_detector = FaceDetector(model_paths['face_landmarks'])
    face_recognizer = FaceRecognizer(model_path=model_paths['face_recognition'])
    anti_spoof = AntiSpoofingDetector(model_path=model_paths['anti_spoof'])
    attendance_manager = AttendanceManager()
    user_manager = UserManager()
    
    return {
        'face_detector': face_detector,
        'face_recognizer': face_recognizer,
        'anti_spoof': anti_spoof,
        'attendance_manager': attendance_manager,
        'user_manager': user_manager
    }


def run_cli_mode(components, args):
    """Run the system in command-line interface mode."""
    logger.info("Starting in CLI mode")
    
    # Handle mobile camera URL if provided
    if args.mobile_camera:
        camera_source = args.mobile_camera
        logger.info(f"Using mobile camera: {camera_source}")
        camera = CameraManager.initialize_mobile_camera(camera_source)
    elif args.droidcam:
        droidcam_url = f"http://{args.droidcam_ip}:{args.droidcam_port}/video"
        logger.info(f"Using DroidCam: {droidcam_url}")
        camera = CameraManager.initialize_mobile_camera(droidcam_url)
    else:
        camera_source = args.camera
        camera = CameraManager.initialize_camera(camera_source)
    
    if not camera or not camera.isOpened():
        logger.error(f"Failed to open camera")
        print("ERROR: Failed to open camera")
        return
    
    print("Face Attendance System - CLI Mode")
    print("--------------------------------")
    print("Press 'q' to quit, 'a' to mark attendance, 'r' to register new user")
    print("Press 'd' to switch to dual camera mode")
    
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
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                logger.error("Failed to capture frame from camera")
                break
            
            # Add camera source info to frame
            camera_info = f"Camera: CLI Mode"
            cv2.putText(frame, camera_info, (10, frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Detect faces
            faces = face_detector.detect_faces(frame)
            
            for face_data in faces:
                # Extract face coordinates
                if isinstance(face_data, tuple) and len(face_data) == 6:
                    x, y, w, h, face_crop, landmarks = face_data
                    left, top, right, bottom = x, y, x + w, y + h
                elif hasattr(face_data, 'left'):
                    left = face_data.left()
                    top = face_data.top()
                    right = face_data.right()
                    bottom = face_data.bottom()
                    face_crop = frame[top:bottom, left:right]
                else:
                    continue
                
                # Check liveness if available
                if liveness_detector:
                    is_live, reason = liveness_detector.is_live(frame, prev_frame=None, prev_landmarks=None)
                    if not is_live:
                        log_spoof_attempt(reason, frame=frame, user_id=None, context='cli')
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, f"{reason}", 
                                  (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        continue
                
                # Check for spoofing
                anti_spoof = components['anti_spoof']
                is_real = anti_spoof.check_if_real(face_crop)
                
                if is_real:
                    # Recognize face
                    recognition_result = face_recognizer.recognize_face(face_crop)
                    user_id, name, confidence = recognition_result
                    
                    if user_id and confidence > 0.7:
                        current_user_id = user_id
                        print(f"Recognized: {user_id}, Confidence: {confidence:.2f}")
                        
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"{name} ({confidence:.2f})", 
                                  (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    else:
                        current_user_id = None
                        print("Unknown face detected")
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "Unknown", 
                                  (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    current_user_id = None
                    print("Warning: Potential spoofing attempt detected!")
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                    cv2.putText(frame, "SPOOF DETECTED", 
                              (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('Face Attendance System', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                if current_user_id:
                    attendance_manager.mark_attendance(current_user_id)
                    print(f"Attendance marked for {current_user_id}")
                else:
                    print("No recognized user to mark attendance for")
            elif key == ord('r'):
                print("\nStarting user registration...")
                try:
                    user_manager.register_new_user()
                    face_recognizer.reload_user_data()
                    print("User registration completed successfully.")
                except Exception as e:
                    print(f"Registration failed: {e}")
            elif key == ord('d'):
                print("\nSwitching to dual camera mode...")
                camera.release()
                cv2.destroyAllWindows()
                run_dual_camera_mode()
                return
    
    except Exception as e:
        logger.exception(f"Error in CLI mode: {e}")
        print(f"Error: {e}")
    finally:
        camera.release()
        cv2.destroyAllWindows()


def run_dual_camera_mode():
    """Run dual camera mode"""
    try:
        root = tk.Tk()
        app = DualCameraWindow(root)
        root.protocol("WM_DELETE_WINDOW", app.close_application)
        root.mainloop()
    except Exception as e:
        logger.error(f"Dual camera mode error: {e}")
        print(f"Error in dual camera mode: {e}")


def run_gui_mode(components, args):
    """Run the system with a graphical user interface."""
    logger.info("Starting in GUI mode")
    
    try:
        # Check if dual camera mode is requested
        if args.dual_camera:
            run_dual_camera_mode()
            return
        
        # Simple GUI fallback
        try:
            from src.gui.main_window_complete import CompleteMainWindow
            logger.info("Loading Complete GUI")
            
            root = tk.Tk()
            root.title("Face Attendance System")
            root.geometry("1200x800")
            
            app = CompleteMainWindow(root)
            root.protocol("WM_DELETE_WINDOW", getattr(app, 'close_application', app.on_closing))
            root.mainloop()
            
        except ImportError:
            logger.warning("Complete GUI not available, falling back to CLI mode")
            run_cli_mode(components, args)
        
    except Exception as e:
        logger.error(f"GUI error: {e}")
        print("Falling back to CLI mode...")
        run_cli_mode(components, args)


def run_system_tests():
    """Run integrated system tests"""
    print("🧪 Running Face Attendance System Tests")
    print("=" * 50)
    
    # Test camera availability
    print("Testing camera availability...")
    cameras = CameraManager.test_camera_availability()
    print(f"Available cameras: {cameras}")
    
    # Test DroidCam connection
    print("Testing DroidCam connection...")
    droidcam_available = CameraManager.test_droidcam_connection("192.168.29.90")
    print(f"DroidCam available: {droidcam_available}")
    
    # Test model files
    print("Testing model files...")
    model_files = [
        'models/shape_predictor_68_face_landmarks.dat',
        'models/anti_spoof_model.h5',
        'models/face_recognition_model.h5'
    ]
    
    for model_file in model_files:
        exists = os.path.exists(model_file)
        print(f"  {model_file}: {'✓' if exists else '✗'}")
    
    print("\n✅ System test completed!")


def main():
    """Main function to run the Face Attendance System."""
    args = parse_arguments()
    
    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Run tests if requested
    if args.test:
        run_system_tests()
        return 0
    
    try:
        components = initialize_system()
        if not components:
            return 1
        
        if args.no_gui:
            run_cli_mode(components, args)
        else:
            run_gui_mode(components, args)
            
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        print(f"ERROR: {e}")
        return 1
    
    logger.info("Application closed normally")
    return 0


if __name__ == "__main__":
    sys.exit(main())
