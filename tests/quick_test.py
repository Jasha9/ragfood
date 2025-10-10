#!/usr/bin/env python3
"""
Quick test to validate the fixed RAG system
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_connections():
    """Test all connections and components"""
    
    print("🔍 Testing RAG System Components...\n")
    
    # Test 1: Environment Variables
    print("1. Checking Environment Variables:")
    groq_key = os.getenv("GROQ_API_KEY")
    upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
    upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    if groq_key:
        print("   ✅ GROQ_API_KEY found")
    else:
        print("   ❌ GROQ_API_KEY missing")
        return False
        
    if upstash_url and upstash_token:
        print("   ✅ Upstash Vector credentials found")
    else:
        print("   ❌ Upstash Vector credentials missing")
        return False
    
    # Test 2: Import Dependencies
    print("\n2. Testing Package Imports:")
    try:
        from upstash_vector import Index
        print("   ✅ upstash-vector imported successfully")
    except ImportError as e:
        print(f"   ❌ upstash-vector import failed: {e}")
        return False
        
    try:
        from groq import Groq
        print("   ✅ groq imported successfully")
    except ImportError as e:
        print(f"   ❌ groq import failed: {e}")
        return False
    
    # Test 3: Groq Connection
    print("\n3. Testing Groq Cloud API:")
    try:
        client = Groq(api_key=groq_key)
        # Simple test call
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Hello' in one word"}],
            max_completion_tokens=10
        )
        print("   ✅ Groq API connection successful")
        print(f"   📊 Response: {completion.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"   ❌ Groq API connection failed: {e}")
        return False
    
    # Test 4: Upstash Vector Connection
    print("\n4. Testing Upstash Vector Database:")
    try:
        index = Index(url=upstash_url, token=upstash_token)
        info = index.info()
        print(f"   ✅ Upstash Vector connection successful")
        print(f"   📊 Vector count: {info.vector_count}")
    except Exception as e:
        print(f"   ❌ Upstash Vector connection failed: {e}")
        return False
    
    # Test 5: Data File
    print("\n5. Checking Data File:")
    try:
        import json
        with open("foods.json", "r", encoding="utf-8") as f:
            food_data = json.load(f)
        print(f"   ✅ foods.json loaded successfully ({len(food_data)} items)")
    except Exception as e:
        print(f"   ❌ foods.json loading failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Your RAG system is ready to use.")
    return True

if __name__ == "__main__":
    if test_connections():
        print("\n✅ No problems found in your code!")
        print("🚀 You can now run: python rag_run.py")
    else:
        print("\n❌ Problems detected. Please check the errors above.")
        sys.exit(1)