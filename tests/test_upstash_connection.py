#!/usr/bin/env python3
"""Test Upstash Vector connection and configuration."""

import os
from dotenv import load_dotenv
from upstash_vector import Index

def test_upstash_connection():
    """Test connection to Upstash Vector database."""
    try:
        # Load environment variables from current directory
        load_dotenv('.env')
        
        # Manual fallback - read .env file directly
        if not os.getenv("UPSTASH_VECTOR_REST_URL"):
            print("📝 Manually reading .env file...")
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            value = value.strip('"')  # Remove quotes
                            os.environ[key] = value
        
        # Get credentials
        url = os.getenv("UPSTASH_VECTOR_REST_URL")
        token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        
        # Debug: Print what we found
        print(f"🔍 Debug - URL: {url[:50] if url else 'None'}...")
        print(f"🔍 Debug - Token: {'Found' if token else 'None'}")
        
        if not url or not token:
            raise ValueError("Missing Upstash credentials in .env file")
        
        print(f"🔗 Connecting to Upstash Vector...")
        print(f"📍 URL: {url}")
        
        # Initialize client
        index = Index(url=url, token=token)
        
        # Test connection with info call
        info = index.info()
        print(f"✅ Connection successful!")
        print(f"📊 Index info: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_upstash_connection()
    exit(0 if success else 1)