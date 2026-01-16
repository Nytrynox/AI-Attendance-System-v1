# src/gui/add_user_window.py

import tkinter as tk
from tkinter import messagebox
import cv2
import os
import pickle
from src.utils.image_utils import resize_image, preprocess_for_face_recognition
from src.utils.data_utils import save_attendance


from datetime import datetime
import threading
import time


class AddUserWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Add New User")
        self.master.geometry("500x400")

        # Main frame
        main_frame = tk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # User info frame
        info_frame = tk.LabelFrame(main_frame, text="User Information", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.name_entry = tk.Entry(info_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=(0, 20))

        tk.Label(info_frame, text="ID:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.id_entry = tk.Entry(info_frame, width=30)
        self.id_entry.grid(row=1, column=1, padx=(0, 20), pady=(10, 0))

        # Camera frame
        camera_frame = tk.LabelFrame(main_frame, text="Photo Capture", padx=10, pady=10)
        camera_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Status display
        self.status_text = tk.Text(camera_frame, height=8, width=60, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Button frame
        button_frame = tk.Frame(camera_frame)
        button_frame.pack(fill=tk.X)

        self.capture_button = tk.Button(button_frame, text="Capture Photo", command=self.capture_photo, bg="lightblue")
        self.capture_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = tk.Button(button_frame, text="Save User", command=self.save_user, state=tk.DISABLED, bg="lightgreen")
        self.save_button.pack(side=tk.RIGHT)

        # Close button
        close_frame = tk.Frame(main_frame)
        close_frame.pack(fill=tk.X)
        
        close_button = tk.Button(close_frame, text="Close", command=self.close_window, bg="lightcoral")
        close_button.pack(side=tk.RIGHT)

        # Variables
        self.face_captured = False
        self.user_data = None
        self.face_encoding = None
        self.captured_frame = None

        self.update_status("Ready to capture photo. Enter name and ID, then click 'Capture Photo'.")

    def update_status(self, message):
        """Update the status display"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def capture_photo(self):
        """Capture a photo using the camera"""
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()

        if not name or not user_id:
            messagebox.showerror("Error", "Please enter both name and ID.")
            return

        self.update_status("Starting camera...")
        self.capture_button.config(state=tk.DISABLED, text="Capturing...")

        # Run camera capture in a separate thread to avoid blocking UI
        threading.Thread(target=self._capture_with_camera, args=(name, user_id), daemon=True).start()

    def _capture_with_camera(self, name, user_id):
        """Camera capture logic running in separate thread"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.master.after(0, lambda: self.update_status("ERROR: Unable to access webcam!"))
                self.master.after(0, lambda: self.capture_button.config(state=tk.NORMAL, text="Capture Photo"))
                return

            self.master.after(0, lambda: self.update_status("Camera started. Please position your face in front of the camera..."))
            
            capture_count = 0
            max_attempts = 100  # 10 seconds at ~10 FPS
            
            while capture_count < max_attempts:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check for face detection
                face_encodings = preprocess_for_face_recognition(frame)
                
                if face_encodings:
                    # Face detected - capture it
                    self.face_encoding = face_encodings[0]
                    self.captured_frame = frame.copy()
                    self.face_captured = True
                    
                    self.master.after(0, lambda: self.update_status("✓ Face detected and captured successfully!"))
                    self.master.after(0, lambda: self._save_photo(name, user_id))
                    break
                else:
                    if capture_count % 20 == 0:  # Update status every 2 seconds
                        self.master.after(0, lambda: self.update_status("Looking for face... Please look at the camera"))
                
                capture_count += 1
                time.sleep(0.1)  # 10 FPS
            
            cap.release()
            
            if not self.face_captured:
                self.master.after(0, lambda: self.update_status("❌ No face detected. Please try again."))
                self.master.after(0, lambda: self.capture_button.config(state=tk.NORMAL, text="Capture Photo"))
        except Exception as e:
            error_msg = f"❌ Camera error: {str(e)}"
            self.master.after(0, lambda: self.update_status(error_msg))
            self.master.after(0, lambda: self.capture_button.config(state=tk.NORMAL, text="Capture Photo"))

    def _save_photo(self, name, user_id):
        """Save the captured photo and user data"""
        try:
            if self.captured_frame is None:
                self.update_status("❌ No photo to save")
                return

            # Create user directory
            user_dir = os.path.join("data/registered_users", user_id)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)

            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = os.path.join(user_dir, f"{user_id}_{timestamp}.jpg")
            
            resized_frame = resize_image(self.captured_frame)
            cv2.imwrite(image_path, resized_frame)

            # Save face encoding
            user_info = {
                'id': user_id,
                'name': name,
                'encoding': self.face_encoding,
                'image_path': image_path,
                'timestamp': timestamp
            }

            encoding_file = os.path.join(user_dir, f"{user_id}_encoding.pkl")
            with open(encoding_file, "wb") as f:
                pickle.dump(user_info, f)

            # Trigger reload notification for real-time updates
            try:
                from src.utils.data_utils import trigger_user_reload_notification
                trigger_user_reload_notification()
                print("[INFO] Triggered user data reload notification")
            except Exception as e:
                print(f"[WARNING] Could not trigger reload notification: {e}")

            self.user_data = user_info
            self.update_status(f"✓ Photo saved successfully for {name} (ID: {user_id})")
            self.save_button.config(state=tk.NORMAL)
            self.capture_button.config(state=tk.NORMAL, text="Capture Photo")

        except Exception as e:
            self.update_status(f"❌ Failed to save photo: {str(e)}")
            self.capture_button.config(state=tk.NORMAL, text="Capture Photo")

    def save_user(self):
        """Save the user's information to the system"""
        if self.user_data:
            try:
                save_attendance(self.user_data['id'], self.user_data['name'])
                self.update_status("✓ User registration completed successfully!")
                messagebox.showinfo("Success", f"User {self.user_data['name']} has been registered successfully!")
            except Exception as e:
                self.update_status(f"❌ Failed to save user data: {str(e)}")
                messagebox.showerror("Error", f"Failed to save user data: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No user data to save. Please capture a photo first.")

    def close_window(self):
        """Close the window"""
        self.master.quit()
        self.master.destroy()


def launch_add_user_window():
    root = tk.Tk()
    AddUserWindow(root)
    root.mainloop()


if __name__ == "__main__":
    launch_add_user_window()
