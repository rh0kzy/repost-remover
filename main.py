#!/usr/bin/env python3
"""
TikTok Repost Remover - Simple CLI Interface
"""

import os
import sys
import argparse
import getpass
from dotenv import load_dotenv
from tiktok_repost_remover import TikTokRepostRemover


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='TikTok Repost Remover')
    parser.add_argument('--username', '-u', help='TikTok username')
    parser.add_argument('--password', '-p', help='TikTok password (will prompt if not provided)')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Scan only, don\'t delete videos')
    parser.add_argument('--threshold', '-t', type=float, default=0.9, help='Similarity threshold (0.0-1.0)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    parser.add_argument('--config', '-c', help='Load credentials from .env file')
    
    args = parser.parse_args()
    
    # Load environment variables if specified
    if args.config:
        load_dotenv(args.config)
    else:
        load_dotenv()  # Load from default .env file
    
    # Get credentials
    username = args.username or os.getenv('TIKTOK_USERNAME')
    password = args.password or os.getenv('TIKTOK_PASSWORD')
    
    if not username:
        username = input("Enter your TikTok username/email: ")
    
    if not password:
        password = getpass.getpass("Enter your TikTok password: ")
    
    if not username or not password:
        print("Error: Username and password are required!")
        sys.exit(1)
    
    # Determine headless mode
    headless = True  # Default
    if args.no_headless:
        headless = False
    elif args.headless:
        headless = True
    
    print("🚀 Starting TikTok Repost Remover...")
    print(f"   Username: {username}")
    print(f"   Threshold: {args.threshold}")
    print(f"   Headless: {headless}")
    print(f"   Dry Run: {args.dry_run}")
    print()
    
    try:
        # Initialize remover
        with TikTokRepostRemover(
            similarity_threshold=args.threshold,
            headless=headless
        ) as remover:
            
            # Login
            print("🔐 Logging in...")
            if not remover.login(username, password):
                print("❌ Login failed!")
                sys.exit(1)
            
            print("✅ Login successful!")
            
            # Scan and remove reposts
            if args.dry_run:
                print("🔍 Scanning for reposts (dry run)...")
                reposts = remover.scan_for_reposts()
                
                if reposts:
                    print(f"📊 Found {len(reposts)} potential reposts:")
                    for i, video in enumerate(reposts, 1):
                        print(f"   {i}. {video.get('title', 'Untitled')} - {video.get('url', 'No URL')}")
                    
                    print("\n💡 Run without --dry-run to remove these videos.")
                else:
                    print("🎉 No reposts found!")
            
            else:
                print("🧹 Removing all reposts...")
                
                # Ask for confirmation
                confirm = input("Are you sure you want to delete reposts? This cannot be undone! (yes/no): ")
                if confirm.lower() not in ['yes', 'y']:
                    print("❌ Operation cancelled.")
                    sys.exit(0)
                
                removed_videos = remover.remove_all_reposts()
                
                if removed_videos:
                    print(f"✅ Successfully removed {len(removed_videos)} reposts!")
                    
                    # Save report
                    report_file = remover.save_report()
                    print(f"📄 Report saved to: {report_file}")
                else:
                    print("🎉 No reposts found to remove!")
            
            # Show statistics
            stats = remover.get_statistics()
            print(f"\n📈 Statistics:")
            print(f"   Total videos: {stats['total_videos']}")
            print(f"   Videos analyzed: {stats['videos_with_hashes']}")
            print(f"   Videos deleted: {stats['deleted_videos']}")
            print(f"   Similarity threshold: {stats['similarity_threshold']}")
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()