import os
import json
import requests
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv('../.env')

# Manual fallback for environment variables
if not os.getenv("UPSTASH_VECTOR_REST_URL"):
    try:
        with open('../.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"')
                    os.environ[key] = value
    except FileNotFoundError:
        pass

# Constants (updated for Groq)
JSON_FILE = "../data/food_data.json"
LLM_MODEL = "llama-3.1-8b-instant"  # Groq's fast model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

# Load data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# Setup Upstash Vector (replaces ChromaDB setup)
upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

if not upstash_url or not upstash_token:
    print("❌ Missing Upstash Vector credentials in .env file")
    exit(1)

index = Index(url=upstash_url, token=upstash_token)

# Check if we need to upload data (replaces ChromaDB logic)
info = index.info()
existing_count = info.vector_count

if existing_count == 0:
    print(f"🆕 Adding {len(food_data)} new documents to Upstash Vector...")
    vectors = []
    for item in food_data:
        # Enhance text with region/type (same logic as original)
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."

        vectors.append((
            item["id"],
            enriched_text,  # Upstash will auto-generate embeddings
            {
                "region": item.get("region", "unknown"),
                "type": item.get("type", "general"),
                "original_text": item["text"],  # Store original for retrieval
                "cultural_significance": item.get("cultural_significance", ""),
                "dietary": item.get("dietary", []),
                "allergens": item.get("allergens", [])
            }
        ))

    # Upload in batches
    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
    
    print("✅ All documents added to Upstash Vector.")
else:
    print("✅ All documents already in Upstash Vector.")

# RAG query function with Groq Cloud API
def rag_query(question):
    try:
        # Step 1: Query the vector DB (Upstash handles embedding automatically)
        results = index.query(
            data=question,  # Upstash auto-embeds this
            top_k=3,
            include_metadata=True
        )

        # Step 2: Extract documents (adapting to Upstash response format)
        top_docs = []
        top_ids = []
        
        for result in results:
            metadata = result.metadata if hasattr(result, 'metadata') else {}
            # Use original text for display (same as ChromaDB version)
            original_text = metadata.get('original_text', '')
            if original_text:
                top_docs.append(original_text)
                # Extract ID from metadata or use a default
                doc_id = result.id if hasattr(result, 'id') else f"doc_{len(top_ids)}"
                top_ids.append(doc_id)

        # Step 3: Show friendly explanation of retrieved documents (exact same format)
        print("\n🧠 Retrieving relevant information to reason through your question...\n")

        for i, doc in enumerate(top_docs):
            print(f"🔹 Source {i + 1} (ID: {top_ids[i]}):")
            print(f"    \"{doc}\"\n")

        print("📚 These seem to be the most relevant pieces of information to answer your question.\n")

        # Step 4: Build prompt from context (same as original)
        context = "\n".join(top_docs)

        # Step 5: Generate answer with Groq Cloud API
        try:
            completion = groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful food expert. Use the provided context to answer questions about food accurately and concisely. Keep your responses informative but not too long."},
                    {"role": "user", "content": f"""Use the following context to answer the question.

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
            
            # Step 6: Return final result
            response_text = completion.choices[0].message.content.strip()
            
            # Log usage for monitoring (optional)
            usage = completion.usage
            print(f"🔍 Groq usage - Input tokens: {usage.prompt_tokens}, Output tokens: {usage.completion_tokens}")
            
            return response_text
        
        except Exception as groq_error:
            print(f"❌ Groq API error: {groq_error}")
            # Fallback response using context
            if top_docs:
                return f"Based on the available information: {top_docs[0][:200]}..."
            else:
                return "I couldn't find relevant information to answer your question."
            
    except Exception as e:
        print(f"❌ Error during RAG query: {e}")
        return "Sorry, I encountered an error while processing your question. Please try again."


# Interactive loop with Groq Cloud API
print("\n🧠 Cloud RAG System (Upstash + Groq) ready! Ask a question (type 'exit' to quit):\n")
while True:
    try:
        question = input("You: ")
        if question.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        if question.strip() == "":
            print("Please ask a question.")
            continue
        answer = rag_query(question)
        print("🤖:", answer)
        print()  # Add blank line for better formatting
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Please try again or type 'exit' to quit.")