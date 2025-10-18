#!/usr/bin/env python3
"""
Test script to verify the environment and run the AI Assistant
"""
import sys
import os
import subprocess

def main():
    print("🚀 AI Assistant Environment Test")
    print("=" * 50)
    
    # Check Python version
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Directory: {os.getcwd()}")
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")
    
    # Test imports
    print("\nTesting imports...")
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy: {e}")
        return False
    
    print("\n🎉 Environment looks good!")
    print("\nStarting AI Assistant...")
    print("🌐 Server will start at: http://localhost:8002")
    print("Press Ctrl+C to stop\n")
    
    # Import and run the main application
    try:
        import simple_main
        print("✅ Application started successfully!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()