"""Script to delete all documents from the search index"""
import asyncio
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient

async def delete_all_documents():
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
        results = await client.search("*", select=["id"])
        
        document_ids = []
        async for result in results:
            document_ids.append({"id": result["id"]})
        
        if not document_ids:
            print("No documents to delete")
            return
        
        print(f"Found {len(document_ids)} documents to delete")
        
        # Delete all documents
        print("Deleting documents...")
        await client.delete_documents(documents=document_ids)
        print(f"✓ Successfully deleted {len(document_ids)} documents")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(delete_all_documents())
