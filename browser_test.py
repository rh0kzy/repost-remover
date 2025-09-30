#!/usr/bin/env python3
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
    print("Testing browser setup...")
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")
        
        print("Setting up ChromeDriver...")
        
        # Try multiple approaches
        driver = None
        
        # Approach 1: Use WebDriver Manager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Method 1 (WebDriver Manager) successful")
        except Exception as e:
            print(f"Method 1 failed: {e}")
            
            # Approach 2: Use system Chrome
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("Method 2 (System Chrome) successful")
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                print("All methods failed!")
                return False
        
        # Test basic functionality
        print("Testing navigation...")
        driver.get("https://www.google.com")
        
        if "Google" in driver.title:
            print("Navigation test passed")
            success = True
        else:
            print("Navigation test failed")
            success = False
        
        driver.quit()
        return success
        
    except Exception as e:
        print(f"Browser test failed: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False

if __name__ == "__main__":
    success = test_browser()
    if success:
        print("Browser test passed! ChromeDriver is working.")
    else:
        print("Browser test failed. Please check the issues above.")
    sys.exit(0 if success else 1)
