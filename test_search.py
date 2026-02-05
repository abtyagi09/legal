"""Test hybrid search with embeddings"""
import asyncio
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential

async def test_search():
    search_endpoint = "https://srch-7alsezpsk27uq.search.windows.net"
    search_key = os.getenv("SEARCH_API_KEY")
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://aifoundryprojectdemoresource.openai.azure.com/")
    
    # Generate embedding for query
    print("Generating embedding for query: 'freelance services invoice'")
    credential = DefaultAzureCredential()
    token_response = await credential.get_token("https://cognitiveservices.azure.com/.default")
    
    client = AsyncAzureOpenAI(
        azure_endpoint=openai_endpoint,
        azure_ad_token=token_response.token,
        api_version="2024-02-01"
    )
    
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input="freelance services invoice"
    )
    query_vector = response.data[0].embedding
    print(f"✓ Generated embedding with {len(query_vector)} dimensions")
    
    # Search with vector
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name="legal-documents-index",
        credential=AzureKeyCredential(search_key)
    )
    
    try:
        print("\n--- Hybrid Search (Keyword + Vector) ---")
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=5,
            fields="content_vector"
        )
        
        results = await search_client.search(
            search_text="freelance services invoice",
            vector_queries=[vector_query],
            select=["title", "upload_date"],
            top=5
        )
        
        print("Results:")
        count = 0
        async for result in results:
            count += 1
            score = result.get('@search.score', 0)
            print(f"{count}. {result['title']} (score: {score:.4f})")
        
        if count == 0:
            print("No results found")
            
    finally:
        await search_client.close()

if __name__ == "__main__":
    asyncio.run(test_search())
