#!/usr/bin/env python3
"""
Setup script for running the Legal Text Correction Chatbot on Google Colab
"""

import os
import sys
import subprocess
import time
import threading
from IPython.display import display, HTML
import warnings
warnings.filterwarnings('ignore')

def install_dependencies():
    """Install required Python packages"""
    print("🔧 Installing dependencies...")
    
    packages = [
        "flask==3.0.0",
        "flask-cors==4.0.0", 
        "google-generativeai==0.3.2",
        "python-dotenv==1.0.0",
        "pyngrok==7.0.0"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
    
    print("✅ Dependencies installed successfully!")

def setup_ngrok():
    """Setup ngrok for public URL access"""
    try:
        from pyngrok import ngrok
        print("🌐 Setting up ngrok tunnel...")
        
        # You can get a free authtoken from https://ngrok.com/
        # Uncomment and add your token here for better stability:
        # ngrok.set_auth_token("YOUR_NGROK_TOKEN")
        
        return ngrok
    except ImportError:
        print("❌ Failed to import pyngrok")
        return None

def setup_gemini_api():
    """Setup Gemini API key"""
    print("\n🔑 Setting up Gemini API...")
    
    # Check if API key is already set
    if 'GEMINI_API_KEY' in os.environ and os.environ['GEMINI_API_KEY']:
        print("✅ Gemini API key already configured!")
        return True
    
    print("Please set your Gemini API key:")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Run this command in a new cell:")
    print("   import os")
    print("   os.environ['GEMINI_API_KEY'] = 'your-api-key-here'")
    print("\nThen run this setup script again.")
    
    return False

def create_app_files():
    """Create the Flask app and HTML template if they don't exist"""
    print("📁 Checking application files...")
    
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Check if files exist
    app_exists = os.path.exists('app.py')
    template_exists = os.path.exists('templates/index.html')
    
    if app_exists and template_exists:
        print("✅ Application files already exist!")
        return True
    else:
        print("❌ Application files missing!")
        print("Please ensure you have:")
        print("- app.py (Flask backend)")
        print("- templates/index.html (Frontend)")
        return False

def run_app_with_tunnel():
    """Run the Flask app with ngrok tunnel"""
    ngrok_module = setup_ngrok()
    
    if not ngrok_module:
        print("❌ Cannot create public tunnel. Running locally only...")
        print("The app will run on http://localhost:5000")
        return
    
    # Start ngrok tunnel
    try:
        public_url = ngrok_module.connect(5000)
        print(f"🌍 Public URL: {public_url}")
        
        # Display clickable link in Colab
        display(HTML(f"""
        <div style='padding: 20px; background: #e8f5e8; border-radius: 10px; margin: 10px 0;'>
            <h3 style='color: #2e7d32; margin-top: 0;'>🎉 Legal Text Correction App is Ready!</h3>
            <p style='font-size: 16px; margin: 10px 0;'>
                <strong>Public URL:</strong> 
                <a href="{public_url}" target="_blank" style='color: #1976d2; text-decoration: none; font-weight: bold;'>
                    {public_url}
                </a>
            </p>
            <p style='color: #666; margin-bottom: 0;'>
                Click the link above to open your legal text correction chatbot!
            </p>
        </div>
        """))
        
    except Exception as e:
        print(f"❌ Failed to create ngrok tunnel: {e}")
        print("Running locally on http://localhost:5000")

def run_flask_app():
    """Run the Flask application"""
    print("🚀 Starting Flask application...")
    
    # Change to the directory containing app.py
    if os.path.exists('app.py'):
        os.environ['FLASK_ENV'] = 'development'
        
        # Start Flask in a separate thread
        def start_flask():
            subprocess.run([sys.executable, 'app.py'])
        
        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()
        
        # Give Flask time to start
        time.sleep(3)
        
        return True
    else:
        print("❌ app.py not found!")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🏛️  LEGAL TEXT CORRECTION CHATBOT - GOOGLE COLAB SETUP")
    print("=" * 60)
    
    # Step 1: Install dependencies
    install_dependencies()
    
    # Step 2: Check Gemini API
    if not setup_gemini_api():
        return False
    
    # Step 3: Check app files
    if not create_app_files():
        return False
    
    # Step 4: Setup tunnel and run app
    run_app_with_tunnel()
    
    # Step 5: Run Flask app
    if run_flask_app():
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("✅ Your legal text correction chatbot is now running!")
        print("=" * 60)
        
        # Display usage instructions
        display(HTML("""
        <div style='padding: 20px; background: #f3e5f5; border-radius: 10px; margin: 20px 0;'>
            <h3 style='color: #7b1fa2; margin-top: 0;'>📖 How to Use</h3>
            <ol style='line-height: 1.6; color: #333;'>
                <li><strong>Click the public URL above</strong> to open the app</li>
                <li><strong>Paste your legal text</strong> in the text area</li>
                <li><strong>Click "Corrigir Texto"</strong> to get the corrected version</li>
                <li>The app will show both <strong>original</strong> and <strong>corrected</strong> versions</li>
            </ol>
            <p style='margin-top: 15px; padding: 10px; background: #fff3e0; border-radius: 5px; color: #e65100;'>
                <strong>💡 Tip:</strong> The app automatically loads with a sample text for testing!
            </p>
        </div>
        """))
        
        return True
    else:
        print("❌ Failed to start Flask application!")
        return False

def quick_test():
    """Quick test function to verify the API is working"""
    print("\n🧪 Running quick API test...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ No API key found for testing")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        test_prompt = "Correct this legal text: O cara não fez o que prometeu no contrato."
        response = model.generate_content(test_prompt)
        
        if response.text:
            print("✅ Gemini API is working correctly!")
            print(f"Sample response: {response.text[:100]}...")
            return True
        else:
            print("❌ No response from Gemini API")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

# For direct execution in Colab
if __name__ == "__main__":
    main()

# Export main function for import
__all__ = ['main', 'quick_test', 'setup_gemini_api']