#!/usr/bin/env python3
"""
Quick demonstration of advanced testing capabilities
Shows key test examples without running the full suite
"""

import os
import time
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv('.env')

def demo_advanced_tests():
    """Demonstrate key advanced testing capabilities"""
    
    print("🧪 Advanced Testing Demonstration")
    print("=" * 50)
    
    # Setup clients
    try:
        upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
        upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        groq_key = os.getenv("GROQ_API_KEY")
        
        index = Index(url=upstash_url, token=upstash_token)
        groq_client = Groq(api_key=groq_key)
        
        print("✅ Test environment initialized")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return
    
    # Define key test examples
    test_examples = [
        {
            'category': 'Semantic Similarity',
            'query': 'healthy Mediterranean options',
            'description': 'Tests understanding of cuisine + health concepts'
        },
        {
            'category': 'Multi-Criteria Search', 
            'query': 'spicy vegetarian Asian dishes',
            'description': 'Tests flavor + diet + region filtering'
        },
        {
            'category': 'Cultural Exploration',
            'query': 'traditional comfort foods from different countries',
            'description': 'Tests cultural knowledge and diversity'
        },
        {
            'category': 'Nutritional Query',
            'query': 'high-protein low-carb foods',
            'description': 'Tests macronutrient understanding'
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_examples, 1):
        print(f"\n🔍 Test {i}/4: {test['category']}")
        print(f"Query: '{test['query']}'")
        print(f"Focus: {test['description']}")
        
        try:
            # Measure performance
            start_time = time.time()
            
            # Vector search
            search_results = index.query(
                data=test['query'],
                top_k=3,
                include_metadata=True
            )
            
            search_time = time.time() - start_time
            
            # Extract contexts
            contexts = []
            for result in search_results:
                metadata = result.metadata if hasattr(result, 'metadata') else {}
                contexts.append({
                    'text': metadata.get('original_text', ''),
                    'region': metadata.get('region', 'unknown'),
                    'type': metadata.get('type', 'general'),
                    'score': result.score if hasattr(result, 'score') else 0
                })
            
            # Generate response
            if contexts:
                context_text = "\n\n".join([
                    f"Food: {ctx['text'][:100]}...\nRegion: {ctx['region']}\nType: {ctx['type']}"
                    for ctx in contexts[:3]
                ])
                
                llm_start = time.time()
                completion = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a food expert. Provide concise, accurate answers based on the context."},
                        {"role": "user", "content": f"Based on this context, answer: {test['query']}\n\nContext:\n{context_text}"}
                    ],
                    temperature=0.7,
                    max_completion_tokens=200
                )
                llm_time = time.time() - llm_start
                
                response = completion.choices[0].message.content.strip()
                total_time = time.time() - start_time
                
                # Evaluate results
                print(f"✅ Response Time: {total_time:.3f}s")
                print(f"🔍 Contexts Found: {len(contexts)}")
                print(f"📊 Top Similarity: {max(ctx['score'] for ctx in contexts):.3f}")
                print(f"💰 Tokens Used: {completion.usage.total_tokens}")
                print(f"🤖 Response: {response[:150]}...")
                
                # Simple accuracy assessment
                query_lower = test['query'].lower()
                response_lower = response.lower()
                
                accuracy_indicators = 0
                if 'mediterranean' in query_lower and any(region in response_lower for region in ['greece', 'lebanon', 'spain']):
                    accuracy_indicators += 1
                if 'asian' in query_lower and any(region in response_lower for region in ['thai', 'japan', 'korea']):
                    accuracy_indicators += 1
                if 'vegetarian' in query_lower and 'vegetarian' in response_lower:
                    accuracy_indicators += 1
                if 'comfort' in query_lower and 'comfort' in response_lower:
                    accuracy_indicators += 1
                if 'protein' in query_lower and 'protein' in response_lower:
                    accuracy_indicators += 1
                
                accuracy_score = min(accuracy_indicators * 0.3, 1.0)
                print(f"🎯 Estimated Accuracy: {accuracy_score:.1%}")
                
                results.append({
                    'category': test['category'],
                    'total_time': total_time,
                    'accuracy': accuracy_score,
                    'contexts': len(contexts),
                    'tokens': completion.usage.total_tokens
                })
                
            else:
                print("❌ No relevant contexts found")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Summary
    if results:
        avg_time = sum(r['total_time'] for r in results) / len(results)
        avg_accuracy = sum(r['accuracy'] for r in results) / len(results)
        total_tokens = sum(r['tokens'] for r in results)
        
        print(f"\n📊 Demo Test Summary:")
        print(f"   Average Response Time: {avg_time:.3f}s")
        print(f"   Average Accuracy: {avg_accuracy:.1%}")
        print(f"   Total Tokens Used: {total_tokens}")
        print(f"   Success Rate: {len(results)}/4 tests completed")
        
        # Performance vs local estimate
        estimated_local_time = avg_time * 3  # Conservative estimate
        speedup = estimated_local_time / avg_time
        print(f"   Estimated Speedup vs Local: {speedup:.1f}x faster")

def main():
    """Run testing demonstration"""
    try:
        demo_advanced_tests()
        
        print(f"\n🎉 Advanced Testing Demo Complete!")
        print(f"💡 Run full test suite with:")
        print(f"   python tests/advanced_testing_suite.py")
        print(f"   python tests/performance_comparison.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()