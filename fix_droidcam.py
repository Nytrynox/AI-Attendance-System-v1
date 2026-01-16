#!/usr/bin/env python3
"""
Quick DroidCam Connection Test and Fix
"""

import cv2
import requests
import time

def test_droidcam_urls():
    """Test different DroidCam URL formats"""
    base_ip = "192.168.29.90"
    
    # Different URL formats to try
    urls_to_test = [
        f"http://{base_ip}:4747/video",           # Standard DroidCam
        f"http://{base_ip}:4747/mjpegfeed",       # Alternative format
        f"http://{base_ip}:4747/cam/1/stream",    # Alternative format
        f"http://{base_ip}:4747/",                # Base URL
    ]
    
    print("🔍 Testing different DroidCam URL formats...")
    
    for url in urls_to_test:
        print(f"\n📡 Testing: {url}")
        
        # Test HTTP response
        try:
            response = requests.get(url, timeout=3)
            print(f"   HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                # Test OpenCV
                try:
                    cap = cv2.VideoCapture(url)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            print(f"   ✅ SUCCESS! Frame shape: {frame.shape}")
                            cap.release()
                            return url
                        else:
                            print("   ❌ No frames received")
                    else:
                        print("   ❌ OpenCV failed to open")
                    cap.release()
                except Exception as e:
                    print(f"   ❌ OpenCV error: {e}")
            
        except Exception as e:
            print(f"   ❌ HTTP error: {e}")
    
    return None

def update_main_py_with_working_url(working_url):
    """Update main.py with the working DroidCam URL"""
    print(f"\n📝 Updating main.py with working URL: {working_url}")
    
    # Read main.py
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Find and replace the mobile_url line
        import re
        pattern = r'mobile_url = "http://[^"]*"'
        replacement = f'mobile_url = "{working_url}"'
        
        new_content = re.sub(pattern, replacement, content)
        
        # Write back to file
        with open('main.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Successfully updated main.py!")
        print(f"   Changed mobile_url to: {working_url}")
        
    except Exception as e:
        print(f"❌ Failed to update main.py: {e}")

def main():
    print("🔧 DroidCam URL Format Tester")
    print("=" * 30)
    
    working_url = test_droidcam_urls()
    
    if working_url:
        print(f"\n🎉 Found working DroidCam URL: {working_url}")
        update_main_py_with_working_url(working_url)
        print("\n🚀 Now try running: python main.py --dual-camera")
    else:
        print("\n❌ No working DroidCam URLs found")
        print("\n🛠️ Troubleshooting steps:")
        print("1. Make sure DroidCam app is running on your phone")
        print("2. Check if the IP address 192.168.29.90 is correct")
        print("3. Both devices must be on the same WiFi network")
        print("4. Try restarting the DroidCam app")
        print("5. Check phone's firewall settings")

if __name__ == "__main__":
    main()
