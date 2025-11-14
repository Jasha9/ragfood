#!/usr/bin/env python3
"""
Updated RAG Food Assistant - Using 'foods' namespace
===================================================

This version uses the dedicated 'foods' namespace in Upstash Vector
to keep food data separate from other application data.

Author: Jasha9
Date: November 2025
"""

import os
import json
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv('.env')

# Manual fallback for environment variables
if not os.getenv("UPSTASH_VECTOR_REST_URL"):
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"')
                    os.environ[key] = value
    except FileNotFoundError:
        pass

# Constants
JSON_FILE = "foods.json"
LLM_MODEL = "llama-3.1-8b-instant"  # Groq's fast model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FOODS_NAMESPACE = "foods"  # Dedicated namespace for food data

# Initialize Groq client
if not GROQ_API_KEY:
    print("❌ Missing GROQ_API_KEY in .env file")
    exit(1)

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq Cloud API client initialized successfully!")
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    exit(1)

# Setup Upstash Vector
upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

if not upstash_url or not upstash_token:
    print("❌ Missing Upstash Vector credentials in .env file")
    exit(1)

# Initialize Upstash Vector client
index = Index(url=upstash_url, token=upstash_token)

# Check if foods data exists in the foods namespace
def check_foods_data():
    try:
        # Test query in foods namespace
        test_results = index.query(
            data="test query",
            namespace=FOODS_NAMESPACE,
            top_k=1,
            include_metadata=True
        )
        return len(test_results) > 0
    except:
        return False

# Load local data for fallback (optional)
def load_local_food_data():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

print(f"🔍 Checking for food data in '{FOODS_NAMESPACE}' namespace...")

if check_foods_data():
    print(f"✅ Food data found in '{FOODS_NAMESPACE}' namespace. Ready to query!")
else:
    print(f"⚠️  No food data found in '{FOODS_NAMESPACE}' namespace.")
    print("💡 Suggestion: Run 'python migrate_to_upstash_foods.py' to migrate your data.")
    
    # Optional: Load local data as fallback
    food_data = load_local_food_data()
    if food_data:
        print(f"📊 Loaded {len(food_data)} items from local JSON as fallback.")
    else:
        print("❌ No local food data available either.")
        exit(1)

# RAG query function using foods namespace
def rag_query(question):
    try:
        print(f"\n🧠 Searching in '{FOODS_NAMESPACE}' namespace for: '{question}'\n")
        
        # Step 1: Query the foods namespace specifically
        results = index.query(
            data=question,  # Upstash auto-embeds this
            namespace=FOODS_NAMESPACE,  # Use dedicated foods namespace
            top_k=3,
            include_metadata=True
        )

        # Step 2: Extract documents
        top_docs = []
        top_ids = []
        
        for result in results:
            metadata = result.metadata if hasattr(result, 'metadata') else {}
            # Use original text for display
            original_text = metadata.get('original_text', '')
            if original_text:
                top_docs.append(original_text)
                # Extract ID from metadata
                doc_id = result.id if hasattr(result, 'id') else f"doc_{len(top_ids)}"
                top_ids.append(doc_id)

        if not top_docs:
            return "❌ No relevant food information found in the database."

        # Step 3: Show retrieved documents
        print("🧠 Retrieving relevant information from foods database...\n")

        for i, doc in enumerate(top_docs):
            print(f"🔹 Source {i + 1} (ID: {top_ids[i]}):")
            print(f"    \"{doc[:200]}{'...' if len(doc) > 200 else ''}\"\n")

        # Step 4: Build context and generate response
        context = "\n".join(top_docs)

        # Step 5: Generate answer with Groq
        try:
            completion = groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful food expert. Use the provided context to answer questions about food accurately and informatively. Include cultural context and interesting details when relevant."},
                    {"role": "user", "content": f"""Use the following context to answer the question about food.

Context:
{context}

Question: {question}
Answer:"""}
                ],
                temperature=0.7,
                max_completion_tokens=500,
                top_p=1.0,
                stream=False
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Log usage
            usage = completion.usage
            print(f"🔍 Groq usage - Input: {usage.prompt_tokens} tokens, Output: {usage.completion_tokens} tokens")
            
            return response_text
            
        except Exception as e:
            return f"❌ Error generating response: {e}"
        
    except Exception as e:
        return f"❌ Error querying foods database: {e}"

# Interactive loop
def main():
    print(f"\n🍽️ RAG Food Assistant - Using '{FOODS_NAMESPACE}' Namespace")
    print("=" * 60)
    print("🔍 Ask questions about food, recipes, nutrition, or culinary traditions!")
    print("💡 Examples: 'Tell me about Italian pasta', 'What are healthy breakfast options?'")
    print("🚪 Type 'exit' to quit\n")

    while True:
        try:
            question = input("You: ").strip()
            
            if question.lower() in ['exit', 'quit', 'bye']:
                print("👋 Thanks for using RAG Food Assistant! Goodbye!")
                break
            
            if not question:
                print("❓ Please ask a question about food.\n")
                continue
            
            # Get answer from RAG system
            answer = rag_query(question)
            print(f"\n🤖 {answer}\n")
            print("-" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()