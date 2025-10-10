#!/usr/bin/env python3
"""
Test the expanded food database with comprehensive examples
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_expanded_database():
    """Test queries on the new expanded database"""
    
    print("🍕 Food Database Enhancement Complete! 🎉\n")
    
    # Load and verify the database
    try:
        with open('foods.json', 'r', encoding='utf-8') as f:
            food_data = json.load(f)
        
        print(f"📊 Database Statistics:")
        print(f"   Total Items: {len(food_data)}")
        print(f"   Range: Items 1-{len(food_data)}")
        
        # Show the 20 new additions (items 91-110)
        print(f"\n🆕 New Additions (Items 91-110):\n")
        
        new_items = food_data[-20:]  # Last 20 items
        
        # Categorize the new items
        world_cuisines = []
        health_conscious = []
        comfort_foods = []
        
        for item in new_items:
            item_id = int(item['id'])
            if item_id in [91, 92, 93, 94, 95, 96, 97, 98]:  # World cuisines
                world_cuisines.append(item)
            elif item_id in [99, 100, 101, 102, 103, 104]:  # Health-conscious
                health_conscious.append(item)
            elif item_id in [105, 106, 107, 108, 109, 110]:  # Comfort foods
                comfort_foods.append(item)
        
        # Display world cuisines
        print("🌍 WORLD CUISINES (8 items):")
        for item in world_cuisines:
            print(f"   {item['id']}. {item['region']} - {item['text'][:50]}...")
        
        print(f"\n💪 HEALTH-CONSCIOUS OPTIONS (6 items):")
        for item in health_conscious:
            print(f"   {item['id']}. {item['text'][:50]}...")
        
        print(f"\n🏠 COMFORT FOODS (6 items):")
        for item in comfort_foods:
            print(f"   {item['id']}. {item['region']} - {item['text'][:50]}...")
        
        # Show enhanced data structure
        sample_item = new_items[0]  # Tom Kha Gai
        print(f"\n📋 Enhanced Data Structure Example (Tom Kha Gai):")
        print(f"   🆔 ID: {sample_item['id']}")
        print(f"   🌍 Region: {sample_item['region']}")
        print(f"   🍽️ Type: {sample_item['type']}")
        print(f"   📍 Origin: {sample_item.get('origin', 'Not specified')}")
        print(f"   🥄 Ingredients: {len(sample_item.get('ingredients', []))} listed")
        print(f"   🍃 Dietary Tags: {sample_item.get('dietary', [])}")
        print(f"   ⚠️ Allergens: {sample_item.get('allergens', [])}")
        print(f"   📝 Description Length: {len(sample_item['text'])} characters")
        
        # Statistics by category
        regions = {}
        dietary_tags = {}
        
        for item in new_items:
            region = item.get('region', 'Unknown')
            regions[region] = regions.get(region, 0) + 1
            
            for tag in item.get('dietary', []):
                dietary_tags[tag] = dietary_tags.get(tag, 0) + 1
        
        print(f"\n📊 New Items by Region:")
        for region, count in sorted(regions.items()):
            print(f"   {region}: {count} items")
        
        print(f"\n🏷️ Dietary Tags Distribution:")
        for tag, count in sorted(dietary_tags.items()):
            print(f"   {tag}: {count} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return False

def test_sample_queries():
    """Show example queries that would work with the new data"""
    
    print(f"\n🔍 Sample Queries You Can Try:")
    
    sample_queries = [
        ("Thai cuisine", "Tom Kha Gai - Thai coconut soup"),
        ("Mediterranean food", "Greek Moussaka, Lebanese Tabbouleh, Spanish Gazpacho"),
        ("healthy breakfast", "Açaí Bowl, Chia Pudding, Overnight Oats"),
        ("comfort food", "Mac and Cheese, Chicken and Dumplings, Fish and Chips"),
        ("vegan options", "Buddha Bowl, Green Goddess Smoothie Bowl"),
        ("Japanese dishes", "Ramen, Katsu Curry"),
        ("superfoods", "Spirulina Energy Balls, Quinoa Power Bowl"),
        ("gluten-free meals", "Several options now available with detailed tags")
    ]
    
    for query, expected in sample_queries:
        print(f"   ❓ \"{query}\" → {expected}")

if __name__ == "__main__":
    print("=" * 60)
    success = test_expanded_database()
    
    if success:
        test_sample_queries()
        print(f"\n🚀 Ready to Test!")
        print(f"   Run: python rag_run.py")
        print(f"   Try queries like: 'Tell me about Thai soup' or 'What are some healthy breakfast options?'")
        print("=" * 60)
    else:
        print(f"\n❌ Database expansion verification failed")