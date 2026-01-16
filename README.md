# AI Attendance Management System v1.0

## Overview
An automated attendance tracking solution utilizing facial recognition technology. This system eliminates manual roll calls and proxy attendance by verifying student identity through classroom cameras.

## Features
-   **Face Detection**: Recognizes individual faces from a group photo or video feed.
-   **Auto-Marking**: Updates the attendance database instantly upon recognition.
-   **Daily Reports**: Generates CSV/Excel sheets of daily attendance.
-   **User Registration**: Simple interface to enroll new students with face data.

## Technology Stack
-   **Vision**: OpenCV.
-   **Recognition**: Face_recognition library (Dlib).
-   **Storage**: SQLite / CSV.
-   **Language**: Python.

## Usage Flow
1.  **Enroll**: Capture reference limits for each student.
2.  **Monitor**: Camera scans the room at the start of class.
3.  **Identify**: System matches live faces against the database.
4.  **Log**: Attendance status is saved and exported.

## Quick Start
```bash
# Clone the repository
git clone "https://github.com/Nytrynox/AI-Attendance-System-1.0.git"

# Install requirements
pip install -r requirements.txt

# Run the system
python main.py
```

## License
MIT License

## Author
**Karthik Idikuda**
