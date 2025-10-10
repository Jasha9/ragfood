#!/usr/bin/env python3
"""Simplified RAG system that shows retrieval working without LLM generation."""

import os
import json
import time
import requests
from dotenv import load_dotenv
from upstash_vector import Index
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv('.env')

# Manual fallback for environment variables (in case load_dotenv doesn't work)
if not os.getenv("UPSTASH_VECTOR_REST_URL"):
    print("📝 Manually loading environment variables...")
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"')  # Remove quotes
                    os.environ[key] = value
    except FileNotFoundError:
        print("❌ .env file not found!")

# Configuration from environment variables
UPSTASH_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
JSON_FILE = os.getenv("JSON_FILE", "foods.json")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "3"))

def initialize_upstash_client() -> Index:
    """Initialize Upstash Vector client with proper error handling."""
    try:
        if not UPSTASH_URL or not UPSTASH_TOKEN:
            raise ValueError("Missing Upstash credentials in environment variables")
        
        print(f"🔗 Connecting to Upstash Vector...")
        print(f"📍 URL: {UPSTASH_URL}")
        
        index = Index(
            url=UPSTASH_URL,
            token=UPSTASH_TOKEN
        )
        
        # Test connectivity
        info = index.info()
        print(f"✅ Connected to Upstash Vector!")
        print(f"📊 Vector count: {info.vector_count}, Dimensions: {info.dimension}")
        print(f"🤖 Embedding model: {info.dense_index.embedding_model}")
        
        return index
    
    except Exception as e:
        raise ConnectionError(f"Failed to initialize Upstash client: {e}")

def load_and_process_food_data() -> List[Dict[str, Any]]:
    """Load and process food data from JSON file."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            food_data = json.load(f)
        
        print(f"📋 Loaded {len(food_data)} food items from {JSON_FILE}")
        return food_data
    
    except FileNotFoundError:
        print(f"❌ Food data file '{JSON_FILE}' not found!")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON file: {e}")
        return []

def upsert_food_data(index: Index, food_data: List[Dict[str, Any]]) -> None:
    """Upsert food data with metadata to Upstash Vector."""
    if not food_data:
        print("⚠️ No food data to upsert")
        return
    
    try:
        # Check existing vectors
        info = index.info()
        if info.vector_count > 0:
            print(f"📊 Found {info.vector_count} existing vectors, skipping upsert")
            return
        
        # Prepare data for batch upsert
        vectors = []
        for item in food_data:
            # Create enriched text for better embeddings
            enriched_text = item["text"]
            if "region" in item:
                enriched_text += f" This food is popular in {item['region']}."
            if "type" in item:
                enriched_text += f" It is a type of {item['type']}."
            
            vectors.append((
                item["id"],
                enriched_text,  # Upstash will automatically generate embeddings
                {
                    "region": item.get("region", "unknown"),
                    "type": item.get("type", "general"),
                    "original_text": item["text"]
                }
            ))
        
        print(f"🚀 Upserting {len(vectors)} food items to Upstash Vector...")
        
        # Batch upsert
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            index.upsert(vectors=batch)
            print(f"✅ Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
        
        # Verify upsert
        final_info = index.info()
        print(f"📊 Final vector count: {final_info.vector_count}")
        print(f"🎉 Successfully upserted food data!")
        
    except Exception as e:
        raise RuntimeError(f"Failed to upsert data: {e}")

def simple_rag_query(index: Index, question: str) -> str:
    """Perform RAG query and return retrieved contexts without LLM generation."""
    try:
        print(f"\n🔍 Processing query: '{question}'")
        
        # Query vector database
        results = index.query(
            data=question,
            top_k=MAX_RESULTS,
            include_metadata=True,
            include_vectors=False
        )
        
        if not results or len(results) == 0:
            return "No relevant information found for your question."
        
        print("\n🧠 Retrieved relevant information:\n")
        
        # Format retrieved contexts
        contexts = []
        for i, result in enumerate(results, 1):
            metadata = result.metadata or {}
            original_text = metadata.get('original_text', '')
            region = metadata.get('region', 'unknown')
            food_type = metadata.get('type', 'general')
            score = result.score or 0
            
            contexts.append(original_text)
            
            print(f"🔹 Source {i} (Region: {region}, Type: {food_type}, Score: {score:.3f}):")
            print(f"    \"{original_text[:200]}...\"\n")
        
        # Return a simple summary instead of LLM generation
        response = f"""Based on the retrieved information, here are some relevant food items related to your query:

{chr(10).join([f"• {ctx[:150]}..." for ctx in contexts])}

Note: This is the raw retrieved information. For a more natural response, an LLM would process this context."""
        
        return response
        
    except Exception as e:
        print(f"❌ Error during RAG query: {e}")
        return "Sorry, I encountered an error while processing your question. Please try again."

def main():
    """Main function to run the simplified RAG system."""
    try:
        print("🚀 Initializing Upstash Vector RAG System...\n")
        
        # Initialize Upstash Vector client
        index = initialize_upstash_client()
        
        # Load food data
        food_data = load_and_process_food_data()
        
        # Upsert data if needed
        if food_data:
            upsert_food_data(index, food_data)
        
        print("\n🧠 RAG system is ready! Ask a question (type 'exit' to quit):\n")
        
        # Interactive loop
        while True:
            try:
                question = input("You: ").strip()
                if question.lower() in ["exit", "quit"]:
                    print("👋 Goodbye!")
                    break
                if question == "":
                    print("Please ask a question.")
                    continue
                
                answer = simple_rag_query(index, question)
                print(f"🤖: {answer}")
                print()  # Add blank line for better formatting
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Please try again or type 'exit' to quit.")
    
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        print("Check your configuration and try again.")

if __name__ == "__main__":
    main()