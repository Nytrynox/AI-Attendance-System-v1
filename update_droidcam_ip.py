#!/usr/bin/env python3
"""
Manual DroidCam IP Update Tool
"""

def update_droidcam_ip():
    """Update DroidCam IP in main.py"""
    print("🔧 Manual DroidCam IP Update")
    print("=" * 30)
    
    current_ip = "192.168.29.90"  # Current IP in main.py
    print(f"📋 Current IP in main.py: {current_ip}")
    
    new_ip = input("📱 Enter the IP address shown in DroidCam app: ").strip()
    
    if not new_ip:
        print("❌ No IP address provided")
        return
    
    # Validate IP format
    try:
        parts = new_ip.split('.')
        if len(parts) != 4 or not all(0 <= int(part) <= 255 for part in parts):
            raise ValueError("Invalid IP format")
    except:
        print("❌ Invalid IP address format")
        return
    
    # Update main.py
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Replace the IP address
        old_url = f'mobile_url = "http://{current_ip}:4747/video"'
        new_url = f'mobile_url = "http://{new_ip}:4747/video"'
        
        if old_url in content:
            new_content = content.replace(old_url, new_url)
            
            with open('main.py', 'w') as f:
                f.write(new_content)
            
            print(f"✅ Successfully updated main.py!")
            print(f"   Changed: {current_ip} → {new_ip}")
            print("\n🚀 Now run: python main.py --dual-camera")
        else:
            print("❌ Could not find DroidCam URL in main.py")
            print(f"   Looking for: {old_url}")
        
    except Exception as e:
        print(f"❌ Error updating main.py: {e}")

if __name__ == "__main__":
    update_droidcam_ip()
