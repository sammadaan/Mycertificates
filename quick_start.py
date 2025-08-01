#!/usr/bin/env python3
"""
Quick Start Script for Legal Text Correction System
This script helps you get the system running quickly for testing.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("🏛️  LEGAL TEXT CORRECTION SYSTEM - QUICK START")
    print("=" * 60)
    print("Complete Brazilian Legal Text Correction with Data Scraping")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def check_requirements():
    """Check if requirements.txt exists"""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    print("✅ requirements.txt found")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n🔧 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Try running manually: pip install -r requirements.txt")
        return False

def check_api_key():
    """Check if API key is configured"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n🔑 GEMINI API KEY REQUIRED")
        print("=" * 40)
        print("1. Go to: https://makersuite.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Set the environment variable:")
        print()
        if os.name == 'nt':  # Windows
            print("   set GEMINI_API_KEY=your-api-key-here")
        else:  # Unix-like
            print("   export GEMINI_API_KEY=your-api-key-here")
        print()
        print("4. Run this script again")
        return False
    
    print("✅ Gemini API key configured")
    return True

def create_test_config():
    """Create a basic configuration for testing"""
    config = {
        "schedule": {
            "day_of_week": "monday",
            "time": "02:00",
            "timezone": "America/Sao_Paulo"
        },
        "scraping": {
            "limit_per_scraper": 10,  # Reduced for testing
            "max_retries": 2,
            "retry_delay_minutes": 15
        },
        "database": {
            "cleanup_enabled": True,
            "days_to_keep": 30,  # Shorter for testing
            "backup_enabled": False  # Disabled for testing
        },
        "monitoring": {
            "email_notifications": False,  # Disabled for testing
            "webhook_url": None,
            "alert_thresholds": {
                "min_success_rate": 0.5,  # Lower for testing
                "max_error_count": 20
            }
        }
    }
    
    import json
    with open('scheduler_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Test configuration created")

def test_imports():
    """Test if all required modules can be imported"""
    modules = [
        'flask', 'requests', 'beautifulsoup4', 'google.generativeai', 
        'schedule'
    ]
    
    print("\n🧪 Testing imports...")
    failed = []
    
    for module in modules:
        try:
            if module == 'beautifulsoup4':
                import bs4
            elif module == 'google.generativeai':
                import google.generativeai
            else:
                __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        print("Try reinstalling requirements: pip install -r requirements.txt")
        return False
    
    print("✅ All imports successful")
    return True

def run_quick_test():
    """Run a quick test of the system"""
    print("\n🧪 Running quick system test...")
    
    try:
        # Test database creation
        from database import LegalTextDatabase
        db = LegalTextDatabase("test.db")
        print("✅ Database system working")
        
        # Test Gemini API
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content("Test: correct this text: ola mundo")
        if response.text:
            print("✅ Gemini API working")
        else:
            print("❌ Gemini API not responding")
            return False
        
        # Clean up test database
        os.remove("test.db")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def start_application():
    """Start the Flask application"""
    print("\n🚀 Starting Legal Text Correction System...")
    print()
    print("The system will start with the following features:")
    print("• Main correction app: http://localhost:5000")
    print("• Admin dashboard: http://localhost:5000/api/admin/dashboard")
    print("• API health check: http://localhost:5000/api/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Import and run the Flask app
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 System stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")

def show_usage_instructions():
    """Show usage instructions"""
    print("\n📖 USAGE INSTRUCTIONS")
    print("=" * 40)
    print()
    print("🎯 Main Text Correction:")
    print("1. Go to http://localhost:5000")
    print("2. Paste legal text in the textarea")
    print("3. Click 'Corrigir Texto' for correction")
    print()
    print("🔧 Admin Dashboard:")
    print("1. Go to http://localhost:5000/api/admin/dashboard")
    print("2. Monitor system stats and database")
    print("3. Run manual scraping and processing")
    print("4. Search collected legal texts")
    print()
    print("⚙️ Manual Operations:")
    print("# Run manual scraping:")
    print("python scheduler.py --run-once")
    print()
    print("# Process unprocessed texts:")
    print("python data_processor.py --process-unprocessed")
    print()
    print("# Start automated scheduler:")
    print("python scheduler.py --start")
    print()

def main():
    """Main quick start function"""
    print_banner()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_requirements():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check API key
    if not check_api_key():
        return False
    
    # Test imports
    if not test_imports():
        return False
    
    # Create test configuration
    create_test_config()
    
    # Run quick test
    if not run_quick_test():
        return False
    
    print("\n🎉 SYSTEM READY!")
    print("All checks passed. The system is ready to run.")
    
    # Ask if user wants to start
    try:
        start_now = input("\nStart the application now? (y/n): ").lower().strip()
        if start_now in ['y', 'yes']:
            show_usage_instructions()
            start_application()
        else:
            print("\n✅ System is ready. You can start it manually with:")
            print("python app.py")
            print("\nOr use the deployment guide in DEPLOYMENT_GUIDE.md")
    except KeyboardInterrupt:
        print("\n\n👋 Setup completed. Run 'python app.py' to start.")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Quick start failed. Check the errors above.")
        print("For detailed instructions, see DEPLOYMENT_GUIDE.md")
        sys.exit(1)
    else:
        print("\n✅ Quick start completed successfully!")
        sys.exit(0)