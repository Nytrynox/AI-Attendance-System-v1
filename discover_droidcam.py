#!/usr/bin/env python3
"""
DroidCam Auto-Discovery and Setup Tool
"""

import socket
import requests
import cv2
import threading
import time

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Connect to a dummy address to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except:
        return "Unknown"

def scan_for_droidcam(network_prefix, max_threads=50):
    """Scan network for DroidCam devices"""
    print(f"🔍 Scanning network {network_prefix}.1-254 for DroidCam devices...")
    
    found_devices = []
    threads = []
    lock = threading.Lock()
    
    def check_ip(ip):
        try:
            # Quick check for port 4747
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, 4747))
            sock.close()
            
            if result == 0:
                # Verify it's actually DroidCam
                try:
                    response = requests.get(f"http://{ip}:4747/", timeout=1)
                    if response.status_code == 200:
                        with lock:
                            found_devices.append(ip)
                            print(f"🎯 Found DroidCam at {ip}:4747")
                except:
                    pass
        except:
            pass
    
    # Create threads for parallel scanning
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        thread = threading.Thread(target=check_ip, args=(ip,))
        threads.append(thread)
        thread.start()
        
        # Limit concurrent threads
        if len(threads) >= max_threads:
            for t in threads:
                t.join()
            threads = []
    
    # Wait for remaining threads
    for thread in threads:
        thread.join()
    
    return found_devices

def test_droidcam_connection(ip):
    """Test DroidCam connection thoroughly"""
    print(f"\n🧪 Testing DroidCam connection to {ip}:4747")
    
    url = f"http://{ip}:4747/video"
    
    # Test 1: HTTP connectivity
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ HTTP Status: {response.status_code}")
        http_ok = response.status_code == 200
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        http_ok = False
    
    # Test 2: OpenCV connection
    try:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ OpenCV test passed: Frame {frame.shape}")
                cap.release()
                opencv_ok = True
            else:
                print("❌ OpenCV: No frames received")
                cap.release()
                opencv_ok = False
        else:
            print("❌ OpenCV: Failed to open video stream")
            opencv_ok = False
    except Exception as e:
        print(f"❌ OpenCV test failed: {e}")
        opencv_ok = False
    
    return http_ok and opencv_ok

def update_main_py(ip):
    """Update main.py with the correct DroidCam IP"""
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Find the line with mobile_url and replace IP
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'mobile_url = "http://' in line and ':4747/video"' in line:
                lines[i] = f'            mobile_url = "http://{ip}:4747/video"'
                print(f"📝 Updated line {i+1}: {lines[i].strip()}")
                break
        
        # Write back
        with open('main.py', 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Successfully updated main.py with IP: {ip}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update main.py: {e}")
        return False

def main():
    print("🔧 DroidCam Auto-Discovery Tool")
    print("=" * 35)
    
    # Get local network info
    local_ip = get_local_ip()
    print(f"💻 Your computer IP: {local_ip}")
    
    if local_ip == "Unknown":
        print("❌ Could not determine local IP address")
        return
    
    # Extract network prefix
    network_parts = local_ip.split('.')
    network_prefix = '.'.join(network_parts[:3])
    print(f"🌐 Scanning network: {network_prefix}.0/24")
    
    # Scan for DroidCam devices
    found_devices = scan_for_droidcam(network_prefix)
    
    if not found_devices:
        print("\n❌ No DroidCam devices found on your network")
        print("\n🔧 Setup Instructions:")
        print("=" * 25)
        print("1. 📱 Install DroidCam app on your phone")
        print("2. 🌐 Connect phone to same WiFi as computer")
        print("3. 📱 Open DroidCam app (it should show 'Ready')")
        print("4. 📋 Note the IP address shown in the app")
        print("5. 🔄 Run this tool again")
        print("\n💡 Alternative: Try USB connection in DroidCam app")
        return
    
    print(f"\n🎉 Found {len(found_devices)} DroidCam device(s)!")
    
    # Test each device
    working_ip = None
    for ip in found_devices:
        if test_droidcam_connection(ip):
            working_ip = ip
            break
    
    if working_ip:
        print(f"\n✅ DroidCam is working at: {working_ip}:4747")
        
        # Update main.py
        if update_main_py(working_ip):
            print("\n🚀 Setup complete! Now run:")
            print("   python main.py --dual-camera")
        
    else:
        print("\n⚠️  Found DroidCam devices but connection tests failed")
        print("Try restarting DroidCam app and run this tool again")

if __name__ == "__main__":
    main()
