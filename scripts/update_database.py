#!/usr/bin/env python3
"""
Update Upstash Vector database with new food items
"""

import os
import json
from dotenv import load_dotenv
from upstash_vector import Index

# Load environment variables
load_dotenv('.env')

def update_database():
    """Update Upstash Vector with new food items"""
    
    print("🔄 Updating Upstash Vector with expanded food database...")
    
    # Initialize Upstash client
    upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
    upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    if not upstash_url or not upstash_token:
        print("❌ Missing Upstash credentials")
        return False
    
    try:
        index = Index(url=upstash_url, token=upstash_token)
        
        # Get current state
        info = index.info()
        current_count = info.vector_count
        print(f"📊 Current vectors in database: {current_count}")
        
        # Load food data
        with open('foods.json', 'r', encoding='utf-8') as f:
            food_data = json.load(f)
        
        print(f"📋 Local database has {len(food_data)} items")
        
        if len(food_data) > current_count:
            print(f"🆕 Found {len(food_data) - current_count} new items to upload...")
            
            # Prepare new vectors (items 91-110)
            new_vectors = []
            for item in food_data[current_count:]:  # Only new items
                # Create enriched text for better embeddings
                enriched_text = item["text"]
                if "region" in item:
                    enriched_text += f" This food is popular in {item['region']}."
                if "type" in item:
                    enriched_text += f" It is a type of {item['type']}."
                
                new_vectors.append((
                    item["id"],
                    enriched_text,
                    {
                        "region": item.get("region", "unknown"),
                        "type": item.get("type", "general"),
                        "original_text": item["text"],
                        "cultural_significance": item.get("cultural_significance", ""),
                        "dietary": item.get("dietary", []),
                        "allergens": item.get("allergens", [])
                    }
                ))
            
            # Upload new vectors
            batch_size = 10
            for i in range(0, len(new_vectors), batch_size):
                batch = new_vectors[i:i + batch_size]
                index.upsert(vectors=batch)
                print(f"   ✅ Uploaded batch {i//batch_size + 1}/{(len(new_vectors)-1)//batch_size + 1}")
            
            # Verify update
            updated_info = index.info()
            print(f"🎉 Database updated! New vector count: {updated_info.vector_count}")
            return True
        else:
            print("✅ Database already up to date!")
            return True
            
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False

if __name__ == "__main__":
    success = update_database()
    if success:
        print("\n🚀 Ready to test expanded database!")
        print("Run: python rag_run.py")
    else:
        print("\n❌ Database update failed")