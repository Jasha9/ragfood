#!/usr/bin/env python3
"""Test the fixed RAG query system."""

import sys
import os
from dotenv import load_dotenv
from upstash_vector import Index

# Import our functions
sys.path.append('.')
from rag_run_upstash import initialize_upstash_client, enhanced_rag_query

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

try:
    # Initialize client
    index = initialize_upstash_client()
    
    # Test the enhanced RAG query
    print("\n" + "="*60)
    print("Testing Enhanced RAG Query System")
    print("="*60)
    
    question = "What are some good breakfast foods?"
    answer = enhanced_rag_query(index, question)
    
    print(f"\nFinal Answer: {answer}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()