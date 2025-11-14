#!/usr/bin/env python3
"""
Upstash Vector Foods Namespace Migration Script
==============================================

This script creates a separate 'foods' namespace in Upstash Vector database
and migrates all food data from foods.json to maintain data separation
from existing digital twin application data.

Author: Jasha9
Date: November 2025
"""

import json
import os
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class UpstashFoodsMigration:
    def __init__(self):
        self.base_url = os.getenv('UPSTASH_VECTOR_REST_URL')
        self.token = os.getenv('UPSTASH_VECTOR_REST_TOKEN')
        self.foods_namespace = "foods"
        
        if not self.base_url or not self.token:
            raise ValueError("Missing Upstash credentials in .env file")
            
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip('/')
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def check_namespace_exists(self) -> bool:
        """Check if the foods namespace already has data"""
        try:
            print(f"🔍 Checking if namespace '{self.foods_namespace}' exists...")
            
            # Try to get namespace info - this will tell us if it exists
            info_url = f"{self.base_url}/info/{self.foods_namespace}"
            response = requests.get(info_url, headers=self.headers)
            
            if response.status_code == 200:
                info = response.json()
                vector_count = info.get('vectorCount', 0)
                print(f"✅ Namespace '{self.foods_namespace}' exists with {vector_count} vectors")
                return True
            elif response.status_code == 404:
                print(f"📝 Namespace '{self.foods_namespace}' doesn't exist yet - will be created automatically")
                return True  # This is fine, namespace will be created on first upsert
            else:
                print(f"❌ Error checking namespace. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking namespace: {e}")
            return False
    
    def load_food_data(self) -> List[Dict[str, Any]]:
        """Load food data from JSON file"""
        try:
            with open('foods.json', 'r', encoding='utf-8') as f:
                foods = json.load(f)
            print(f"📊 Loaded {len(foods)} food items from JSON file")
            return foods
        except Exception as e:
            print(f"❌ Error loading food data: {e}")
            return []
    
    def prepare_food_text(self, food_item: Dict[str, Any]) -> str:
        """Prepare comprehensive text representation of food item for embedding"""
        text_parts = [food_item.get('text', '')]
        
        # Add additional metadata to enhance search
        if food_item.get('region'):
            text_parts.append(f"Region: {food_item['region']}")
        
        if food_item.get('type'):
            text_parts.append(f"Type: {food_item['type']}")
            
        if food_item.get('origin'):
            text_parts.append(f"Origin: {food_item['origin']}")
            
        if food_item.get('ingredients'):
            ingredients = ', '.join(food_item['ingredients'])
            text_parts.append(f"Ingredients: {ingredients}")
            
        if food_item.get('preparation'):
            text_parts.append(f"Preparation: {food_item['preparation']}")
            
        if food_item.get('cultural_significance'):
            text_parts.append(f"Cultural significance: {food_item['cultural_significance']}")
            
        if food_item.get('dietary'):
            dietary = ', '.join(food_item['dietary'])
            text_parts.append(f"Dietary: {dietary}")
        
        return ' '.join(text_parts)
    
    def upsert_food_items(self, foods: List[Dict[str, Any]]) -> bool:
        """Upsert food items to the foods namespace using Upstash Vector client"""
        try:
            print(f"🚀 Starting migration of {len(foods)} food items...")
            
            # Import Upstash Vector client
            from upstash_vector import Index
            
            # Initialize Upstash Vector client
            foods_index = Index(
                url=self.base_url,
                token=self.token
            )
            
            # Prepare vectors in the format expected by Upstash Vector client
            vectors = []
            for food in foods:
                # Use same text enrichment as current RAG system
                enriched_text = food.get("text", "")
                if food.get("region"):
                    enriched_text += f" This food is popular in {food['region']}."
                if food.get("type"):
                    enriched_text += f" It is a type of {food['type']}."
                
                # Add more context from extended metadata
                if food.get("origin"):
                    enriched_text += f" Origin: {food['origin']}."
                if food.get("cultural_significance"):
                    enriched_text += f" Cultural significance: {food['cultural_significance']}"
                
                # Create vector tuple: (id, text_data, metadata)
                vector_tuple = (
                    f"food_{food['id']}",
                    enriched_text,  # Upstash will auto-generate embeddings
                    {
                        'id': food['id'],
                        'region': food.get('region', ''),
                        'type': food.get('type', ''),
                        'origin': food.get('origin', ''),
                        'ingredients': food.get('ingredients', []),
                        'preparation': food.get('preparation', ''),
                        'nutrition': food.get('nutrition', ''),
                        'cultural_significance': food.get('cultural_significance', ''),
                        'dietary': food.get('dietary', []),
                        'allergens': food.get('allergens', []),
                        'original_text': food.get('text', '')
                    }
                )
                vectors.append(vector_tuple)
            
            # Process in batches of 50 to avoid payload limits
            batch_size = 50
            total_batches = (len(vectors) + batch_size - 1) // batch_size
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
                
                try:
                    # Use Upstash Vector client upsert method with namespace
                    foods_index.upsert(vectors=batch, namespace=self.foods_namespace)
                    print(f"✅ Successfully upserted batch {batch_num}")
                except Exception as e:
                    print(f"❌ Failed to upsert batch {batch_num}: {e}")
                    return False
                
                # Small delay between batches
                time.sleep(0.5)
            
            print(f"🎉 Successfully migrated all {len(foods)} food items to '{self.foods_namespace}' namespace!")
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify the migration by checking namespace stats"""
        try:
            print("🔍 Verifying migration...")
            
            # Get namespace info
            info_url = f"{self.base_url}/info/{self.foods_namespace}"
            response = requests.get(info_url, headers=self.headers)
            
            if response.status_code == 200:
                info = response.json()
                vector_count = info.get('vectorCount', 0)
                print(f"✅ Verification successful!")
                print(f"📊 Namespace '{self.foods_namespace}' contains {vector_count} vectors")
                print(f"📏 Dimension: {info.get('dimension', 'Unknown')}")
                print(f"🔧 Similarity function: {info.get('similarityFunction', 'Unknown')}")
                return True
            else:
                print(f"❌ Failed to get namespace info. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        print("🍽️ Starting Upstash Vector Foods Migration")
        print("=" * 50)
        
        # Step 1: Check namespace
        if not self.check_namespace_exists():
            return False
        
        # Step 2: Load food data
        foods = self.load_food_data()
        if not foods:
            return False
        
        # Step 3: Migrate data
        if not self.upsert_food_items(foods):
            return False
        
        # Step 4: Verify migration
        if not self.verify_migration():
            return False
        
        print("\n🎉 Migration completed successfully!")
        print(f"✅ All food data is now available in the '{self.foods_namespace}' namespace")
        print("✅ Your existing digital twin data remains untouched in the default namespace")
        
        return True

def main():
    """Main function to run the migration"""
    try:
        migration = UpstashFoodsMigration()
        success = migration.run_migration()
        
        if success:
            print("\n📝 Next Steps:")
            print("1. Update your RAG system to use the 'foods' namespace")
            print("2. Test queries to ensure proper data separation")
            print("3. Your digital twin data remains in the default namespace")
        else:
            print("\n❌ Migration failed. Please check the errors above.")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()