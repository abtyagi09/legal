"""Script to check document security fields"""
import asyncio
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient

async def check_documents():
    search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://srch-7alsezpsk27uq.search.windows.net")
    search_key = os.getenv("SEARCH_API_KEY")
    
    if not search_key:
        print("ERROR: SEARCH_API_KEY environment variable not set")
        return
    
    index_name = "legal-documents-index"
    
    # Create search client
    credential = AzureKeyCredential(search_key)
    client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)
    
    try:
        # Get all documents
        print("Fetching all documents...")
        results = await client.search("*", select=["id", "title", "file_name", "owner_id", "allowed_users"])
        
        doc_count = 0
        async for result in results:
            doc_count += 1
            print(f"\n--- Document {doc_count} ---")
            print(f"ID: {result.get('id')}")
            print(f"Title: {result.get('title')}")
            print(f"File: {result.get('file_name')}")
            print(f"Owner ID: {result.get('owner_id')}")
            print(f"Allowed Users: {result.get('allowed_users')}")
        
        if doc_count == 0:
            print("No documents found in index")
        else:
            print(f"\n✓ Total documents: {doc_count}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_documents())
