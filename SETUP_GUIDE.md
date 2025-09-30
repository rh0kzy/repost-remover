# TikTok Repost Remover - Setup & Troubleshooting Guide

## 🚨 Important Notice

TikTok has very strong anti-bot measures. This tool may require manual intervention to complete login due to:
- CAPTCHA challenges
- Phone verification
- Suspicious activity detection
- Two-factor authentication

## ✅ Current Status

✅ **ChromeDriver Issue Fixed** - Browser automation is working  
✅ **Login Form Detection** - Can find and fill login forms  
⚠️ **Manual Verification Required** - TikTok requires human verification  

## 🎯 Recommended Usage

### Option 1: Manual Verification Mode (Recommended)
```bash
# Run with manual verification enabled
python main.py --no-headless --manual --dry-run
```

**What happens:**
1. Browser opens and navigates to TikTok login
2. Tool attempts automatic login
3. If verification is needed, you complete it manually
4. Tool continues with repost detection

### Option 2: Fully Manual Login
```bash
# Start with browser visible, log in yourself
python main.py --no-headless --dry-run

# When prompted for login, manually:
# 1. Log into TikTok in the browser
# 2. Navigate to your profile
# 3. Press Enter in the terminal
```

### Option 3: Use with Different Account
- Create a test TikTok account specifically for testing
- Use less strict credentials (no 2FA if possible)
- Upload a few test videos with obvious duplicates

## 🔧 Step-by-Step Setup

### 1. Install and Test
```bash
# Install dependencies
python install.py

# Test browser functionality
python browser_test.py

# Test with visible browser
python main.py --no-headless --manual --dry-run
```

### 2. Configure Credentials
Edit `.env` file:
```
TIKTOK_USERNAME=your_username
TIKTOK_PASSWORD=your_password
```

### 3. Run Tests
```bash
# Always test with dry-run first
python main.py --dry-run --manual --no-headless

# If successful, run actual removal
python main.py --manual --no-headless
```

## 🐛 Troubleshooting

### Login Issues
**Problem**: "Login failed" or verification challenges  
**Solution**: 
- Use `--manual --no-headless` flags
- Complete verification manually in browser
- Try with a test account first

**Problem**: "Stale element reference"  
**Solution**: This is normal - TikTok changes the page dynamically. Use manual mode.

### Browser Issues
**Problem**: ChromeDriver errors  
**Solution**: 
```bash
python fix_chromedriver.py
python browser_test.py
```

**Problem**: "Chrome not found"  
**Solution**: Install Google Chrome from https://www.google.com/chrome/

### No Videos Found
**Problem**: Tool can't find videos on profile  
**Solution**: 
- Make sure profile is public
- Check if you're logged in correctly
- Use `--no-headless` to see what's happening

## 🎮 Demo Mode

For testing without your main account:

1. **Create Test Account**:
   - New TikTok account with simple password
   - No 2FA enabled
   - Upload 3-4 test videos (same content)

2. **Run Demo**:
   ```bash
   python examples.py basic
   ```

## 🔒 Security Notes

- ✅ Credentials stored locally only
- ✅ No data sent to external servers
- ✅ Browser automation visible for transparency
- ⚠️ Use at your own risk
- ⚠️ Respect TikTok's Terms of Service

## 📞 Need Help?

Common solutions:
1. **Always run `--dry-run` first**
2. **Use `--no-headless --manual` for TikTok**
3. **Test with `browser_test.py` first**
4. **Try with a test account**
5. **Check Chrome is updated**

## 🚀 Quick Commands

```bash
# Full test sequence
python browser_test.py
python main.py --no-headless --manual --dry-run

# If test passes, run real removal
python main.py --no-headless --manual

# Emergency: just view browser automation
python -c "
from selenium import webdriver
driver = webdriver.Chrome()
driver.get('https://tiktok.com/login')
input('Press Enter to close...')
driver.quit()
"
```