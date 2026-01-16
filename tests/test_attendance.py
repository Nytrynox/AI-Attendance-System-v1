import unittest
import os
import csv
import datetime
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil

# Add the parent directory to the path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.attendance_manager import AttendanceManager
from src.user_manager import UserManager


class TestAttendanceManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.attendance_dir = os.path.join(self.test_dir, 'attendance')
        self.users_dir = os.path.join(self.test_dir, 'registered_users')
        
        # Create necessary directories
        os.makedirs(self.attendance_dir, exist_ok=True)
        os.makedirs(self.users_dir, exist_ok=True)
        
        # Create a sample user
        self.user_manager = UserManager(self.users_dir)
        self.user_id = "test_user_001"
        self.user_name = "Test User"
        
        # Create a mock embedding for the test user
        mock_embedding = [0.1] * 128  # Typical face embedding size
        self.user_manager.add_user(self.user_id, self.user_name, mock_embedding)
        
        # Initialize attendance manager
        self.attendance_manager = AttendanceManager(self.attendance_dir, self.user_manager)
        
        # Today's date for testing
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    def tearDown(self):
        # Clean up the test directory
        shutil.rmtree(self.test_dir)
    
    def test_attendance_file_creation(self):
        """Test if attendance file is created correctly"""
        # Ensure the attendance file doesn't exist
        attendance_file = os.path.join(self.attendance_dir, f"{self.today}.csv")
        if os.path.exists(attendance_file):
            os.remove(attendance_file)
            
        # Mark attendance (this should create the file)
        self.attendance_manager.mark_attendance(self.user_id)
        
        # Check if file exists
        self.assertTrue(os.path.exists(attendance_file))
        
        # Check file structure
        with open(attendance_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ['UserID', 'Name', 'Time', 'Status'])
    
    def test_mark_attendance(self):
        """Test marking attendance for a user"""
        # Mark attendance
        result = self.attendance_manager.mark_attendance(self.user_id)
        
        # Check return value
        self.assertTrue(result)
        
        # Verify attendance was recorded
        attendance_file = os.path.join(self.attendance_dir, f"{self.today}.csv")
        df = pd.read_csv(attendance_file)
        
        # Check if user is in the attendance record
        self.assertIn(self.user_id, df['UserID'].values)
        self.assertIn(self.user_name, df['Name'].values)
        self.assertEqual(df[df['UserID'] == self.user_id]['Status'].values[0], 'Present')
    
    def test_mark_attendance_unknown_user(self):
        """Test marking attendance for an unknown user"""
        # Try to mark attendance for unknown user
        result = self.attendance_manager.mark_attendance("unknown_user")
        
        # It should return False
        self.assertFalse(result)
        
        # Verify attendance was not recorded
        attendance_file = os.path.join(self.attendance_dir, f"{self.today}.csv")
        if os.path.exists(attendance_file):
            df = pd.read_csv(attendance_file)
            # Check user is not in records
            self.assertNotIn("unknown_user", df['UserID'].values)
    
    def test_duplicate_attendance(self):
        """Test marking attendance twice for the same user"""
        # Mark attendance first time
        self.attendance_manager.mark_attendance(self.user_id)
        
        # Get the record count
        attendance_file = os.path.join(self.attendance_dir, f"{self.today}.csv")
        df1 = pd.read_csv(attendance_file)
        count1 = len(df1[df1['UserID'] == self.user_id])
        
        # Mark attendance second time with default settings (duplicate handling)
        self.attendance_manager.mark_attendance(self.user_id)
        
        # Get the new record count
        df2 = pd.read_csv(attendance_file)
        count2 = len(df2[df2['UserID'] == self.user_id])
        
        # Default behavior: only one entry should be maintained per day
        self.assertEqual(count1, count2)
    
    def test_multiple_attendance_when_allowed(self):
        """Test multiple attendance entries when allowed"""
        # Create attendance manager that allows multiple entries
        attendance_manager = AttendanceManager(self.attendance_dir, self.user_manager, allow_multiple_entries=True)
        
        # Mark attendance first time
        attendance_manager.mark_attendance(self.user_id)
        
        # Wait briefly to ensure different timestamp
        import time
        time.sleep(0.1)
        
        # Mark attendance second time
        attendance_manager.mark_attendance(self.user_id)
        
        # Get the record count
        attendance_file = os.path.join(self.attendance_dir, f"{self.today}.csv")
        df = pd.read_csv(attendance_file)
        count = len(df[df['UserID'] == self.user_id])
        
        # Should have two entries
        self.assertEqual(count, 2)
    
    def test_get_attendance_report(self):
        """Test generating attendance report"""
        # Mark attendance for a user
        self.attendance_manager.mark_attendance(self.user_id)
        
        # Get attendance report for today
        report = self.attendance_manager.get_attendance_report(self.today)
        
        # Verify report structure
        self.assertIsInstance(report, pd.DataFrame)
        self.assertIn('UserID', report.columns)
        self.assertIn('Name', report.columns)
        self.assertIn('Time', report.columns)
        self.assertIn('Status', report.columns)
        
        # Verify user is in the report
        self.assertIn(self.user_id, report['UserID'].values)
    
    def test_get_user_attendance_history(self):
        """Test getting attendance history for a specific user"""
        # Mark attendance
        self.attendance_manager.mark_attendance(self.user_id)
        
        # Get user history
        history = self.attendance_manager.get_user_attendance_history(self.user_id)
        
        # Verify history structure
        self.assertIsInstance(history, pd.DataFrame)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history['UserID'].iloc[0], self.user_id)
    
    @patch('src.attendance_manager.datetime')
    def test_mark_absence(self, mock_datetime):
        """Test marking a user as absent"""
        # Mock the datetime to use a specific date
        mock_date = datetime.datetime(2023, 1, 10)
        mock_datetime.datetime.now.return_value = mock_date
        mock_datetime.datetime.strftime = datetime.datetime.strftime
        
        test_date = mock_date.strftime("%Y-%m-%d")
        
        # Mark user as absent
        self.attendance_manager.mark_absence(self.user_id)
        
        # Check if absence was recorded
        attendance_file = os.path.join(self.attendance_dir, f"{test_date}.csv")
        df = pd.read_csv(attendance_file)
        
        # Verify the absence status
        user_records = df[df['UserID'] == self.user_id]
        self.assertEqual(user_records['Status'].values[0], 'Absent')
    
    def test_export_monthly_report(self):
        """Test exporting a monthly attendance report"""
        # Mark attendance
        self.attendance_manager.mark_attendance(self.user_id)
        
        # Get current month and year
        current_month = datetime.datetime.now().month
        current_year = datetime.datetime.now().year
        
        # Export monthly report
        export_path = os.path.join(self.test_dir, 'monthly_report.csv')
        result = self.attendance_manager.export_monthly_report(
            current_year, current_month, export_path
        )
        
        # Verify export was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # Check report content
        df = pd.read_csv(export_path)
        self.assertIn(self.user_id, df['UserID'].values)
    
    def test_get_attendance_stats(self):
        """Test getting attendance statistics"""
        # Mark attendance for multiple days (mock)
        with patch('os.path.exists', return_value=True):
            with patch('pandas.read_csv') as mock_read_csv:
                # Create mock data for 30 days, with user present for 20 days
                data = []
                for i in range(1, 31):
                    date = f"2023-01-{i:02d}"
                    status = 'Present' if i <= 20 else 'Absent'
                    data.append({
                        'Date': date,
                        'UserID': self.user_id,
                        'Name': self.user_name,
                        'Status': status
                    })
                
                mock_df = pd.DataFrame(data)
                mock_read_csv.return_value = mock_df
                
                # Get attendance stats
                stats = self.attendance_manager.get_attendance_stats(
                    self.user_id, 
                    start_date="2023-01-01", 
                    end_date="2023-01-30"
                )
                
                # Verify stats
                self.assertEqual(stats['total_days'], 30)
                self.assertEqual(stats['present_days'], 20)
                self.assertEqual(stats['absent_days'], 10)
                self.assertAlmostEqual(stats['attendance_percentage'], 66.67, places=2)


if __name__ == '__main__':
    unittest.main()