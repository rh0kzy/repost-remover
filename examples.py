#!/usr/bin/env python3
"""
Example usage scripts for TikTok Repost Remover
"""

from tiktok_repost_remover import TikTokRepostRemover
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")
    
    # Get credentials from environment or user input
    username = os.getenv('TIKTOK_USERNAME') or input("Username: ")
    password = os.getenv('TIKTOK_PASSWORD') or input("Password: ")
    
    # Initialize and use the remover
    with TikTokRepostRemover() as remover:
        # Login
        if remover.login(username, password):
            print("✅ Login successful!")
            
            # Scan for reposts (dry run)
            reposts = remover.scan_for_reposts()
            print(f"Found {len(reposts)} potential reposts")
            
            # Optionally remove them
            if reposts and input("Remove reposts? (y/n): ").lower() == 'y':
                removed = remover.remove_all_reposts()
                print(f"Removed {len(removed)} videos")
        else:
            print("❌ Login failed!")


def advanced_usage():
    """Advanced usage with custom settings."""
    print("=== Advanced Usage Example ===")
    
    username = os.getenv('TIKTOK_USERNAME') or input("Username: ")
    password = os.getenv('TIKTOK_PASSWORD') or input("Password: ")
    
    # Custom configuration
    remover = TikTokRepostRemover(
        similarity_threshold=0.95,  # Very strict similarity
        batch_size=10,              # Process more videos at once
        headless=False              # Show browser window
    )
    
    try:
        # Login
        if not remover.login(username, password):
            print("❌ Login failed!")
            return
        
        print("✅ Login successful!")
        
        # Navigate to profile
        if not remover.navigate_to_profile():
            print("❌ Failed to navigate to profile!")
            return
        
        # Collect videos
        videos = remover.collect_videos()
        print(f"📹 Collected {len(videos)} videos")
        
        # Analyze for duplicates
        duplicates = remover.analyze_videos()
        print(f"🔍 Found {len(duplicates)} duplicate groups")
        
        # Show duplicate groups
        for group_name, group_videos in duplicates.items():
            print(f"\n{group_name}: {len(group_videos)} videos")
            for video in group_videos:
                print(f"  - {video.get('title', 'Untitled')[:50]}...")
        
        # Remove duplicates with confirmation
        if duplicates:
            choice = input(f"\nRemove duplicates from {len(duplicates)} groups? (y/n): ")
            if choice.lower() == 'y':
                removed_videos = []
                for group_videos in duplicates.values():
                    # Keep the first (most popular) and remove the rest
                    to_remove = group_videos[1:]
                    removed = remover.remove_specific_reposts(to_remove)
                    removed_videos.extend(removed)
                
                print(f"✅ Removed {len(removed_videos)} duplicate videos")
                
                # Save report
                report_file = remover.save_report()
                print(f"📄 Report saved to: {report_file}")
        
        # Show final statistics
        stats = remover.get_statistics()
        print(f"\n📊 Final Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    finally:
        remover.close()


def selective_removal():
    """Example of selective repost removal."""
    print("=== Selective Removal Example ===")
    
    username = os.getenv('TIKTOK_USERNAME') or input("Username: ")
    password = os.getenv('TIKTOK_PASSWORD') or input("Password: ")
    
    with TikTokRepostRemover() as remover:
        if not remover.login(username, password):
            print("❌ Login failed!")
            return
        
        # Scan for reposts
        reposts = remover.scan_for_reposts()
        
        if not reposts:
            print("🎉 No reposts found!")
            return
        
        print(f"Found {len(reposts)} potential reposts:")
        
        # Let user select which ones to remove
        selected_reposts = []
        for i, video in enumerate(reposts):
            title = video.get('title', 'Untitled')[:50]
            url = video.get('url', 'No URL')
            likes = video.get('likes', 0)
            views = video.get('views', 0)
            
            print(f"\n{i+1}. {title}")
            print(f"    URL: {url}")
            print(f"    Engagement: {likes} likes, {views} views")
            
            choice = input("    Remove this video? (y/n/q to quit): ").lower()
            if choice == 'y':
                selected_reposts.append(video)
            elif choice == 'q':
                break
        
        # Remove selected videos
        if selected_reposts:
            print(f"\nRemoving {len(selected_reposts)} selected videos...")
            removed = remover.remove_specific_reposts(selected_reposts)
            print(f"✅ Successfully removed {len(removed)} videos")
        else:
            print("No videos selected for removal.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == "basic":
            basic_usage()
        elif example == "advanced":
            advanced_usage()
        elif example == "selective":
            selective_removal()
        else:
            print("Available examples: basic, advanced, selective")
    else:
        print("Choose an example:")
        print("1. Basic usage")
        print("2. Advanced usage")
        print("3. Selective removal")
        
        choice = input("\nEnter choice (1-3): ")
        if choice == "1":
            basic_usage()
        elif choice == "2":
            advanced_usage()
        elif choice == "3":
            selective_removal()
        else:
            print("Invalid choice")