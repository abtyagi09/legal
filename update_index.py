"""Script to update Azure AI Search index with vector field"""
import asyncio
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

async def update_index():
    # Get configuration from environment or use defaults
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
        print(f"Fetching existing index: {index_name}")
        index = await client.get_index(index_name)
        
        # Add vector field if it doesn't exist
        vector_field_exists = any(field.name == "content_vector" for field in index.fields)
        
        if not vector_field_exists:
            print("Adding vector field 'content_vector'...")
            
            # Add the vector field
            index.fields.append(
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="vector-profile"
                )
            )
        else:
            print("✓ Vector field 'content_vector' already exists")
            
        # Configure vector search if not present
        if not index.vector_search:
            print("Adding vector search configuration...")
            index.vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="vector-algorithm",
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="vector-profile",
                        algorithm_configuration_name="vector-algorithm"
                    )
                ]
            )
        else:
            print("✓ Vector search already configured")
        
        # Configure semantic search if not present
        if not index.semantic_search:
            print("Adding semantic search configuration...")
            index.semantic_search = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[SemanticField(field_name="content")],
                            keywords_fields=[SemanticField(field_name="file_name")]
                        )
                    )
                ]
            )
        else:
            print("✓ Semantic search already configured")
        
        # Update the index
        print("Updating index...")
        await client.create_or_update_index(index)
        print("✓ Index updated successfully")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(update_index())
