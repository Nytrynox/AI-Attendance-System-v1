#!/usr/bin/env python3
"""
DroidCam Connection Diagnostic Tool
---------------------------------
This tool helps diagnose DroidCam connection issues.
"""

import requests
import cv2
import socket
import time
import sys
import os

def test_network_connectivity(ip="192.168.29.90", port=4747):
    """Test basic network connectivity to DroidCam"""
    print(f"🔍 Testing network connectivity to {ip}:{port}")
    
    try:
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connection successful to {ip}:{port}")
            return True
        else:
            print(f"❌ Cannot connect to {ip}:{port}")
            print("   📱 Make sure DroidCam app is running on your phone")
            print("   🌐 Check if both devices are on the same WiFi network")
            return False
            
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def test_http_response(ip="192.168.29.90", port=4747):
    """Test HTTP response from DroidCam"""
    url = f"http://{ip}:{port}/video"
    print(f"🌐 Testing HTTP response from {url}")
    
    try:
        response = requests.get(url, timeout=5, stream=True)
        print(f"📡 HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ DroidCam HTTP server is responding correctly")
            return True
        else:
            print(f"❌ DroidCam returned HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - DroidCam not responding")
        print("   📱 Restart DroidCam app on your phone")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("   📱 Check if DroidCam app is actually running")
        print("   🌐 Verify IP address matches what's shown in DroidCam app")
        return False
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")
        return False

def test_opencv_connection(ip="192.168.29.90", port=4747):
    """Test OpenCV VideoCapture connection"""
    url = f"http://{ip}:{port}/video"
    print(f"📹 Testing OpenCV VideoCapture connection to {url}")
    
    try:
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            print("❌ OpenCV failed to open video stream")
            print("   🔧 Try restarting DroidCam app")
            return False
        
        # Try to read a frame
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            print(f"✅ Successfully received video frame: {frame.shape}")
            return True
        else:
            print("❌ Failed to read video frame from DroidCam")
            print("   📱 Check if camera permission is granted in DroidCam app")
            return False
            
    except Exception as e:
        print(f"❌ OpenCV test failed: {e}")
        return False

def scan_local_network():
    """Scan local network for DroidCam devices"""
    print("🔍 Scanning local network for DroidCam devices...")
    
    # Get local IP range
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"💻 Your computer IP: {local_ip}")
    
    # Extract network prefix (assumes /24 subnet)
    ip_parts = local_ip.split('.')
    network = '.'.join(ip_parts[:3])
    
    found_devices = []
    
    # Scan common DroidCam IPs
    for i in range(1, 255):
        test_ip = f"{network}.{i}"
        try:
            # Quick TCP test to port 4747
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((test_ip, 4747))
            sock.close()
            
            if result == 0:
                print(f"🎯 Found potential DroidCam at {test_ip}:4747")
                found_devices.append(test_ip)
                
        except:
            pass
    
    if found_devices:
        print(f"📱 Found {len(found_devices)} potential DroidCam device(s):")
        for device in found_devices:
            print(f"   • {device}:4747")
    else:
        print("❌ No DroidCam devices found on local network")
        print("   📱 Make sure DroidCam app is running")
        print("   🌐 Check WiFi connection")

def provide_solutions():
    """Provide troubleshooting solutions"""
    print("\n🛠️  TROUBLESHOOTING SOLUTIONS:")
    print("=" * 50)
    
    print("\n1. 📱 Check DroidCam App:")
    print("   • Open DroidCam app on your phone")
    print("   • Ensure it shows 'Ready' status")
    print("   • Note the IP address displayed")
    print("   • Make sure 'WiFi IP' mode is selected")
    
    print("\n2. 🌐 Network Settings:")
    print("   • Both devices must be on same WiFi network")
    print("   • Disable mobile data on phone")
    print("   • Try restarting WiFi on both devices")
    
    print("\n3. 🔧 DroidCam Settings:")
    print("   • Try different video quality in DroidCam")
    print("   • Enable 'Keep Screen On' in DroidCam")
    print("   • Grant camera permissions to DroidCam")
    
    print("\n4. 🛡️ Firewall/Security:")
    print("   • Temporarily disable Windows Firewall")
    print("   • Check if antivirus is blocking connection")
    print("   • Disable phone's firewall if any")
    
    print("\n5. 🔄 Alternative Solutions:")
    print("   • Try USB connection instead of WiFi")
    print("   • Restart both DroidCam app and computer")
    print("   • Try different port if available")

def main():
    """Main diagnostic function"""
    print("🔧 DroidCam Connection Diagnostic Tool")
    print("=" * 40)
    
    # Get IP from user or use default
    ip = input("Enter DroidCam IP address (press Enter for 192.168.29.90): ").strip()
    if not ip:
        ip = "192.168.29.90"
    
    print(f"\n🎯 Testing DroidCam connection to: {ip}:4747")
    print("-" * 40)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_network_connectivity(ip):
        tests_passed += 1
    
    if test_http_response(ip):
        tests_passed += 1
        
    if test_opencv_connection(ip):
        tests_passed += 1
    
    # Summary
    print(f"\n📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ DroidCam should work with the face attendance system!")
    elif tests_passed == 0:
        print("❌ DroidCam is not accessible. Check solutions below.")
        scan_local_network()
    else:
        print("⚠️  Partial connectivity. Some issues detected.")
    
    provide_solutions()
    
    print(f"\n💡 To update the IP in main.py, change line 266:")
    print(f'   mobile_url = "http://{ip}:4747/video"')

if __name__ == "__main__":
    main()
