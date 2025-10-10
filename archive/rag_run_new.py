import os
import json
import requests
from dotenv import load_dotenv
from upstash_vector import Index

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

# Constants (keeping original variable names for compatibility)
JSON_FILE = "foods.json"
LLM_MODEL = "llama3.2"
UPSTASH_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

class RAGSystem:
    """RAG System using Upstash Vector for semantic search."""
    
    def __init__(self):
        """Initialize the RAG system with Upstash Vector."""
        self.index = None
        self.food_data = []
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize Upstash Vector and load data."""
        try:
            print("🚀 Initializing Upstash Vector RAG System...")
            
            # Initialize Upstash Vector client
            if not UPSTASH_URL or not UPSTASH_TOKEN:
                raise ValueError("Missing Upstash credentials in environment variables")
            
            self.index = Index(url=UPSTASH_URL, token=UPSTASH_TOKEN)
            
            # Test connection
            info = self.index.info()
            print(f"✅ Connected to Upstash Vector!")
            print(f"   📊 Vectors: {info.vector_count}")
            print(f"   🤖 Model: {info.dense_index.embedding_model}")
            print(f"   📏 Dimensions: {info.dimension}")
            
            # Load food data
            self.load_food_data()
            
            # Ensure data is in Upstash (idempotent operation)
            if info.vector_count == 0:
                print("📤 No vectors found, uploading food data...")
                self.upsert_food_data()
            else:
                print(f"✅ Found {info.vector_count} vectors already in index")
            
        except Exception as e:
            print(f"❌ Failed to initialize system: {e}")
            sys.exit(1)
    
    def load_food_data(self):
        """Load food data from JSON file."""
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                self.food_data = json.load(f)
            print(f"📋 Loaded {len(self.food_data)} food items")
        except Exception as e:
            print(f"❌ Failed to load food data: {e}")
            sys.exit(1)
    
    def upsert_food_data(self):
        """Upsert food data to Upstash Vector with enhanced text and metadata."""
        if not self.food_data:
            print("⚠️ No food data to upsert")
            return
        
        try:
            vectors = []
            for item in self.food_data:
                # Create enriched text for better embeddings
                enriched_text = item["text"]
                if "region" in item:
                    enriched_text += f" This food is popular in {item['region']}."
                if "type" in item:
                    enriched_text += f" It is a type of {item['type']}."
                
                vectors.append((
                    item["id"],
                    enriched_text,
                    {
                        "region": item.get("region", "unknown"),
                        "type": item.get("type", "general"),
                        "original_text": item["text"]
                    }
                ))
            
            print(f"📤 Upserting {len(vectors)} food items...")
            
            # Batch upsert
            batch_size = 50
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                print(f"   ✅ Batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1} complete")
            
            print("🎉 All food data successfully uploaded!")
            
        except Exception as e:
            print(f"❌ Failed to upsert data: {e}")
            raise
    
    def search_foods(self, query: str) -> List[Dict]:
        """Search for relevant foods using Upstash Vector."""
        try:
            print(f"🔍 Searching for: '{query}'")
            
            # Perform vector search
            results = self.index.query(
                data=query,
                top_k=MAX_RESULTS,
                include_metadata=True
            )
            
            # Process results
            processed_results = []
            for result in results:
                metadata = result.metadata if hasattr(result, 'metadata') else {}
                score = result.score if hasattr(result, 'score') else 0
                
                processed_results.append({
                    'text': metadata.get('original_text', ''),
                    'region': metadata.get('region', 'unknown'),
                    'type': metadata.get('type', 'general'),
                    'score': score
                })
            
            return processed_results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def generate_response(self, query: str, contexts: List[Dict]) -> str:
        """Generate response using contexts (simplified version)."""
        if not contexts:
            return "I couldn't find any relevant information about that. Could you try asking about a specific type of food or cuisine?"
        
        # Create a simple response based on retrieved contexts
        response = f"Based on your question about '{query}', here's what I found:\\n\\n"
        
        for i, ctx in enumerate(contexts, 1):
            region = ctx['region']
            food_type = ctx['type']
            text = ctx['text']
            score = ctx['score']
            
            response += f"{i}. **{region}** ({food_type}): {text}\\n"
            response += f"   Relevance: {score:.1%}\\n\\n"
        
        return response.strip()
    
    def query(self, question: str) -> str:
        """Perform complete RAG query."""
        try:
            # Search for relevant contexts
            contexts = self.search_foods(question)
            
            if contexts:
                print("\\n🧠 Retrieved relevant information:")
                for i, ctx in enumerate(contexts, 1):
                    print(f"   {i}. [{ctx['region']}/{ctx['type']}] {ctx['text'][:60]}...")
                    print(f"      Similarity: {ctx['score']:.3f}")
                print()
            
            # Generate response
            response = self.generate_response(question, contexts)
            return response
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return "Sorry, I encountered an error while processing your question. Please try again."
    
    def run_interactive(self):
        """Run interactive query loop."""
        print("\\n🧠 RAG System ready! Ask questions about food (type 'exit' to quit):")
        print("=" * 60)
        
        while True:
            try:
                # Handle different input scenarios
                try:
                    question = input("\\nYou: ").strip()
                except EOFError:
                    # Handle piped input or EOF
                    break
                except KeyboardInterrupt:
                    print("\\n\\n👋 Goodbye!")
                    break
                
                if question.lower() in ["exit", "quit", "bye"]:
                    print("👋 Goodbye!")
                    break
                
                if question == "":
                    print("💭 Please ask a question about food!")
                    continue
                
                # Process query
                answer = self.query(question)
                print(f"\\n🤖 Assistant: {answer}")
                
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Please try again or type 'exit' to quit.")

def main():
    """Main function."""
    try:
        # Initialize RAG system
        rag = RAGSystem()
        
        # Check if we have command line arguments for non-interactive mode
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            print(f"\\n🔍 Processing query: '{query}'")
            answer = rag.query(query)
            print(f"\\n🤖 Answer: {answer}")
        else:
            # Run interactive mode
            rag.run_interactive()
            
    except KeyboardInterrupt:
        print("\\n\\n👋 System shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()