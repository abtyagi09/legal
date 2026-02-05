"""Test security filtering"""
import asyncio
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient

async def test_security_filter():
    search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://srch-7alsezpsk27uq.search.windows.net")
    search_key = os.getenv("SEARCH_API_KEY")
    
    if not search_key:
        print("ERROR: SEARCH_API_KEY environment variable not set")
        return
    
    index_name = "legal-documents-index"
    correct_user = "c0a74faa-ea65-4666-9ac3-9709998fbda7"
    wrong_user = "wrong-user-id-123"
    
    credential = AzureKeyCredential(search_key)
    client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)
    
    try:
        # Test 1: Search with correct user
        print(f"\n=== Test 1: Searching with CORRECT user ID ===")
        print(f"User: {correct_user}")
        filter1 = f"allowed_users/any(u: u eq '{correct_user}')"
        print(f"Filter: {filter1}")
        
        results = await client.search("*", filter=filter1, select=["id", "title", "owner_id", "allowed_users"])
        count = 0
        async for result in results:
            count += 1
            print(f"  Found: {result.get('title')} (Owner: {result.get('owner_id')})")
        print(f"Results: {count} document(s)")
        
        # Test 2: Search with wrong user
        print(f"\n=== Test 2: Searching with WRONG user ID ===")
        print(f"User: {wrong_user}")
        filter2 = f"allowed_users/any(u: u eq '{wrong_user}')"
        print(f"Filter: {filter2}")
        
        results = await client.search("*", filter=filter2, select=["id", "title", "owner_id", "allowed_users"])
        count = 0
        async for result in results:
            count += 1
            print(f"  Found: {result.get('title')} (Owner: {result.get('owner_id')})")
        print(f"Results: {count} document(s)")
        
        # Test 3: Search with NO filter
        print(f"\n=== Test 3: Searching with NO filter ===")
        results = await client.search("*", select=["id", "title", "owner_id", "allowed_users"])
        count = 0
        async for result in results:
            count += 1
            print(f"  Found: {result.get('title')} (Owner: {result.get('owner_id')}, Allowed: {result.get('allowed_users')})")
        print(f"Results: {count} document(s)")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_security_filter())
