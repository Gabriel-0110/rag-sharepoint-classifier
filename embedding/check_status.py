#!/usr/bin/env python3
"""
Quick status check for all embedding collections
"""
import requests
import json

def check_collections():
    base_url = "http://localhost:6333"
    
    try:
        # Get all collections
        response = requests.get(f"{base_url}/collections")
        if response.status_code == 200:
            collections_data = response.json()
            collections = collections_data["result"]["collections"]
            
            print("📊 COMPLETE DOCUMENT LIBRARY STATUS")
            print("=" * 50)
            print()
            
            total_embeddings = 0
            our_collections = ["test_batch_library", "sp_batch_library", "data_docs_library", "docs_library"]
            
            for collection_name in our_collections:
                # Get collection details
                detail_response = requests.get(f"{base_url}/collections/{collection_name}")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    count = detail_data["result"]["points_count"]
                    total_embeddings += count
                    print(f"  ✅ {collection_name}: {count} embeddings")
                else:
                    print(f"  ❌ {collection_name}: Collection not found")
            
            print()
            print(f"📈 TOTAL EMBEDDINGS: {total_embeddings}")
            print(f"🗃️  TOTAL COLLECTIONS: {len([c for c in collections if c['name'] in our_collections])}")
            print()
            
            # List all collections for reference
            print("All Available Collections:")
            for col in collections:
                print(f"  - {col['name']}")
                
        else:
            print(f"Error connecting to Qdrant: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_collections()
