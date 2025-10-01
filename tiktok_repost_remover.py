import os
import time
import logging
import requests
from typing import List, Dict, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import imagehash
import cv2
import numpy as np
from tqdm import tqdm
import json
from datetime import datetime
from urllib.parse import urljoin
import config


class TikTokRepostRemover:
    """
    A comprehensive tool for detecting and removing TikTok reposts.
    
    Reposts are videos that you've shared from other creators to your own profile.
    They appear with a "repost" label and are found in the "Repost" tab on your profile.
    """
    
    def __init__(self, similarity_threshold: float = None, batch_size: int = None, headless: bool = None):
        """
        Initialize the TikTok Repost Remover.
        
        Args:
            similarity_threshold: Threshold for considering videos as duplicates (0.0-1.0)
            batch_size: Number of videos to process at once
            headless: Whether to run browser in headless mode
        """
        self.similarity_threshold = similarity_threshold or config.SIMILARITY_THRESHOLD
        self.batch_size = batch_size or config.BATCH_SIZE
        self.headless = headless if headless is not None else config.HEADLESS_BROWSER
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize browser
        self.driver = None
        self.wait = None
        
        # Storage for video data
        self.videos = []
        self.video_hashes = {}
        self.deleted_videos = []
        
        self.logger.info("TikTok Repost Remover initialized")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_browser(self):
        """Setup Chrome browser with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize webdriver with better error handling
        try:
            # Try system Chrome first (more reliable)
            self.logger.info("Attempting to use system Chrome...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("System Chrome initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"System Chrome failed: {e}")
            # Fallback: try ChromeDriverManager
            try:
                self.logger.info("Trying ChromeDriverManager fallback...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.logger.info("ChromeDriverManager fallback successful")
            except Exception as e2:
                self.logger.error(f"ChromeDriverManager fallback failed: {e2}")
                raise Exception(f"Could not initialize Chrome browser. Please ensure Chrome is installed and try running with --no-headless to debug. Errors: System Chrome: {e}, ChromeDriverManager: {e2}")
        
        self.wait = WebDriverWait(self.driver, config.BROWSER_TIMEOUT)
        self.logger.info("Browser initialized successfully")
    
    def login(self, username: str, password: str, manual_verification: bool = False) -> bool:
        """
        Login to TikTok account.
        
        Args:
            username: TikTok username or email
            password: TikTok password
            manual_verification: If True, wait for user to complete verification manually
            
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.driver:
            self._setup_browser()
        
        try:
            self.logger.info("Attempting to login to TikTok")
            self.driver.get(f"{config.TIKTOK_BASE_URL}/login")
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # Try different login methods
            login_success = self._try_login_methods(username, password, manual_verification)
            
            if login_success:
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False
    
    def _try_login_methods(self, username: str, password: str, manual_verification: bool = False) -> bool:
        """Try different login methods."""
        try:
            # First, try to find the login form
            self.logger.info("Looking for login form...")
            
            # Wait a bit for the page to load completely
            time.sleep(3)
            
            # Look for "Use phone / email / username" option
            login_options = [
                "//div[contains(text(), 'Use phone')]",
                "//div[contains(text(), 'Use email')]", 
                "//div[contains(text(), 'phone')]",
                "//a[contains(@href, 'login')]",
                "//button[contains(text(), 'Log in')]"
            ]
            
            # Try to click on login option
            for option in login_options:
                try:
                    element = self.driver.find_element(By.XPATH, option)
                    element.click()
                    self.logger.info(f"Clicked login option: {option}")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Method 1: Look for email/username input
            username_selectors = [
                "input[placeholder*='email']",
                "input[placeholder*='Email']",
                "input[placeholder*='Username']",
                "input[placeholder*='username']",
                "input[name='username']",
                "input[type='email']",
                "input[type='text']",
                "//input[contains(@placeholder, 'email')]",
                "//input[contains(@placeholder, 'Email')]",
                "//input[contains(@placeholder, 'phone')]",
                "//input[contains(@placeholder, 'Phone')]"
            ]
            
            password_selectors = [
                "input[placeholder*='Password']",
                "input[placeholder*='password']",
                "input[name='password']",
                "input[type='password']",
                "//input[contains(@placeholder, 'password')]",
                "//input[contains(@placeholder, 'Password')]"
            ]
            
            username_input = None
            password_input = None
            
            # Try to find username input
            for selector in username_selectors:
                try:
                    if selector.startswith("//"):
                        username_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        username_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    self.logger.info(f"Found username input with selector: {selector}")
                    break
                except:
                    continue
            
            # Try to find password input
            for selector in password_selectors:
                try:
                    if selector.startswith("//"):
                        password_input = self.driver.find_element(By.XPATH, selector)
                    else:
                        password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found password input with selector: {selector}")
                    break
                except:
                    continue
            
            if username_input and password_input:
                self.logger.info("Found login form, entering credentials...")
                
                # Clear and enter username
                username_input.clear()
                time.sleep(0.5)
                username_input.send_keys(username)
                time.sleep(1)
                
                # Clear and enter password
                password_input.clear()
                time.sleep(0.5)
                password_input.send_keys(password)
                time.sleep(1)
                
                # Look for login button
                login_button_selectors = [
                    "button[type='submit']",
                    "button[data-e2e='login-button']",
                    "button[data-testid='login-button']",
                    "//button[contains(text(), 'Log in')]",
                    "//button[contains(text(), 'Sign in')]",
                    "//button[contains(text(), 'Login')]",
                    "//div[@role='button' and contains(text(), 'Log in')]",
                    "//button[@type='submit']",
                    "//input[@type='submit']",
                    "button:not([disabled])[type='submit']",
                    "button:not([disabled])[data-e2e='login-button']"
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        if selector.startswith("//"):
                            login_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        # Check if button is enabled
                        if login_button.is_enabled():
                            self.logger.info(f"Found login button with selector: {selector}")
                            break
                        else:
                            self.logger.warning(f"Login button found but disabled: {selector}")
                            login_button = None
                    except:
                        continue
                
                if login_button:
                    self.logger.info("Clicking login button...")
                    
                    # Wait for button to be enabled if it's currently disabled
                    if not login_button.is_enabled():
                        self.logger.info("Login button is disabled, waiting for it to become enabled...")
                        try:
                            self.wait.until(lambda driver: login_button.is_enabled())
                        except:
                            self.logger.warning("Login button remained disabled, proceeding anyway...")
                    
                    # Try multiple click methods
                    try:
                        login_button.click()
                    except Exception as click_error:
                        self.logger.warning(f"Direct click failed: {click_error}, trying JavaScript click...")
                        try:
                            self.driver.execute_script("arguments[0].click();", login_button)
                        except Exception as js_error:
                            self.logger.error(f"JavaScript click also failed: {js_error}")
                            return False
                    
                    time.sleep(3)
                    
                    # Check for verification challenges
                    if manual_verification or self._check_for_verification():
                        self.logger.info("Verification challenge detected or manual mode enabled")
                        if not self.headless:
                            print("\n🔒 Manual verification required!")
                            print("Please complete any verification challenges in the browser window.")
                            print("Press Enter when you have successfully logged in...")
                            input()
                        else:
                            self.logger.error("Verification required but running in headless mode")
                            return False
                    
                    # Wait for login to complete
                    time.sleep(5)
                    
                    # Check if login was successful
                    return self._verify_login()
                else:
                    self.logger.error("Could not find enabled login button")
            else:
                self.logger.error(f"Could not find login form. Username input: {username_input is not None}, Password input: {password_input is not None}")
                
                # If manual verification is enabled and we can't find the form, let user handle it
                if manual_verification and not self.headless:
                    print("\n🔒 Could not find login form automatically.")
                    print("Please log in manually in the browser window.")
                    print("Press Enter when you have successfully logged in...")
                    input()
                    return self._verify_login()
            
        except Exception as e:
            self.logger.error(f"Login method error: {str(e)}")
            
            # Final fallback: manual login if not headless
            if manual_verification and not self.headless:
                print(f"\n🔒 Automatic login failed: {str(e)}")
                print("Please log in manually in the browser window.")
                print("Press Enter when you have successfully logged in...")
                input()
                return self._verify_login()
        
        return False
    
    def _check_for_verification(self) -> bool:
        """Check if there's a verification challenge."""
        try:
            verification_indicators = [
                "//div[contains(text(), 'verify')]",
                "//div[contains(text(), 'Verify')]",
                "//div[contains(text(), 'captcha')]",
                "//div[contains(text(), 'CAPTCHA')]",
                "//div[contains(text(), 'challenge')]",
                "//div[contains(text(), 'Challenge')]",
                "//div[contains(text(), 'robot')]",
                "//div[contains(text(), 'Robot')]",
                "[data-testid='captcha']",
                ".captcha",
                "#captcha"
            ]
            
            for indicator in verification_indicators:
                try:
                    if indicator.startswith("//"):
                        self.driver.find_element(By.XPATH, indicator)
                    else:
                        self.driver.find_element(By.CSS_SELECTOR, indicator)
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking for verification: {str(e)}")
            return False
    
    def _verify_login(self) -> bool:
        """Verify if login was successful."""
        try:
            # Wait a moment for page to load
            time.sleep(2)
            
            # Look for elements that indicate successful login
            success_indicators = [
                "[data-e2e='profile-icon']",
                "[data-e2e='nav-profile']",
                "[data-e2e='nav-avatar']",
                "img[alt*='avatar']",
                "[href*='/profile']",
                "a[href*='/@']",
                "[data-e2e='user-title']",
                "[data-e2e='user-subtitle']",
                ".user-info",
                ".profile-info"
            ]
            
            for indicator in success_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, indicator)
                    self.logger.info(f"Login verified with indicator: {indicator}")
                    return True
                except:
                    continue
            
            # Check URL for profile page or main feed
            current_url = self.driver.current_url
            if "/profile" in current_url or "/@" in current_url or "tiktok.com" in current_url:
                # Additional check: look for feed content or navigation
                try:
                    feed_indicators = [
                        "[data-e2e='video-player']",
                        "[data-e2e='feed-video']",
                        ".video-feed",
                        ".feed-item"
                    ]
                    for feed_indicator in feed_indicators:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, feed_indicator)
                            self.logger.info("Login verified - found feed content")
                            return True
                        except:
                            continue
                except:
                    pass
                
                # If we're on a TikTok page and not on login page, assume success
                if "login" not in current_url.lower():
                    self.logger.info("Login verified - on TikTok page (not login)")
                    return True
                
        except Exception as e:
            self.logger.error(f"Login verification error: {str(e)}")
        
        self.logger.warning("Login verification failed - may still be on login page")
        return False
    
    def navigate_to_reposts_tab(self, username: str = None) -> bool:
        """
        Navigate to user's reposts tab.
        
        Args:
            username: TikTok username (optional if already logged in)
            
        Returns:
            bool: True if navigation successful
        """
        try:
            if username:
                profile_url = f"{config.TIKTOK_BASE_URL}/@{username}"
            else:
                # Try multiple methods to find profile URL
                profile_url = None
                
                # Method 1: Look for profile link in navigation
                profile_elements = [
                    "[data-e2e='profile-icon']",
                    "[data-e2e='nav-profile']",
                    "a[href*='/profile']",
                    "a[href*='/@']",
                    "img[alt*='avatar']",
                    "[data-e2e='nav-avatar']",
                    "//a[contains(@href, '/@')]"
                ]
                
                for element_selector in profile_elements:
                    try:
                        if element_selector.startswith("//"):
                            element = self.driver.find_element(By.XPATH, element_selector)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
                        profile_url = element.get_attribute('href')
                        if profile_url and '/@' in profile_url:
                            self.logger.info(f"Found profile URL: {profile_url}")
                            break
                    except:
                        continue
                
                # Method 2: Try to construct profile URL from current page or stored username
                if not profile_url:
                    try:
                        current_url = self.driver.current_url
                        if '/@' in current_url:
                            profile_url = current_url.split('/@')[0] + '/@' + current_url.split('/@')[1].split('/')[0]
                            self.logger.info(f"Constructed profile URL from current page: {profile_url}")
                    except:
                        pass
                
                # Method 3: Try to find username from page elements
                if not profile_url:
                    username_selectors = [
                        "[data-e2e='user-title']",
                        "[data-e2e='user-subtitle']",
                        ".user-info h3",
                        ".profile-info h1",
                        "//h1[@data-e2e='user-title']",
                        "//h2[@data-e2e='user-subtitle']"
                    ]
                    
                    for selector in username_selectors:
                        try:
                            if selector.startswith("//"):
                                element = self.driver.find_element(By.XPATH, selector)
                            else:
                                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            username_text = element.text.strip()
                            if username_text and '@' in username_text:
                                username_clean = username_text.replace('@', '')
                                profile_url = f"{config.TIKTOK_BASE_URL}/@{username_clean}"
                                self.logger.info(f"Constructed profile URL from username element: {profile_url}")
                                break
                        except:
                            continue
                
                if not profile_url:
                    self.logger.error("Could not find profile URL")
                    return False
            
            # Navigate to profile first
            self.driver.get(profile_url)
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # Wait for profile page to load
            try:
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(2)
            except:
                pass
            
            # Look for and click the "Reposts" tab
            repost_tab_selectors = [
                "//div[contains(text(), 'Reposts')]",
                "//span[contains(text(), 'Reposts')]", 
                "//a[contains(text(), 'Reposts')]",
                "//button[contains(text(), 'Reposts')]",
                "[data-e2e='reposts-tab']",
                "[data-e2e='user-reposts']",
                "//div[@role='tab' and contains(text(), 'Reposts')]",
                "//div[contains(@class, 'tab') and contains(text(), 'Reposts')]",
                "//span[contains(@class, 'tab') and contains(text(), 'Reposts')]",
                "//a[contains(@href, 'repost')]",
                "//div[text()='Reposts']",
                "//span[text()='Reposts']"
            ]
            
            repost_tab = None
            for selector in repost_tab_selectors:
                try:
                    if selector.startswith("//"):
                        repost_tab = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        repost_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    self.logger.info(f"Found reposts tab with selector: {selector}")
                    break
                except:
                    continue
            
            if repost_tab:
                repost_tab.click()
                time.sleep(config.PAGE_LOAD_DELAY)
                self.logger.info(f"Navigated to reposts tab: {profile_url}")
                return True
            else:
                self.logger.warning("Could not find reposts tab. User may have no reposts or tab structure changed.")
                # Try scrolling to see if reposts tab appears
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Try again after scrolling
                for selector in repost_tab_selectors:
                    try:
                        if selector.startswith("//"):
                            repost_tab = self.driver.find_element(By.XPATH, selector)
                        else:
                            repost_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                        repost_tab.click()
                        time.sleep(config.PAGE_LOAD_DELAY)
                        self.logger.info(f"Found reposts tab after scrolling with selector: {selector}")
                        return True
                    except:
                        continue
                
                return False
            
        except Exception as e:
            self.logger.error(f"Reposts navigation error: {str(e)}")
            return False
    
    def collect_reposts(self) -> List[Dict]:
        """
        Collect all reposts from the user's reposts tab.
        
        Returns:
            List of repost information dictionaries
        """
        self.logger.info("Starting repost collection")
        reposts = []
        
        try:
            # Scroll to load all reposts
            self._scroll_to_load_all_videos()
            
            # Find repost elements
            repost_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-e2e='user-post-item'], [data-e2e='video-item'], .video-feed-item, .video-item")
            
            self.logger.info(f"Found {len(repost_elements)} repost elements")
            
            for i, element in enumerate(tqdm(repost_elements, desc="Collecting reposts")):
                try:
                    repost_info = self._extract_repost_info(element, i)
                    if repost_info:
                        reposts.append(repost_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing repost {i}: {str(e)}")
                    continue
            
            self.videos = reposts  # Store as videos for compatibility
            self.logger.info(f"Collected {len(reposts)} reposts")
            return reposts
            
        except Exception as e:
            self.logger.error(f"Repost collection error: {str(e)}")
            return reposts
    
    def _extract_repost_info(self, element, index: int) -> Optional[Dict]:
        """Extract information from a repost element."""
        try:
            repost_info = {
                'index': index,
                'element': element,
                'url': None,
                'thumbnail_url': None,
                'title': None,
                'original_creator': None,
                'repost_date': None,
                'likes': 0,
                'views': 0,
                'is_repost': True  # Mark as repost
            }
            
            # Get repost URL
            try:
                link_element = element.find_element(By.TAG_NAME, "a")
                repost_info['url'] = link_element.get_attribute('href')
            except:
                pass
            
            # Get thumbnail URL
            try:
                img_element = element.find_element(By.TAG_NAME, "img")
                repost_info['thumbnail_url'] = img_element.get_attribute('src')
            except:
                pass
            
            # Get repost title/description
            try:
                title_selectors = [
                    "[data-e2e='video-desc']",
                    ".video-meta-title",
                    "img[alt]"
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, selector)
                        repost_info['title'] = title_element.get_attribute('alt') or title_element.text
                        if repost_info['title']:
                            break
                    except:
                        continue
            except:
                pass
            
            # Try to find original creator info
            try:
                creator_selectors = [
                    "[data-e2e='video-author']",
                    ".video-author",
                    ".original-creator",
                    "//span[contains(text(), '@')]"
                ]
                
                for selector in creator_selectors:
                    try:
                        if selector.startswith("//"):
                            creator_element = element.find_element(By.XPATH, selector)
                        else:
                            creator_element = element.find_element(By.CSS_SELECTOR, selector)
                        creator_text = creator_element.text
                        if '@' in creator_text:
                            repost_info['original_creator'] = creator_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Get engagement metrics
            try:
                stats_elements = element.find_elements(By.CSS_SELECTOR, 
                    "[data-e2e*='like'], [data-e2e*='view'], .video-count")
                
                for stat_element in stats_elements:
                    text = stat_element.text
                    if 'like' in stat_element.get_attribute('data-e2e') or '♥' in text:
                        repost_info['likes'] = self._parse_count(text)
                    elif 'view' in stat_element.get_attribute('data-e2e') or 'view' in text.lower():
                        repost_info['views'] = self._parse_count(text)
            except:
                pass
            
            return repost_info
            
        except Exception as e:
            self.logger.warning(f"Error extracting repost info: {str(e)}")
            return None
    
    def _scroll_to_load_all_videos(self):
        """Scroll down to load all videos."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
                
            last_height = new_height
            
            # Limit scanning if configured
            if config.MAX_VIDEOS_TO_SCAN > 0:
                current_videos = len(self.driver.find_elements(By.CSS_SELECTOR, 
                    "[data-e2e='user-post-item'], [data-e2e='video-item']"))
                if current_videos >= config.MAX_VIDEOS_TO_SCAN:
                    break
    
    def _extract_video_info(self, element, index: int) -> Optional[Dict]:
        """Extract information from a video element."""
        try:
            video_info = {
                'index': index,
                'element': element,
                'url': None,
                'thumbnail_url': None,
                'title': None,
                'likes': 0,
                'views': 0,
                'upload_date': None,
                'duration': None
            }
            
            # Get video URL
            try:
                link_element = element.find_element(By.TAG_NAME, "a")
                video_info['url'] = link_element.get_attribute('href')
            except:
                pass
            
            # Get thumbnail URL
            try:
                img_element = element.find_element(By.TAG_NAME, "img")
                video_info['thumbnail_url'] = img_element.get_attribute('src')
            except:
                pass
            
            # Get video title/description
            try:
                title_selectors = [
                    "[data-e2e='video-desc']",
                    ".video-meta-title",
                    "img[alt]"
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, selector)
                        video_info['title'] = title_element.get_attribute('alt') or title_element.text
                        if video_info['title']:
                            break
                    except:
                        continue
            except:
                pass
            
            # Get engagement metrics
            try:
                stats_elements = element.find_elements(By.CSS_SELECTOR, 
                    "[data-e2e*='like'], [data-e2e*='view'], .video-count")
                
                for stat_element in stats_elements:
                    text = stat_element.text
                    if 'like' in stat_element.get_attribute('data-e2e') or '♥' in text:
                        video_info['likes'] = self._parse_count(text)
                    elif 'view' in stat_element.get_attribute('data-e2e') or 'view' in text.lower():
                        video_info['views'] = self._parse_count(text)
            except:
                pass
            
            return video_info
            
        except Exception as e:
            self.logger.warning(f"Error extracting video info: {str(e)}")
            return None
    
    def _parse_count(self, count_text: str) -> int:
        """Parse count text like '1.2K', '5.4M' to integer."""
        try:
            count_text = count_text.strip().upper()
            
            # Remove non-numeric characters except K, M, B, .
            import re
            count_text = re.sub(r'[^\d.KMB]', '', count_text)
            
            if 'K' in count_text:
                return int(float(count_text.replace('K', '')) * 1000)
            elif 'M' in count_text:
                return int(float(count_text.replace('M', '')) * 1000000)
            elif 'B' in count_text:
                return int(float(count_text.replace('B', '')) * 1000000000)
            else:
                return int(float(count_text)) if count_text else 0
                
        except:
            return 0
    
    def analyze_videos(self) -> Dict:
        """
        Analyze videos to detect reposts using image hashing.
        
        Returns:
            Dictionary containing duplicate groups
        """
        self.logger.info("Starting video analysis for duplicates")
        
        if not self.videos:
            self.logger.warning("No videos to analyze")
            return {}
        
        # Download and hash thumbnails
        self._process_thumbnails()
        
        # Find duplicates
        duplicates = self._find_duplicates()
        
        self.logger.info(f"Found {len(duplicates)} groups of duplicates")
        return duplicates
    
    def _process_thumbnails(self):
        """Download and process video thumbnails."""
        self.logger.info("Processing video thumbnails")
        
        for video in tqdm(self.videos, desc="Processing thumbnails"):
            try:
                if video.get('thumbnail_url'):
                    # Download thumbnail
                    response = requests.get(video['thumbnail_url'], timeout=10)
                    if response.status_code == 200:
                        # Convert to PIL Image
                        image = Image.open(requests.get(video['thumbnail_url'], stream=True).raw)
                        
                        # Resize for consistent comparison
                        image = image.resize(config.THUMBNAIL_SIZE)
                        
                        # Generate perceptual hash
                        phash = imagehash.phash(image, hash_size=config.IMAGE_HASH_SIZE)
                        
                        # Store hash
                        video['image_hash'] = str(phash)
                        self.video_hashes[video['index']] = phash
                        
                        # Small delay to avoid overwhelming the server
                        time.sleep(0.1)
                        
            except Exception as e:
                self.logger.warning(f"Error processing thumbnail for video {video['index']}: {str(e)}")
                continue
    
    def _find_duplicates(self) -> Dict:
        """Find duplicate videos based on image hashes."""
        duplicates = {}
        processed = set()
        
        for i, video1 in enumerate(self.videos):
            if i in processed or 'image_hash' not in video1:
                continue
                
            hash1 = self.video_hashes.get(i)
            if not hash1:
                continue
                
            duplicate_group = [video1]
            
            for j, video2 in enumerate(self.videos[i+1:], i+1):
                if j in processed or 'image_hash' not in video2:
                    continue
                    
                hash2 = self.video_hashes.get(j)
                if not hash2:
                    continue
                
                # Calculate similarity
                similarity = 1 - (hash1 - hash2) / len(hash1.hash) ** 2
                
                if similarity >= self.similarity_threshold:
                    duplicate_group.append(video2)
                    processed.add(j)
            
            if len(duplicate_group) > 1:
                duplicates[f"group_{len(duplicates)}"] = duplicate_group
                processed.add(i)
        
        return duplicates
    
    def remove_all_reposts(self, dry_run: bool = False) -> List[Dict]:
        """
        Main method to scan and remove all TikTok reposts.
        
        Args:
            dry_run: If True, only scan and report, don't actually remove
            
        Returns:
            List of removed reposts
        """
        self.logger.info(f"Starting repost removal (dry_run={dry_run})")
        
        # Navigate to reposts tab
        if not self.navigate_to_reposts_tab():
            raise Exception("Failed to navigate to reposts tab")
        
        # Collect reposts
        reposts = self.collect_reposts()
        if not reposts:
            self.logger.info("No reposts found")
            return []
        
        # Remove reposts
        removed_reposts = []
        
        self.logger.info(f"Found {len(reposts)} reposts to process")
        
        if not dry_run:
            for repost in reposts:
                self.logger.info(f"Processing repost from @{repost.get('original_creator', 'Unknown')}: {repost.get('title', 'Untitled')[:50]}")
                
                if self._delete_repost(repost):
                    removed_reposts.append(repost)
                    self.deleted_videos.append(repost)  # Keep for compatibility
                    time.sleep(config.DELAY_BETWEEN_ACTIONS)  # Respect rate limits
        else:
            self.logger.info(f"Would remove {len(reposts)} reposts")
            removed_reposts = reposts
        
        self.logger.info(f"Removed {len(removed_reposts)} reposts")
        return removed_reposts
    
    def _delete_repost(self, repost: Dict) -> bool:
        """Delete a specific repost using TikTok's remove repost feature."""
        try:
            self.logger.info(f"Removing repost: {repost.get('url', 'Unknown URL')}")
            
            # Navigate to repost
            if repost.get('url'):
                self.driver.get(repost['url'])
                time.sleep(config.PAGE_LOAD_DELAY)
            
            # Method 1: Try Share button -> Remove repost
            try:
                share_selectors = [
                    "[data-e2e='video-share-button']",
                    "[data-e2e='browse-share']",
                    "button[aria-label*='Share']",
                    ".share-button",
                    "//button[contains(@aria-label, 'Share')]"
                ]
                
                share_button = None
                for selector in share_selectors:
                    try:
                        if selector.startswith("//"):
                            share_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            share_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if share_button:
                    share_button.click()
                    time.sleep(1)
                    
                    # Look for "Remove repost" option
                    remove_repost_selectors = [
                        "//div[contains(text(), 'Remove repost')]",
                        "//span[contains(text(), 'Remove repost')]",
                        "[data-e2e='remove-repost']",
                        "//button[contains(text(), 'Remove repost')]"
                    ]
                    
                    for selector in remove_repost_selectors:
                        try:
                            if selector.startswith("//"):
                                remove_button = self.driver.find_element(By.XPATH, selector)
                            else:
                                remove_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            remove_button.click()
                            time.sleep(1)
                            
                            self.logger.info("Repost removed via Share -> Remove repost")
                            return True
                        except:
                            continue
            
            except Exception as e:
                self.logger.warning(f"Share button method failed: {str(e)}")
            
            # Method 2: Try long press -> Remove repost
            try:
                # Find the video element
                video_selectors = [
                    "[data-e2e='video-player']",
                    "video",
                    ".video-container",
                    "[data-e2e='browse-video']"
                ]
                
                video_element = None
                for selector in video_selectors:
                    try:
                        video_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if video_element:
                    # Long press on video
                    actions = ActionChains(self.driver)
                    actions.click_and_hold(video_element).perform()
                    time.sleep(2)
                    actions.release().perform()
                    
                    # Look for context menu with remove repost
                    remove_repost_selectors = [
                        "//div[contains(text(), 'Remove repost')]",
                        "//span[contains(text(), 'Remove repost')]",
                        "[data-e2e='remove-repost']"
                    ]
                    
                    for selector in remove_repost_selectors:
                        try:
                            if selector.startswith("//"):
                                remove_button = self.driver.find_element(By.XPATH, selector)
                            else:
                                remove_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            remove_button.click()
                            time.sleep(1)
                            
                            self.logger.info("Repost removed via long press -> Remove repost")
                            return True
                        except:
                            continue
            
            except Exception as e:
                self.logger.warning(f"Long press method failed: {str(e)}")
            
            # Method 3: Try profile photo -> Reposted -> Remove repost
            try:
                profile_photo_selectors = [
                    "[data-e2e='video-avatar']",
                    ".video-avatar",
                    "img[alt*='avatar']",
                    ".user-avatar"
                ]
                
                for selector in profile_photo_selectors:
                    try:
                        profile_photo = self.driver.find_element(By.CSS_SELECTOR, selector)
                        profile_photo.click()
                        time.sleep(1)
                        
                        # Look for "Reposted" indicator
                        reposted_selectors = [
                            "//div[contains(text(), 'Reposted')]",
                            "//span[contains(text(), 'Reposted')]",
                            "[data-e2e='reposted-indicator']"
                        ]
                        
                        for repost_selector in reposted_selectors:
                            try:
                                if repost_selector.startswith("//"):
                                    reposted_element = self.driver.find_element(By.XPATH, repost_selector)
                                else:
                                    reposted_element = self.driver.find_element(By.CSS_SELECTOR, repost_selector)
                                reposted_element.click()
                                time.sleep(1)
                                
                                # Look for remove repost option
                                remove_selectors = [
                                    "//div[contains(text(), 'Remove repost')]",
                                    "//span[contains(text(), 'Remove repost')]"
                                ]
                                
                                for remove_selector in remove_selectors:
                                    try:
                                        remove_button = self.driver.find_element(By.XPATH, remove_selector)
                                        remove_button.click()
                                        time.sleep(1)
                                        
                                        self.logger.info("Repost removed via profile photo -> Reposted -> Remove repost")
                                        return True
                                    except:
                                        continue
                            except:
                                continue
                        break
                    except:
                        continue
            
            except Exception as e:
                self.logger.warning(f"Profile photo method failed: {str(e)}")
            
            self.logger.error("All removal methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing repost: {str(e)}")
            return False
    
    def scan_for_reposts(self, dry_run: bool = True) -> List[Dict]:
        """
        Scan for reposts without removing them.
        
        Args:
            dry_run: Always True for this method
            
        Returns:
            List of detected reposts
        """
        return self.remove_all_reposts(dry_run=True)
    
    def remove_specific_reposts(self, videos_to_remove: List[Dict]) -> List[Dict]:
        """
        Remove specific videos from the repost list.
        
        Args:
            videos_to_remove: List of video dictionaries to remove
            
        Returns:
            List of successfully removed videos
        """
        removed_videos = []
        
        for video in videos_to_remove:
            if self._delete_video(video):
                removed_videos.append(video)
                self.deleted_videos.append(video)
        
        return removed_videos
    
    def get_statistics(self) -> Dict:
        """Get statistics about the scanning and removal process."""
        return {
            'total_videos': len(self.videos),
            'videos_with_hashes': len([v for v in self.videos if 'image_hash' in v]),
            'deleted_videos': len(self.deleted_videos),
            'similarity_threshold': self.similarity_threshold
        }
    
    def save_report(self, filename: str = None) -> str:
        """Save a detailed report of the process."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"repost_removal_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'deleted_videos': self.deleted_videos,
            'configuration': {
                'similarity_threshold': self.similarity_threshold,
                'batch_size': self.batch_size,
                'headless': self.headless
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report saved to {filename}")
        return filename
    
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed")
    
    def keep_browser_open(self):
        """Keep the browser open for manual use."""
        if self.driver:
            self.logger.info("Browser will remain open for manual use")
            print("🌐 Browser is staying open. You can:")
            print("- Verify the changes on TikTok")
            print("- Navigate to other parts of the site")
            print("- Close the browser window manually when done")
        else:
            self.logger.warning("No browser session to keep open")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Don't automatically close if we want to keep browser open
        if hasattr(self, '_keep_open') and self._keep_open:
            self.keep_browser_open()
        else:
            self.close()