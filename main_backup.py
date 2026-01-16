#!/usr/bin/env python3
"""
Facial Attendance System - Complete Integrated Application
---------------------------------------------------------
Complete face attendance system with all camera modes integrated.
Supports single camera, dual camera, DroidCam, and enhanced features.
"""

import os
import logging
import argparse
import cv2
import time
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from PIL import Image, ImageTk
import requests

# Add the project root to path to allow imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
from src.face_detector import FaceDetector
from src.face_recognizer import FaceRecognizer
from src.anti_spoof import AntiSpoofingDetector
from src.attendance_manager import AttendanceManager
from src.user_manager import UserManager
from src.utils.data_utils import ensure_directories, load_registered_users
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
        
        self.left_label = tk.Label(left_frame, text="Laptop Camera Feed", bg='black', fg='white')
        self.left_label.pack(fill=tk.BOTH, expand=True)
        
        left_controls = ttk.Frame(left_frame)
        left_controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(left_controls, text="Start Left Camera", command=self.start_left_camera).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_controls, text="Stop Left Camera", command=self.stop_left_camera).pack(side=tk.LEFT)
        
        # Right camera (Mobile/DroidCam)
        right_frame = ttk.LabelFrame(camera_frame, text="Mobile Camera (DroidCam)", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.right_label = tk.Label(right_frame, text="Mobile Camera Feed", bg='black', fg='white')
        self.right_label.pack(fill=tk.BOTH, expand=True)
        
        right_controls = ttk.Frame(right_frame)
        right_controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(right_controls, text="Start Right Camera", command=self.start_right_camera).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(right_controls, text="Stop Right Camera", command=self.stop_right_camera).pack(side=tk.LEFT)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Attendance mode toggle
        self.attendance_var = tk.BooleanVar()
        attendance_check = ttk.Checkbutton(control_frame, text="Attendance Mode", 
                                         variable=self.attendance_var, 
                                         command=self.toggle_attendance_mode)
        attendance_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = tk.Label(control_frame, text="Ready", fg='green')
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Close button
        ttk.Button(control_frame, text="Close", command=self.close_application).pack(side=tk.RIGHT)
    
    def initialize_cameras(self):
        """Initialize both cameras"""
        self.start_left_camera()
        self.start_right_camera()
    
    def start_left_camera(self):
        """Start left camera (laptop camera)"""
        if not self.left_camera_running:
            self.left_camera = CameraManager.initialize_camera(0)
            if self.left_camera:
                self.left_camera_running = True
                self.left_video_thread = threading.Thread(target=self.update_left_camera, daemon=True)
                self.left_video_thread.start()
                self.status_label.config(text="Left camera started", fg='green')
            else:
                self.status_label.config(text="Failed to start left camera", fg='red')
      def stop_left_camera(self):
        """Stop left camera"""
        self.left_camera_running = False
        if self.left_camera:
            self.left_camera.release()
            self.left_camera = None
        self.status_label.config(text="Left camera stopped", fg='orange')
    
    def start_right_camera(self):
        """Start right camera (mobile camera)"""
        if not self.right_camera_running:
            mobile_url = "http://192.168.29.90:4747/video"
            self.status_label.config(text="Connecting to DroidCam...", fg='orange')
            self.right_camera = CameraManager.initialize_mobile_camera(mobile_url)
            if self.right_camera:
                self.right_camera_running = True
                self.right_video_thread = threading.Thread(target=self.update_right_camera, daemon=True)
                self.right_video_thread.start()
                self.status_label.config(text="DroidCam connected successfully", fg='green')
            else:
                self.status_label.config(text="DroidCam connection failed - Check IP/DroidCam app", fg='red')
                # Show helpful message
                self.show_droidcam_help()
    def stop_right_camera(self):
        """Stop right camera"""
        self.right_camera_running = False
        if self.right_camera:
            self.right_camera.release()
            self.right_camera = None
        self.status_label.config(text="Right camera stopped", fg='orange')
    
    def update_left_camera(self):
        """Update left camera feed"""
        while self.left_camera_running and self.left_camera:
            try:
                ret, frame = self.left_camera.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    
                    # Process frame for face detection if in attendance mode
                    if self.attendance_mode:
                        frame = self.process_frame_for_attendance(frame)
                    
                    # Convert and display - use thread-safe GUI update
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((640, 480), Image.Resampling.LANCZOS)
                    
                    # Schedule GUI update on main thread
                    self.master.after(0, self._update_left_image, img)
                    
                time.sleep(0.03)  # ~30 FPS                
            except Exception as e:
                logger.error(f"Error in left camera feed: {e}")
                break
    
    def _update_left_image(self, img):
        """Update left camera image on main thread"""
        try:
            photo = ImageTk.PhotoImage(img)
            self.left_label.config(image=photo)
            self.left_label.image = photo
        except Exception as e:
            logger.error(f"Error updating left image: {e}")
    
    def update_right_camera(self):
        """Update right camera feed"""
        while self.right_camera_running and self.right_camera:
            try:
                ret, frame = self.right_camera.read()
                if ret:
                    # Process frame for face detection if in attendance mode
                    if self.attendance_mode:
                        frame = self.process_frame_for_attendance(frame)                    
                    
                    # Convert and display - use thread-safe GUI update
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((640, 480), Image.Resampling.LANCZOS)
                    
                    # Schedule GUI update on main thread
                    self.master.after(0, self._update_right_image, img)
                    
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error in right camera feed: {e}")
                break
    
    def _update_right_image(self, img):
        """Update right camera image on main thread"""
        try:
            photo = ImageTk.PhotoImage(img)
            self.right_label.config(image=photo)
            self.right_label.image = photo
        except Exception as e:
            logger.error(f"Error updating right image: {e}")
    
    def process_frame_for_attendance(self, frame):
        """Process frame for face detection and recognition"""
        try:
            faces = self.face_detector.detect_faces(frame)
            
            for face in faces:
                x, y, w, h, face_crop, landmarks = face
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Extract face for recognition (use the pre-extracted face_crop)
                face_img = face_crop
                
                # Recognize face
                user_id = self.face_recognizer.recognize_face(face_img)
                
                if user_id:
                    cv2.putText(frame, f"User: {user_id}", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Unknown", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
        
        return frame
    
    def toggle_attendance_mode(self):
        """Toggle attendance mode on/off"""
        self.attendance_mode = self.attendance_var.get()
        mode_text = "ON" if self.attendance_mode else "OFF"
        self.status_label.config(text=f"Attendance Mode: {mode_text}", 
                               fg='blue' if self.attendance_mode else 'green')
    
    def close_application(self):
        """Close the application properly"""
        self.stop_left_camera()
        self.stop_right_camera()
        self.master.quit()
        self.master.destroy()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Face Attendance System')
    parser.add_argument('--no-gui', action='store_true', help='Run in CLI mode without GUI')
    parser.add_argument('--test', action='store_true', help='Run system tests')
    parser.add_argument('--dual-camera', action='store_true', help='Enable dual camera mode')
    parser.add_argument('--enhanced-camera', action='store_true', help='Enable enhanced camera features')
    parser.add_argument('--camera', type=int, default=0, help='Camera index to use')
    parser.add_argument('--mobile-camera', type=str, default='http://192.168.29.90:4747/video', 
                       help='Mobile camera URL (default: http://192.168.29.90:4747/video)')
    parser.add_argument('--droidcam-ip', type=str, default='192.168.29.90', 
                       help='DroidCam IP address (default: 192.168.29.90)')
    parser.add_argument('--droidcam-port', type=str, default='4747', 
                       help='DroidCam port (default: 4747)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()


def initialize_system():
    """Initialize system components and ensure required directories exist."""
    logger.info("Initializing Facial Attendance System...")
    
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
    
    # Check if models exist (optional check)
    missing_models = []
    for name, path in model_paths.items():
        if not os.path.exists(path):
            missing_models.append(path)
    
    if missing_models:
        logger.warning(f"Some model files not found: {missing_models}")
        logger.info("System will continue with basic functionality")
    
    # Initialize components
    try:
        face_detector = FaceDetector()
        face_recognizer = FaceRecognizer()
        anti_spoof = AntiSpoofingDetector()
        attendance_manager = AttendanceManager()
        user_manager = UserManager()
        
        logger.info("System initialization completed successfully")
        
        return {
            'face_detector': face_detector,
            'face_recognizer': face_recognizer,
            'anti_spoof': anti_spoof,
            'attendance_manager': attendance_manager,
            'user_manager': user_manager
        }
    
    except Exception as e:
        logger.error(f"Error initializing system components: {e}")
        return None


def run_cli_mode(components, args):
    """Run the system in command-line interface mode."""
    logger.info("Starting in CLI mode")
    
    face_detector = components['face_detector']
    face_recognizer = components['face_recognizer']
    anti_spoof_detector = components['anti_spoof']
    attendance_manager = components['attendance_manager']
    user_manager = components['user_manager']
    
    # Initialize camera
    if args.mobile_camera and CameraManager.test_droidcam_connection(args.droidcam_ip, args.droidcam_port):
        camera = CameraManager.initialize_mobile_camera(args.mobile_camera)
        print("Using mobile camera (DroidCam)")
    else:
        camera = CameraManager.initialize_camera(args.camera)
        print(f"Using local camera {args.camera}")
    
    if not camera:
        print("ERROR: Could not initialize camera")
        return
    
    print("\n=== Face Attendance System (CLI Mode) ===")
    print("Controls:")
    print("  'q' - Quit")
    print("  'a' - Mark attendance for recognized user")
    print("  'r' - Register new user")
    print("  'd' - Switch to dual camera mode")
    print("  ESC - Exit")
    print("=" * 50)
    
    current_user_id = None
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                logger.error("Failed to capture frame from camera")
                break
            
            # Flip frame horizontally for mirror effect (except for mobile cameras)
            if args.camera is not None:
                frame = cv2.flip(frame, 1)
              # Detect faces
            faces = face_detector.detect_faces(frame)
            
            for face in faces:
                x, y, w, h, face_crop, landmarks = face
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Extract face region (use the pre-extracted face_crop)
                face_img = face_crop
                
                # Anti-spoofing check
                is_real = anti_spoof_detector.is_real_face(face_img)
                
                if is_real:
                    # Face recognition
                    user_id = face_recognizer.recognize_face(face_img)
                    
                    if user_id:
                        current_user_id = user_id
                        cv2.putText(frame, f"Welcome {user_id}", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.putText(frame, "Press 'a' for attendance", (x, y+h+25), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        current_user_id = None
                        cv2.putText(frame, "Unknown User", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                        cv2.putText(frame, "Press 'r' to register", (x, y+h+25), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                else:
                    cv2.putText(frame, "SPOOF DETECTED!", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    log_spoof_attempt("CLI_MODE")
            
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
        
        # Try to load available GUI modules
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
            logger.warning("Complete GUI not available, using dual camera mode as fallback")
            run_dual_camera_mode()
        
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
