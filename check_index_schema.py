"""Script to check the current index schema"""
import asyncio
import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.aio import SearchIndexClient

async def check_index_schema():
    search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://srch-7alsezpsk27uq.search.windows.net")
    search_key = os.getenv("SEARCH_API_KEY")
    
    if not search_key:
        print("ERROR: SEARCH_API_KEY environment variable not set")
        return
    
    index_name = "legal-documents-index"
    
    # Create index client
    credential = AzureKeyCredential(search_key)
    client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
    
    try:
        # Get existing index
        print(f"Fetching index: {index_name}")
        index = await client.get_index(index_name)
        
        print("\n=== FIELDS ===")
        for field in index.fields:
            print(f"\nField: {field.name}")
            print(f"  Type: {field.type}")
            print(f"  Key: {field.key}")
            print(f"  Searchable: {field.searchable}")
            print(f"  Filterable: {field.filterable}")
            print(f"  Sortable: {field.sortable}")
            if hasattr(field, 'vector_search_dimensions'):
                print(f"  Vector Dims: {field.vector_search_dimensions}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_index_schema())
