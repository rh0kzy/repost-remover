# Configuration settings for TikTok Repost Remover

# Similarity threshold for duplicate detection (0.0 - 1.0)
# Higher values = more strict (videos must be more similar)
SIMILARITY_THRESHOLD = 0.9

# Number of videos to process in each batch
BATCH_SIZE = 5

# Delay between actions (seconds) to avoid rate limiting
DELAY_BETWEEN_ACTIONS = 2

# Delay between page loads (seconds)
PAGE_LOAD_DELAY = 3

# Maximum number of videos to scan (0 = unlimited)
MAX_VIDEOS_TO_SCAN = 0

# Browser settings
HEADLESS_BROWSER = True  # Set to False to see browser window
BROWSER_TIMEOUT = 30

# Image analysis settings
IMAGE_HASH_SIZE = 16  # Size for perceptual hashing
THUMBNAIL_SIZE = (256, 256)  # Size to resize thumbnails for comparison

# Logging settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "repost_remover.log"

# TikTok specific settings
TIKTOK_BASE_URL = "https://www.tiktok.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"