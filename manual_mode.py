#!/usr/bin/env python3
"""
Manual Login Helper for TikTok Repost Remover
This script opens TikTok and lets you log in manually, then continues with repost detection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tiktok_repost_remover import TikTokRepostRemover
from selenium.webdriver.common.by import By
import time


def manual_login_and_scan():
    """Manual login process with guided steps for TikTok reposts removal."""
    print("🚀 TikTok Repost Remover - Manual Mode")
    print("=" * 50)
    print("This mode removes TikTok REPOSTS (videos you've shared from other creators).")
    print("Reposts appear with a 'repost' label and are found in your Reposts tab.")
    print()
    
    # Get username for profile navigation
    username = input("Enter your TikTok username (without @): ")
    if not username:
        print("Username is required!")
        return False
    
    print("\n📋 Manual Process:")
    print("1. Browser will open to TikTok")
    print("2. You log in manually (handle any verification)")
    print("3. Navigate to your profile's Reposts tab")
    print("4. Press Enter here to continue scanning")
    print("5. Tool will remove all your reposts")
    print()
    
    print("⚠️  NOTE: This will remove videos you've reposted from other creators!")
    print("         Your original videos will NOT be affected.")
    print()
    
    input("Press Enter to open TikTok...")
    
    try:
        # Initialize browser (non-headless)
        remover = TikTokRepostRemover(headless=False)
        remover._setup_browser()
        
        # Navigate to TikTok
        print("🌐 Opening TikTok...")
        remover.driver.get("https://www.tiktok.com/login")
        time.sleep(3)
        
        print("\n🔐 MANUAL LOGIN STEP:")
        print("1. Complete login in the browser window")
        print("2. Handle any verification challenges")
        print("3. Make sure you're logged in successfully")
        input("Press Enter when you're logged in...")
        
        # Navigate to profile and reposts tab
        print(f"🏠 Navigating to profile @{username} reposts tab...")
        if not remover.navigate_to_reposts_tab(username):
            print("❌ Could not find reposts tab. This could mean:")
            print("   - You have no reposts")
            print("   - Your profile structure is different")
            print("   - TikTok changed their layout")
            print("\n🔧 Manual navigation:")
            print("1. Go to your profile")
            print("2. Click on the 'Reposts' tab")
            input("Press Enter when you're viewing your reposts...")
        
        # Collect reposts
        print("\n🔍 Scanning for reposts...")
        try:
            reposts = remover.collect_reposts()
            print(f"📹 Found {len(reposts)} reposts")
            
            if len(reposts) == 0:
                print("🎉 No reposts found! Your profile doesn't have any shared content.")
                print("\nWhat are TikTok reposts?")
                print("- Videos you've shared from other creators to your profile")
                print("- They appear with a 'repost' label")
                print("- Found in the 'Reposts' tab on your profile")
                return True
            
            # Show repost details
            print(f"\n📊 REPOSTS FOUND:")
            for i, repost in enumerate(reposts, 1):
                title = repost.get('title', 'Untitled')[:40]
                creator = repost.get('original_creator', 'Unknown creator')
                url = repost.get('url', 'No URL')
                
                print(f"\n{i}. {title}")
                print(f"   Original creator: {creator}")
                print(f"   URL: {url}")
            
            print(f"\n🎯 SUMMARY:")
            print(f"Total reposts found: {len(reposts)}")
            print("These are videos you've shared from other creators.")
            print("Your original content will NOT be affected.")
            
            # Ask what to do
            print("\n🤔 What would you like to do?")
            print("1. Remove ALL reposts")
            print("2. Choose which reposts to remove")
            print("3. Save report and exit (no changes)")
            
            choice = input("Enter choice (1-3): ").strip()
            
            if choice == "1":
                print("\n🧹 Removing all reposts...")
                print("⚠️  This will remove all videos you've reposted from other creators!")
                confirm = input("Type 'yes' to confirm: ")
                if confirm.lower() == 'yes':
                    removed_reposts = remover.remove_all_reposts(dry_run=False)
                    print(f"✅ Removed {len(removed_reposts)} reposts")
                    
                    # Save report
                    report_file = remover.save_report()
                    print(f"📄 Report saved to: {report_file}")
                else:
                    print("❌ Removal cancelled")
            
            elif choice == "2":
                # Manual selection mode
                print("\n🎯 Manual Selection Mode:")
                removed_reposts = []
                
                for i, repost in enumerate(reposts, 1):
                    title = repost.get('title', 'Untitled')[:50]
                    creator = repost.get('original_creator', 'Unknown')
                    url = repost.get('url', 'No URL')
                    
                    print(f"\n--- Repost {i}/{len(reposts)} ---")
                    print(f"Title: {title}")
                    print(f"Original creator: {creator}")
                    print(f"URL: {url}")
                    
                    choice = input("Remove this repost? (y/n/q to quit): ").lower()
                    if choice == 'y':
                        if remover._delete_repost(repost):
                            removed_reposts.append(repost)
                            print("✅ Removed")
                        else:
                            print("❌ Failed to remove")
                    elif choice == 'q':
                        break
                
                print(f"\n✅ Manual removal complete: {len(removed_reposts)} reposts removed")
            
            elif choice == "3":
                # Save report only
                report_file = remover.save_report()
                print(f"📄 Report saved to: {report_file}")
                print("No reposts were modified.")
            
            # Don't close browser automatically - let user control it
            print("\n🌐 Browser will remain open for you to verify the changes.")
            print("You can:")
            print("- Check your profile to see the reposts have been removed")
            print("- Navigate to other parts of TikTok")
            print("- Close the browser manually when done")
            input("\nPress Enter to close this program (browser will stay open)...")
            
        except Exception as e:
            print(f"❌ Error during scanning: {str(e)}")
            print("This might be due to:")
            print("- TikTok page structure changes")
            print("- Network issues")
            print("- Reposts tab not accessible")
            
            # Keep browser open even on error for debugging
            print("\n🌐 Browser will remain open for debugging.")
            input("Press Enter to close this program (browser will stay open)...")
            return False
        
        # Don't close browser - let user control it
        print("\n🎉 Process completed! Browser remains open for your use.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = manual_login_and_scan()
        if success:
            print("\n🎉 Manual process completed successfully!")
        else:
            print("\n❌ Process failed. Check the error messages above.")
    except KeyboardInterrupt:
        print("\n⚠️  Process cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("Please check the SETUP_GUIDE.md for troubleshooting steps.")