import os
import time
import logging
import requests
from typing import List, Dict, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
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
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize webdriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, config.BROWSER_TIMEOUT)
        self.logger.info("Browser initialized successfully")
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to TikTok account.
        
        Args:
            username: TikTok username or email
            password: TikTok password
            
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
            login_success = self._try_login_methods(username, password)
            
            if login_success:
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False
    
    def _try_login_methods(self, username: str, password: str) -> bool:
        """Try different login methods."""
        try:
            # Method 1: Look for email/username input
            username_selectors = [
                "input[placeholder*='Email']",
                "input[placeholder*='Username']",
                "input[name='username']",
                "input[type='email']",
                "input[type='text']"
            ]
            
            password_selectors = [
                "input[placeholder*='Password']",
                "input[name='password']",
                "input[type='password']"
            ]
            
            username_input = None
            password_input = None
            
            # Try to find username input
            for selector in username_selectors:
                try:
                    username_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
            
            # Try to find password input
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if username_input and password_input:
                username_input.clear()
                username_input.send_keys(username)
                time.sleep(1)
                
                password_input.clear()
                password_input.send_keys(password)
                time.sleep(1)
                
                # Look for login button
                login_button_selectors = [
                    "button[type='submit']",
                    "button[data-e2e='login-button']",
                    "button:contains('Log in')",
                    "div[role='button']:contains('Log in')"
                ]
                
                for selector in login_button_selectors:
                    try:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        login_button.click()
                        break
                    except:
                        continue
                
                # Wait for login to complete
                time.sleep(5)
                
                # Check if login was successful by looking for profile elements
                return self._verify_login()
            
        except Exception as e:
            self.logger.error(f"Login method error: {str(e)}")
        
        return False
    
    def _verify_login(self) -> bool:
        """Verify if login was successful."""
        try:
            # Look for elements that indicate successful login
            success_indicators = [
                "[data-e2e='profile-icon']",
                "img[alt*='avatar']",
                "[href*='/profile']",
                "a[href*='/@']"
            ]
            
            for indicator in success_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, indicator)
                    return True
                except:
                    continue
            
            # Check URL for profile page
            current_url = self.driver.current_url
            if "/profile" in current_url or "/@" in current_url:
                return True
                
        except Exception as e:
            self.logger.error(f"Login verification error: {str(e)}")
        
        return False
    
    def navigate_to_profile(self, username: str = None) -> bool:
        """
        Navigate to user's profile page.
        
        Args:
            username: TikTok username (optional if already logged in)
            
        Returns:
            bool: True if navigation successful
        """
        try:
            if username:
                profile_url = f"{config.TIKTOK_BASE_URL}/@{username}"
            else:
                # Try to find profile link
                profile_elements = [
                    "[data-e2e='profile-icon']",
                    "a[href*='/profile']",
                    "img[alt*='avatar']"
                ]
                
                for element_selector in profile_elements:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
                        profile_url = element.get_attribute('href')
                        if profile_url:
                            break
                    except:
                        continue
                else:
                    self.logger.error("Could not find profile URL")
                    return False
            
            self.driver.get(profile_url)
            time.sleep(config.PAGE_LOAD_DELAY)
            
            self.logger.info(f"Navigated to profile: {profile_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Profile navigation error: {str(e)}")
            return False
    
    def collect_videos(self) -> List[Dict]:
        """
        Collect all videos from the user's profile.
        
        Returns:
            List of video information dictionaries
        """
        self.logger.info("Starting video collection")
        videos = []
        
        try:
            # Scroll to load all videos
            self._scroll_to_load_all_videos()
            
            # Find video elements
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-e2e='user-post-item'], [data-e2e='video-item'], .video-feed-item, .video-item")
            
            self.logger.info(f"Found {len(video_elements)} video elements")
            
            for i, element in enumerate(tqdm(video_elements, desc="Collecting videos")):
                try:
                    video_info = self._extract_video_info(element, i)
                    if video_info:
                        videos.append(video_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing video {i}: {str(e)}")
                    continue
            
            self.videos = videos
            self.logger.info(f"Collected {len(videos)} videos")
            return videos
            
        except Exception as e:
            self.logger.error(f"Video collection error: {str(e)}")
            return videos
    
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
        Main method to scan and remove all reposts.
        
        Args:
            dry_run: If True, only scan and report, don't actually delete
            
        Returns:
            List of removed videos
        """
        self.logger.info(f"Starting repost removal (dry_run={dry_run})")
        
        # Navigate to profile
        if not self.navigate_to_profile():
            raise Exception("Failed to navigate to profile")
        
        # Collect videos
        videos = self.collect_videos()
        if not videos:
            self.logger.warning("No videos found")
            return []
        
        # Analyze for duplicates
        duplicates = self.analyze_videos()
        if not duplicates:
            self.logger.info("No duplicates found")
            return []
        
        # Remove duplicates
        removed_videos = []
        
        for group_name, duplicate_group in duplicates.items():
            self.logger.info(f"Processing {group_name} with {len(duplicate_group)} duplicates")
            
            # Sort by engagement (keep the one with most likes/views)
            duplicate_group.sort(key=lambda x: (x.get('likes', 0) + x.get('views', 0)), reverse=True)
            
            # Keep the first (most popular) and remove the rest
            to_remove = duplicate_group[1:]
            
            if not dry_run:
                for video in to_remove:
                    if self._delete_video(video):
                        removed_videos.append(video)
                        self.deleted_videos.append(video)
            else:
                self.logger.info(f"Would remove {len(to_remove)} videos from {group_name}")
                removed_videos.extend(to_remove)
        
        self.logger.info(f"Removed {len(removed_videos)} reposts")
        return removed_videos
    
    def _delete_video(self, video: Dict) -> bool:
        """Delete a specific video."""
        try:
            self.logger.info(f"Deleting video: {video.get('url', 'Unknown URL')}")
            
            # Navigate to video
            if video.get('url'):
                self.driver.get(video['url'])
                time.sleep(config.PAGE_LOAD_DELAY)
            
            # Find and click options menu
            options_selectors = [
                "[data-e2e='video-more-button']",
                "[data-e2e='browse-more']",
                "button[aria-label='More']",
                ".more-button",
                "button:contains('⋯')"
            ]
            
            options_button = None
            for selector in options_selectors:
                try:
                    options_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
            
            if not options_button:
                self.logger.error("Could not find options menu")
                return False
            
            options_button.click()
            time.sleep(1)
            
            # Find and click delete button
            delete_selectors = [
                "[data-e2e='delete-post']",
                "button:contains('Delete')",
                "div:contains('Delete')",
                "[aria-label*='Delete']"
            ]
            
            delete_button = None
            for selector in delete_selectors:
                try:
                    delete_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
            
            if not delete_button:
                self.logger.error("Could not find delete button")
                return False
            
            delete_button.click()
            time.sleep(1)
            
            # Confirm deletion
            confirm_selectors = [
                "button:contains('Delete')",
                "button:contains('Confirm')",
                "[data-e2e='confirm-delete']"
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    confirm_button.click()
                    break
                except:
                    continue
            
            time.sleep(config.DELAY_BETWEEN_ACTIONS)
            self.logger.info("Video deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting video: {str(e)}")
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
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()