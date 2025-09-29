# Quick Start Guide for TikTok Repost Remover

## Installation

1. **Install dependencies:**
   ```bash
   python install.py
   ```

2. **Setup credentials:**
   - Edit `.env` file with your TikTok username and password
   - Or use command line arguments

## Usage

### Quick Removal (Recommended)
```bash
# Dry run first (scan only, no deletion)
python main.py --dry-run

# If satisfied with results, remove reposts
python main.py
```

### With Credentials
```bash
# Using command line
python main.py -u your_username -p your_password --dry-run

# Using environment file
python main.py -c .env --dry-run
```

### Advanced Options
```bash
# Custom similarity threshold (0.9 = 90% similar)
python main.py --threshold 0.95 --dry-run

# Show browser window (helpful for debugging)
python main.py --no-headless --dry-run

# Full command with all options
python main.py -u username -p password --threshold 0.9 --headless --dry-run
```

## Examples

Run interactive examples:
```bash
# Basic usage example
python examples.py basic

# Advanced usage with custom settings
python examples.py advanced

# Selective removal (choose which videos to remove)
python examples.py selective
```

## How It Works

1. **Login**: Logs into your TikTok account using browser automation
2. **Scan**: Collects all videos from your profile
3. **Analyze**: Downloads thumbnails and creates perceptual hashes
4. **Compare**: Finds videos with similar visual content
5. **Remove**: Deletes duplicate videos (keeps most popular version)

## Safety Features

- ✅ **Dry run mode** - Test before deleting anything
- ✅ **Confirmation prompts** - Always asks before deletion
- ✅ **Detailed logging** - Tracks all actions
- ✅ **Report generation** - Saves summary of what was removed
- ✅ **Smart selection** - Keeps most popular version of duplicates

## Troubleshooting

### Login Issues
- Try running with `--no-headless` to see what's happening
- Make sure your credentials are correct
- TikTok may require 2FA - handle manually in visible browser

### No Videos Found
- Make sure your profile is public or you're logged in correctly
- Check if TikTok changed their page structure
- Try with `--no-headless` to debug

### Permission Errors
- Make sure you have permission to create files in the directory
- Run as administrator if necessary on Windows

## Configuration

Edit `config.py` to customize:
- `SIMILARITY_THRESHOLD`: How similar videos need to be (0.0-1.0)
- `BATCH_SIZE`: Number of videos to process at once
- `DELAY_BETWEEN_ACTIONS`: Delay between actions (avoid rate limiting)

## Warning

⚠️ **Always use `--dry-run` first!**
⚠️ **This tool cannot undo deletions!**
⚠️ **Use at your own risk - respect TikTok's Terms of Service**