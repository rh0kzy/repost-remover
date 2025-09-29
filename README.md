# TikTok Repost Remover

A Python tool that automatically detects and removes reposts from your TikTok account.

## Features

- 🔍 **Smart Detection**: Uses image hashing and content analysis to identify reposts
- 🤖 **Automated Removal**: Automatically deletes detected reposts
- 🔐 **Secure Login**: Safe authentication using your TikTok credentials
- 📊 **Progress Tracking**: Real-time progress updates with detailed logging
- ⚙️ **Customizable**: Configurable similarity thresholds and batch processing

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd repost-remover
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your TikTok credentials:
```
TIKTOK_USERNAME=your_username
TIKTOK_PASSWORD=your_password
```

## Usage

### Quick Start
```python
from tiktok_repost_remover import TikTokRepostRemover

# Initialize the remover
remover = TikTokRepostRemover()

# Login with your credentials
remover.login("your_username", "your_password")

# Scan and remove all reposts
remover.remove_all_reposts()
```

### Advanced Usage
```python
# Custom configuration
remover = TikTokRepostRemover(
    similarity_threshold=0.95,  # How similar videos need to be (0.0-1.0)
    batch_size=10,              # Number of videos to process at once
    headless=True               # Run browser in background
)

# Dry run (scan only, don't delete)
reposts = remover.scan_for_reposts(dry_run=True)
print(f"Found {len(reposts)} potential reposts")

# Remove specific reposts
remover.remove_specific_reposts(reposts[:5])  # Remove first 5
```

## How It Works

1. **Login**: Securely logs into your TikTok account using Selenium WebDriver
2. **Video Collection**: Gathers all videos from your profile
3. **Content Analysis**: Downloads and analyzes video thumbnails and metadata
4. **Duplicate Detection**: Uses perceptual hashing to identify similar content
5. **Smart Removal**: Keeps the oldest/most popular version and removes duplicates

## Safety Features

- ⚠️ **Confirmation Prompts**: Always asks before deleting videos
- 📝 **Detailed Logging**: Logs all actions for review
- 🔄 **Undo Support**: Maintains a list of deleted videos for reference
- 🛡️ **Rate Limiting**: Respects TikTok's API limits to avoid account issues

## Configuration

You can customize the tool's behavior by modifying `config.py`:

- `SIMILARITY_THRESHOLD`: How similar videos need to be to be considered reposts (default: 0.9)
- `BATCH_SIZE`: Number of videos to process simultaneously (default: 5)
- `DELAY_BETWEEN_ACTIONS`: Delay between actions to avoid rate limiting (default: 2 seconds)

## Disclaimer

This tool is for educational purposes. Use responsibly and in accordance with TikTok's Terms of Service. The authors are not responsible for any account issues that may arise from using this tool.

## License

MIT License - see LICENSE file for details.