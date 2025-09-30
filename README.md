# TikTok Repost Remover

A Python tool that automatically detects and removes **TikTok reposts** from your account.

## What are TikTok Reposts?

**TikTok reposts** are videos that you've shared from other creators to your own profile. They:
- Appear with a "repost" label
- Show the original creator's name
- Are found in the "Reposts" tab on your profile
- Are NOT your original content

This tool helps you clean up your profile by removing these shared videos.

## Features

- 🔍 **Smart Detection**: Finds all reposts in your Reposts tab
- 🤖 **Automated Removal**: Uses TikTok's official "Remove repost" feature
- 🔐 **Secure Login**: Safe authentication with manual verification support
- 📊 **Progress Tracking**: Real-time progress updates with detailed logging
- ⚙️ **Manual Selection**: Choose which reposts to remove
- 🛡️ **Safe Operation**: Only affects reposts, never your original content

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
remover.login("your_username", "your_password", manual_verification=True)

# Navigate to reposts tab and remove all reposts
remover.remove_all_reposts()
```

### Manual Mode (Recommended)
```bash
# Use the guided manual mode
python manual_mode.py

# Or with the main script
python main.py --no-headless --manual --dry-run
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

1. **Login**: Securely logs into your TikTok account using browser automation
2. **Navigate**: Goes to your profile's "Reposts" tab
3. **Collect**: Gathers all reposted videos (videos you've shared from others)
4. **Remove**: Uses TikTok's official "Remove repost" feature to clean them up
5. **Report**: Provides detailed logging of what was removed

## What Gets Removed vs. What Stays

✅ **REMOVED (Reposts):**
- Videos you've shared from other creators
- Content with "repost" labels
- Videos in your "Reposts" tab

❌ **NEVER TOUCHED (Your Content):**
- Your original videos
- Videos you created and uploaded
- Content in your main profile tab

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