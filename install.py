"""
Installation script for TikTok Repost Remover
"""

import subprocess
import sys
import os


def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False


def setup_env_file():
    """Setup environment file."""
    if not os.path.exists('.env'):
        print("\nSetting up environment file...")
        
        # Copy example file
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your TikTok credentials")
        else:
            # Create basic .env file
            with open('.env', 'w') as f:
                f.write("# TikTok Repost Remover Configuration\n")
                f.write("TIKTOK_USERNAME=your_username_here\n")
                f.write("TIKTOK_PASSWORD=your_password_here\n")
            
            print("✅ Created basic .env file")
            print("📝 Please edit .env file with your TikTok credentials")
    else:
        print("✅ .env file already exists")


def main():
    """Main installation process."""
    print("🚀 TikTok Repost Remover Installation")
    print("=" * 40)
    
    # Install packages
    if not install_requirements():
        print("❌ Installation failed!")
        sys.exit(1)
    
    # Setup environment
    setup_env_file()
    
    print("\n" + "=" * 40)
    print("🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your TikTok credentials")
    print("2. Run: python main.py --dry-run (to test)")
    print("3. Run: python main.py (to remove reposts)")
    print("\n💡 For more examples, run: python examples.py")
    print("\n⚠️  Always test with --dry-run first!")


if __name__ == "__main__":
    main()