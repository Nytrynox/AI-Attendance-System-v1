#!/usr/bin/env python3
"""
Debug version of the liveness window with bypass options for testing
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import pickle
from datetime import datetime

# Add the src directory to the path
import sys
sys.path.append('src')

from src.utils.camera_utils import CameraManager
from src.face_detector import FaceDetector
from src.anti_spoof import AntiSpoofDetector
from src.utils.image_utils import preprocess_for_face_recognition

class DebugLivenessWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Debug Liveness Registration Window")
        self.master.geometry("800x700")
        
        # Initialize components
        self.face_detector = FaceDetector()
        self.anti_spoof_detector = AntiSpoofDetector()
        
        # Camera and capture state
        self.camera_running = False
        self.current_frame = None
        self.captured_frame = None
        self.face_encoding = None
        self.face_captured = False
        
        # Liveness state (simplified for testing)
        self.liveness_tests_completed = {
            'blink': False,
            'head_movement': False,
            'phone_detection': False
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Title
        title_label = tk.Label(self.master, text="Debug Face Registration", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # User input frame
        input_frame = tk.Frame(self.master)
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = tk.Entry(input_frame, width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(input_frame, text="ID:").grid(row=1, column=0, padx=5, pady=5)
        self.id_entry = tk.Entry(input_frame, width=20)
        self.id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Camera controls
        camera_frame = tk.Frame(self.master)
        camera_frame.pack(pady=10)
        
        self.start_camera_btn = tk.Button(camera_frame, text="Start Camera", 
                                         command=self.start_camera, bg="green", fg="white")
        self.start_camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_camera_btn = tk.Button(camera_frame, text="Stop Camera", 
                                        command=self.stop_camera, state=tk.DISABLED)
        self.stop_camera_btn.pack(side=tk.LEFT, padx=5)
        
        # Camera display
        self.camera_label = tk.Label(self.master, text="Camera not started", 
                                    width=80, height=20, bg="black", fg="white")
        self.camera_label.pack(pady=10)
        
        # Liveness status with bypass buttons
        liveness_frame = tk.Frame(self.master)
        liveness_frame.pack(pady=10)
        
        tk.Label(liveness_frame, text="Liveness Tests:", font=("Arial", 12, "bold")).pack()
        
        self.blink_status = tk.Label(liveness_frame, text="❌ Blink Test")
        self.blink_status.pack()
        self.bypass_blink_btn = tk.Button(liveness_frame, text="Bypass Blink", 
                                         command=lambda: self.bypass_test('blink'))
        self.bypass_blink_btn.pack()
        
        self.head_status = tk.Label(liveness_frame, text="❌ Head Movement Test")
        self.head_status.pack()
        self.bypass_head_btn = tk.Button(liveness_frame, text="Bypass Head Movement", 
                                        command=lambda: self.bypass_test('head_movement'))
        self.bypass_head_btn.pack()
        
        self.phone_status = tk.Label(liveness_frame, text="❌ Phone Detection Test")
        self.phone_status.pack()
        self.bypass_phone_btn = tk.Button(liveness_frame, text="Bypass Phone Detection", 
                                         command=lambda: self.bypass_test('phone_detection'))
        self.bypass_phone_btn.pack()
        
        # Action buttons
        action_frame = tk.Frame(self.master)
        action_frame.pack(pady=10)
        
        self.capture_btn = tk.Button(action_frame, text="Capture Face", 
                                    command=self.capture_face, state=tk.DISABLED,
                                    bg="blue", fg="white")
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(action_frame, text="Save User", 
                                 command=self.save_user, state=tk.DISABLED,
                                 bg="orange", fg="white")
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(self.master, text="Ready to start", 
                                    wraplength=400, bg="lightgray")
        self.status_label.pack(pady=5, fill=tk.X)
        
    def bypass_test(self, test_name):
        """Bypass a liveness test for debugging"""
        self.liveness_tests_completed[test_name] = True
        self.update_liveness_status()
        messagebox.showinfo("Debug", f"{test_name.title()} test bypassed!")
        
    def update_liveness_status(self):
        """Update the liveness test status display"""
        if self.liveness_tests_completed['blink']:
            self.blink_status.config(text="✅ Blink Test - PASSED")
        else:
            self.blink_status.config(text="❌ Blink Test - PENDING")
            
        if self.liveness_tests_completed['head_movement']:
            self.head_status.config(text="✅ Head Movement Test - PASSED")
        else:
            self.head_status.config(text="❌ Head Movement Test - PENDING")
            
        if self.liveness_tests_completed['phone_detection']:
            self.phone_status.config(text="✅ Phone Detection Test - PASSED")
        else:
            self.phone_status.config(text="❌ Phone Detection Test - PENDING")
            
        # Enable capture button if all tests passed
        if all(self.liveness_tests_completed.values()):
            self.capture_btn.config(state=tk.NORMAL)
            self.status_label.config(text="✅ All liveness tests passed! Ready to capture face.")
        else:
            self.capture_btn.config(state=tk.DISABLED)
            
    def start_camera(self):
        """Start the camera"""
        try:
            if CameraManager.initialize_camera():
                self.camera_running = True
                self.start_camera_btn.config(state=tk.DISABLED)
                self.stop_camera_btn.config(state=tk.NORMAL)
                
                # Start camera thread
                self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
                self.camera_thread.start()
                
                self.status_label.config(text="Camera started! Use bypass buttons to complete liveness tests.")
            else:
                messagebox.showerror("Error", "Failed to initialize camera")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
            
    def stop_camera(self):
        """Stop the camera"""
        self.camera_running = False
        CameraManager.release_camera()
        
        self.start_camera_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.DISABLED)
        
        self.camera_label.config(image="", text="Camera stopped", bg="black", fg="white")
        self.status_label.config(text="Camera stopped")
        
    def camera_loop(self):
        """Camera display loop"""
        while self.camera_running:
            frame = CameraManager.get_frame()
            if frame is not None:
                self.current_frame = frame
                
                # Display frame
                display_frame = cv2.resize(frame, (640, 480))
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.camera_label.config(image=photo)
                self.camera_label.image = photo
                
            time.sleep(0.1)
            
    def capture_face(self):
        """Capture face for registration"""
        if self.current_frame is None:
            messagebox.showerror("Error", "No camera frame available")
            return
            
        if not all(self.liveness_tests_completed.values()):
            messagebox.showwarning("Warning", "Please complete all liveness tests first")
            return
        
        try:
            # Process for face recognition
            processed_face = preprocess_for_face_recognition(self.current_frame)
            if not processed_face or len(processed_face) == 0:
                messagebox.showerror("Error", "Failed to generate face encoding")
                return
            
            # Get the first face encoding
            self.face_encoding = processed_face[0]
            self.captured_frame = self.current_frame.copy()
            self.face_captured = True
            
            print(f"[DEBUG] Face encoding generated successfully, shape: {self.face_encoding.shape}")
            
            self.capture_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.NORMAL)
            
            self.status_label.config(text="✅ Face captured successfully! Ready to save user.")
            messagebox.showinfo("Success", "Face captured and encoded successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture face: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def save_user(self):
        """Save user with captured face data"""
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()
        
        if not name or not user_id:
            messagebox.showerror("Error", "Please enter both name and ID")
            return
        
        if not self.face_captured or self.face_encoding is None:
            messagebox.showerror("Error", "Please capture face first")
            return
        
        try:
            # Create user directory
            user_dir = f"data/registered_users/{user_id}_{name.replace(' ', '_')}"
            os.makedirs(user_dir, exist_ok=True)
            print(f"[DEBUG] Created user directory: {user_dir}")
            
            # Create user data
            user_data = {
                'name': name,
                'id': user_id,
                'encoding': self.face_encoding,
                'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'liveness_verified': True,
                'anti_spoof_passed': True,
                'encoding_version': 'face_recognition_1.3.0'
            }
            
            # Save encoding file
            encoding_file = os.path.join(user_dir, f"{user_id}_encoding.pkl")
            with open(encoding_file, 'wb') as f:
                pickle.dump(user_data, f)
            print(f"[DEBUG] Saved encoding to: {encoding_file}")
            
            # Save image files
            if self.captured_frame is not None:
                image_file = os.path.join(user_dir, f"{user_id}_photo.jpg")
                cv2.imwrite(image_file, self.captured_frame)
                print(f"[DEBUG] Saved photo to: {image_file}")
                
                face_crop_file = os.path.join(user_dir, f"{user_id}_face_crop.jpg")
                cv2.imwrite(face_crop_file, self.captured_frame)
                print(f"[DEBUG] Saved face crop to: {face_crop_file}")
            
            # Save metadata
            metadata_file = os.path.join(user_dir, "user_info.txt")
            with open(metadata_file, 'w') as f:
                f.write(f"Name: {name}\n")
                f.write(f"ID: {user_id}\n")
                f.write(f"Registration Date: {user_data['registration_date']}\n")
                f.write(f"Liveness Verified: {user_data['liveness_verified']}\n")
                f.write(f"Anti-Spoof Passed: {user_data['anti_spoof_passed']}\n")
                f.write(f"Face Encoding Shape: {self.face_encoding.shape}\n")
                f.write(f"Encoding Version: {user_data['encoding_version']}\n")
            print(f"[DEBUG] Saved metadata to: {metadata_file}")
            
            messagebox.showinfo("Success", 
                f"User {name} registered successfully!\n\n"
                f"Files saved:\n"
                f"• Encoding: {encoding_file}\n"
                f"• Photo: {user_id}_photo.jpg\n"
                f"• Face crop: {user_id}_face_crop.jpg\n"
                f"• Metadata: user_info.txt")
            
            # Reset form
            self.name_entry.delete(0, tk.END)
            self.id_entry.delete(0, tk.END)
            self.face_captured = False
            self.face_encoding = None
            self.captured_frame = None
            
            # Reset liveness tests
            self.liveness_tests_completed = {
                'blink': False,
                'head_movement': False,
                'phone_detection': False
            }
            self.update_liveness_status()
            
            self.save_btn.config(state=tk.DISABLED)
            self.status_label.config(text="User saved successfully. Ready for next registration.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save user: {str(e)}")
            import traceback
            traceback.print_exc()

def launch_debug_window():
    """Launch the debug liveness window"""
    root = tk.Tk()
    app = DebugLivenessWindow(root)
    root.mainloop()

if __name__ == "__main__":
    launch_debug_window()
