"""Script to recreate the search index with correct schema"""
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

async def recreate_index():
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
        # Delete existing index
        print(f"Deleting existing index: {index_name}")
        try:
            await client.delete_index(index_name)
            print("✓ Index deleted")
        except Exception as e:
            print(f"Note: {e}")
        
        # Wait a moment for deletion to complete
        await asyncio.sleep(2)
        
        # Create new index with correct schema
        print(f"Creating new index: {index_name}")
        
        index = SearchIndex(
            name=index_name,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String, sortable=True),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="upload_date", type=SearchFieldDataType.String, sortable=True),
                SimpleField(name="file_name", type=SearchFieldDataType.String),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="vector-profile"
                ),
                SimpleField(name="owner_id", type=SearchFieldDataType.String, filterable=True),
                SearchableField(
                    name="allowed_users",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    filterable=True,
                    searchable=True
                ),
            ],
            vector_search=VectorSearch(
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
            ),
            semantic_search=SemanticSearch(
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
        )
        
        await client.create_index(index)
        print("✓ Index created successfully with correct schema")
        
        # Verify the schema
        print("\nVerifying index schema...")
        created_index = await client.get_index(index_name)
        for field in created_index.fields:
            if field.name in ["owner_id", "allowed_users", "content_vector"]:
                print(f"  {field.name}: {field.type} (filterable: {field.filterable})")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(recreate_index())
