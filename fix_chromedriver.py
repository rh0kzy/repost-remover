#!/usr/bin/env python3
"""
Fix ChromeDriver issues and setup script
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def clear_webdriver_cache():
    """Clear WebDriver manager cache to fix version issues."""
    print("🧹 Clearing WebDriver cache...")
    
    # Common cache locations
    cache_paths = [
        Path.home() / ".wdm",
        Path.home() / "AppData" / "Local" / ".wdm",
        Path(os.environ.get("USERPROFILE", "")) / ".wdm" if os.environ.get("USERPROFILE") else None
    ]
    
    for cache_path in cache_paths:
        if cache_path and cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                print(f"✅ Cleared cache: {cache_path}")
            except Exception as e:
                print(f"⚠️  Could not clear {cache_path}: {e}")


def install_specific_chromedriver():
    """Install specific ChromeDriver version."""
    print("🔧 Installing specific ChromeDriver...")
    
    try:
        # Install specific webdriver-manager version
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "webdriver-manager==4.0.1", "--force-reinstall"
        ])
        print("✅ WebDriver manager reinstalled")
        
        return True
    except Exception as e:
        print(f"❌ Failed to install ChromeDriver: {e}")
        return False


def test_chrome_installation():
    """Test if Chrome is properly installed."""
    print("🧪 Testing Chrome installation...")
    
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        # Check common Chrome installation paths
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe")
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                print(f"✅ Found Chrome at: {path}")
                return True
        
        print("❌ Chrome not found in common locations")
        print("💡 Please install Google Chrome from: https://www.google.com/chrome/")
        return False
    
    else:
        print("ℹ️  Non-Windows system, skipping Chrome path check")
        return True


def create_browser_test():
    """Create a simple browser test."""
    test_content = '''#!/usr/bin/env python3
"""
Simple browser test to verify ChromeDriver works
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys

def test_browser():
    """Test basic browser functionality."""
    print("🧪 Testing browser setup...")
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")
        
        print("📦 Setting up ChromeDriver...")
        
        # Try multiple approaches
        driver = None
        
        # Approach 1: Use WebDriver Manager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Method 1 (WebDriver Manager) successful")
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
            
            # Approach 2: Use system Chrome
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("✅ Method 2 (System Chrome) successful")
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                print("❌ All methods failed!")
                return False
        
        # Test basic functionality
        print("🌐 Testing navigation...")
        driver.get("https://www.google.com")
        
        if "Google" in driver.title:
            print("✅ Navigation test passed")
            success = True
        else:
            print("❌ Navigation test failed")
            success = False
        
        driver.quit()
        return success
        
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False

if __name__ == "__main__":
    success = test_browser()
    if success:
        print("🎉 Browser test passed! ChromeDriver is working.")
    else:
        print("❌ Browser test failed. Please check the issues above.")
    sys.exit(0 if success else 1)
'''
    
    with open("browser_test.py", "w") as f:
        f.write(test_content)
    
    print("✅ Created browser_test.py")


def main():
    """Main fix process."""
    print("🔧 TikTok Repost Remover - ChromeDriver Fix")
    print("=" * 50)
    
    # Test Chrome installation
    if not test_chrome_installation():
        print("\n❌ Please install Google Chrome first!")
        return False
    
    # Clear cache
    clear_webdriver_cache()
    
    # Reinstall webdriver manager
    if not install_specific_chromedriver():
        return False
    
    # Create test script
    create_browser_test()
    
    print("\n" + "=" * 50)
    print("🎉 Fix process completed!")
    print("\n📋 Next steps:")
    print("1. Test the fix: python browser_test.py")
    print("2. If test passes, try: python main.py --dry-run")
    print("3. If still fails, try: python main.py --no-headless --dry-run")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)