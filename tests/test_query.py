#!/usr/bin/env python3
"""Test the Upstash RAG system with a single query."""

import sys
import os
from dotenv import load_dotenv
from upstash_vector import Index

# Load environment
load_dotenv('.env')

# Manual fallback
if not os.getenv("UPSTASH_VECTOR_REST_URL"):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                value = value.strip('"')
                os.environ[key] = value

# Initialize client
UPSTASH_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

try:
    index = Index(url=UPSTASH_URL, token=UPSTASH_TOKEN)
    
    # Test query
    print("🔍 Testing query...")
    results = index.query(
        data="What are good breakfast foods?",
        top_k=3,
        include_metadata=True
    )
    
    print(f"📊 Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Result: {result}")
        # Try to access attributes instead of dict methods
        try:
            metadata = getattr(result, 'metadata', {})
            original_text = metadata.get('original_text', 'No text') if metadata else 'No text'
            score = getattr(result, 'score', 0)
            print(f"   Score: {score:.3f} - {original_text[:100]}...")
        except Exception as e:
            print(f"   Error parsing result: {e}")

except Exception as e:
    print(f"❌ Error: {e}")