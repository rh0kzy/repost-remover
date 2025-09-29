#!/usr/bin/env python3
"""
Test script for TikTok Repost Remover
Tests basic functionality without actually deleting anything
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tiktok_repost_remover import TikTokRepostRemover
import config


def test_initialization():
    """Test basic initialization."""
    print("🧪 Testing initialization...")
    
    try:
        remover = TikTokRepostRemover()
        print("✅ TikTokRepostRemover initialized successfully")
        
        # Test configuration
        assert hasattr(remover, 'similarity_threshold')
        assert hasattr(remover, 'batch_size')
        assert hasattr(remover, 'headless')
        print("✅ Configuration attributes present")
        
        # Test default values
        assert remover.similarity_threshold == config.SIMILARITY_THRESHOLD
        assert remover.batch_size == config.BATCH_SIZE
        print("✅ Default configuration values correct")
        
        remover.close()
        print("✅ Cleanup successful")
        
    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        return False
    
    return True


def test_browser_setup():
    """Test browser setup."""
    print("\n🧪 Testing browser setup...")
    
    try:
        remover = TikTokRepostRemover(headless=True)
        remover._setup_browser()
        
        print("✅ Browser setup successful")
        
        # Test basic navigation
        remover.driver.get("https://www.google.com")
        assert "Google" in remover.driver.title
        print("✅ Basic navigation works")
        
        remover.close()
        print("✅ Browser cleanup successful")
        
    except Exception as e:
        print(f"❌ Browser setup test failed: {e}")
        return False
    
    return True


def test_image_processing():
    """Test image processing functionality."""
    print("\n🧪 Testing image processing...")
    
    try:
        remover = TikTokRepostRemover()
        
        # Test with dummy video data
        dummy_videos = [
            {'index': 0, 'thumbnail_url': 'https://via.placeholder.com/300x300/FF0000/FFFFFF?text=Test1'},
            {'index': 1, 'thumbnail_url': 'https://via.placeholder.com/300x300/FF0000/FFFFFF?text=Test1'},  # Same as above
            {'index': 2, 'thumbnail_url': 'https://via.placeholder.com/300x300/00FF00/FFFFFF?text=Test2'},
        ]
        
        remover.videos = dummy_videos
        
        # This would normally download and process thumbnails
        # For testing, we'll just check the method exists
        assert hasattr(remover, '_process_thumbnails')
        assert hasattr(remover, '_find_duplicates')
        print("✅ Image processing methods available")
        
        remover.close()
        
    except Exception as e:
        print(f"❌ Image processing test failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test configuration loading."""
    print("\n🧪 Testing configuration...")
    
    try:
        # Test custom configuration
        custom_remover = TikTokRepostRemover(
            similarity_threshold=0.95,
            batch_size=10,
            headless=False
        )
        
        assert custom_remover.similarity_threshold == 0.95
        assert custom_remover.batch_size == 10
        assert custom_remover.headless == False
        print("✅ Custom configuration works")
        
        custom_remover.close()
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True


def test_utility_functions():
    """Test utility functions."""
    print("\n🧪 Testing utility functions...")
    
    try:
        remover = TikTokRepostRemover()
        
        # Test count parsing
        assert remover._parse_count("1.2K") == 1200
        assert remover._parse_count("5.4M") == 5400000
        assert remover._parse_count("1.1B") == 1100000000
        assert remover._parse_count("123") == 123
        print("✅ Count parsing works")
        
        # Test statistics
        stats = remover.get_statistics()
        assert isinstance(stats, dict)
        assert 'total_videos' in stats
        print("✅ Statistics generation works")
        
        remover.close()
        
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("🚀 TikTok Repost Remover - Test Suite")
    print("=" * 50)
    
    tests = [
        test_initialization,
        test_configuration,
        test_utility_functions,
        test_browser_setup,
        test_image_processing,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The tool is ready to use.")
        print("\n💡 Next steps:")
        print("1. Set up your .env file with TikTok credentials")
        print("2. Run: python main.py --dry-run")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("\n🔧 Common solutions:")
        print("- Make sure all dependencies are installed: pip install -r requirements.txt")
        print("- Check your internet connection")
        print("- Try running individual tests to isolate issues")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)