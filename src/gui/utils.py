# src/gui/utils.py

import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import os
import pickle
from sklearn.preprocessing import LabelEncoder
from tkinter import filedialog
from tkinter import messagebox
import matplotlib.pyplot as plt


def resize_image(image, width=500, height=500):
    """
    Resize the input image to a desired width and height while maintaining aspect ratio.
    Args:
        image (numpy.ndarray): Input image in BGR format (OpenCV).
        width (int): Desired width for resizing.
        height (int): Desired height for resizing.
    Returns:
        resized_image (numpy.ndarray): Resized image.
    """
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def preprocess_for_face_recognition(image, face_encoding_model):
    """
    Preprocess an image for face recognition.
    Args:
        image (numpy.ndarray): Input image in BGR format (OpenCV).
        face_encoding_model (keras.Model): Pre-trained face encoding model.
    Returns:
        face_encoding (numpy.ndarray): The encoded face representation.
    """
    face = detect_face(image)
    if face is not None:
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        face = Image.fromarray(face)
        face = face.resize((160, 160))
        face_array = np.asarray(face)
        face_encoding = face_encoding_model.predict(np.expand_dims(face_array, axis=0))
        return face_encoding
    else:
        return None


def detect_face(image):
    """
    Detect a face in the image using OpenCV's Haar Cascade classifier.
    Args:
        image (numpy.ndarray): Input image in BGR format (OpenCV).
    Returns:
        face (numpy.ndarray): Cropped face region.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        face = image[y:y+h, x:x+w]
        return face
    return None


def save_registered_user(user_name, user_id, user_face_encoding):
    """
    Save a registered user's name, ID, and face encoding to a file.
    Args:
        user_name (str): Name of the user.
        user_id (str): ID of the user.
        user_face_encoding (numpy.ndarray): Face encoding of the user.
    """
    registered_users_path = "data/registered_users/"
    if not os.path.exists(registered_users_path):
        os.makedirs(registered_users_path)

    user_data = {
        'name': user_name,
        'id': user_id,
        'face_encoding': user_face_encoding
    }

    file_name = f"{user_id}_{user_name}.pkl"
    file_path = os.path.join(registered_users_path, file_name)
    with open(file_path, 'wb') as f:
        pickle.dump(user_data, f)


def load_registered_users():
    """
    Load all registered users from the saved files.
    Returns:
        registered_users (dict): Dictionary containing user_id as keys and user_name as values.
    """
    registered_users_path = "data/registered_users/"
    registered_users = {}

    for file_name in os.listdir(registered_users_path):
        if file_name.endswith(".pkl"):
            file_path = os.path.join(registered_users_path, file_name)
            with open(file_path, 'rb') as f:
                user_data = pickle.load(f)
                registered_users[user_data['id']] = {
                    'name': user_data['name'],
                    'face_encoding': user_data['face_encoding']
                }

    return registered_users


def save_attendance(user_id, user_name, timestamp):
    """
    Save attendance information to a CSV file.
    Args:
        user_id (str): ID of the user.
        user_name (str): Name of the user.
        timestamp (str): Date and time of the attendance.
    """
    attendance_file = "data/attendance/attendance_log.csv"
    if not os.path.exists(attendance_file):
        with open(attendance_file, 'w') as f:
            f.write("user_id,user_name,timestamp\n")

    with open(attendance_file, 'a') as f:
        f.write(f"{user_id},{user_name},{timestamp}\n")


def show_image(image):
    """
    Show an image using Matplotlib.
    Args:
        image (numpy.ndarray): The image to be displayed.
    """
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.show()


def select_image_file():
    """
    Open a file dialog to select an image file.
    Returns:
        image (PIL.Image): The selected image as a PIL Image.
    """
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
    if file_path:
        image = Image.open(file_path)
        return image
    return None


def show_error_message(message):
    """
    Show an error message box.
    Args:
        message (str): The message to be displayed in the error box.
    """
    messagebox.showerror("Error", message)


def show_info_message(message):
    """
    Show an info message box.
    Args:
        message (str): The message to be displayed in the info box.
    """
    messagebox.showinfo("Information", message)


def encode_labels(user_names):
    """
    Encode user names into numerical labels.
    Args:
        user_names (list): List of user names to encode.
    Returns:
        label_encoder (LabelEncoder): Trained LabelEncoder.
        encoded_labels (list): List of numerical labels corresponding to the user names.
    """
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(user_names)
    return label_encoder, encoded_labels
