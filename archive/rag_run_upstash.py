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
UPSTASH_READONLY_TOKEN = os.getenv("UPSTASH_VECTOR_REST_READONLY_TOKEN")
JSON_FILE = os.getenv("JSON_FILE", "foods.json")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "3"))
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class UpstashError(Exception):
    """Base exception for Upstash operations."""
    pass

class RateLimitError(UpstashError):
    """Raised when API rate limit is exceeded."""
    pass

class AuthenticationError(UpstashError):
    """Raised when API authentication fails."""
    pass

def with_retry(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator for implementing exponential backoff retry logic."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, RateLimitError) as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
                    print(f"⏳ Retry {attempt + 1}/{max_retries} in {wait_time}s...")
            return None
        return wrapper
    return decorator

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

@with_retry(max_retries=3)
def safe_upsert(index: Index, vectors: List[tuple]) -> None:
    """Perform upsert with automatic retry logic."""
    try:
        return index.upsert(vectors=vectors)
    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg:
            raise RateLimitError(f"Rate limit exceeded: {e}")
        elif "auth" in error_msg:
            raise AuthenticationError(f"Authentication failed: {e}")
        else:
            raise UpstashError(f"Upsert failed: {e}")

@with_retry(max_retries=3)
def safe_query(index: Index, query_data: str, **kwargs):
    """Perform query with automatic retry logic."""
    try:
        return index.query(data=query_data, **kwargs)
    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg:
            raise RateLimitError(f"Rate limit exceeded: {e}")
        elif "auth" in error_msg:
            raise AuthenticationError(f"Authentication failed: {e}")
        else:
            raise UpstashError(f"Query failed: {e}")

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
        # Check existing vectors to avoid duplicates
        info = index.info()
        existing_count = info.vector_count
        
        print(f"📊 Current vectors in index: {existing_count}")
        
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
        
        # Batch upsert (process in chunks for large datasets)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            safe_upsert(index, batch)
            print(f"✅ Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
        
        # Verify upsert
        final_info = index.info()
        print(f"📊 Final vector count: {final_info.vector_count}")
        print(f"🎉 Successfully upserted food data!")
        
    except Exception as e:
        raise RuntimeError(f"Failed to upsert data: {e}")

def enhanced_rag_query(index: Index, question: str) -> str:
    """Perform RAG query using Upstash Vector with enhanced error handling."""
    try:
        print(f"\n🔍 Processing query: '{question}'")
        
        # Query vector database
        results = safe_query(
            index, 
            question,
            top_k=MAX_RESULTS,
            include_metadata=True,
            include_vectors=False  # Don't need vectors in response
        )
        
        if not results or len(results) == 0:
            return "No relevant information found for your question."
        
        # Extract documents and metadata
        contexts = []
        print("\n🧠 Retrieved relevant information:\n")
        
        for i, result in enumerate(results, 1):
            # Access Upstash QueryResult attributes correctly
            metadata = result.metadata or {}
            original_text = metadata.get('original_text', '')
            region = metadata.get('region', 'unknown')
            food_type = metadata.get('type', 'general')
            score = result.score or 0
            
            contexts.append({
                'text': original_text,
                'region': region,
                'type': food_type,
                'score': score
            })
            
            print(f"🔹 Source {i} (Region: {region}, Type: {food_type}, Score: {score:.3f}):")
            print(f"    \"{original_text}\"\n")
        
        print("📚 Using this information to generate your answer...\n")
        
        # Generate response using LLM
        context_text = "\n".join([ctx['text'] for ctx in contexts])
        return generate_llm_response(question, context_text)
        
    except Exception as e:
        print(f"❌ Error during RAG query: {e}")
        return "Sorry, I encountered an error while processing your question. Please try again."

def generate_llm_response(question: str, context: str) -> str:
    """Generate response using Ollama LLM."""
    try:
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        response = requests.post(f"{OLLAMA_HOST}/api/generate", json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        })
        
        response.raise_for_status()
        return response.json()["response"].strip()
    
    except Exception as e:
        print(f"❌ Error generating LLM response: {e}")
        return "Sorry, I couldn't generate a response. Please try again."

def main():
    """Main function to run the RAG system."""
    try:
        print("🚀 Initializing Upstash Vector RAG System...\n")
        
        # Initialize Upstash Vector client
        index = initialize_upstash_client()
        
        # Load food data
        food_data = load_and_process_food_data()
        
        # Upsert data (this will handle duplicates automatically)
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
                
                answer = enhanced_rag_query(index, question)
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