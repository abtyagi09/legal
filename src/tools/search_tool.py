"""
Azure AI Search Tool for Legal Document Agent
Provides semantic search capabilities across legal document corpus
"""
from typing import Annotated, List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery, QueryType
from azure.core.credentials import AzureKeyCredential
import logging

logger = logging.getLogger(__name__)


class SearchTool:
    """
    Tool for searching legal documents using Azure AI Search
    
    Capabilities:
    - Semantic search across indexed legal documents
    - Retrieve relevant documents based on natural language queries
    - Filter by document type, date, or other metadata
    """
    
    def __init__(
        self, 
        service_endpoint: str, 
        api_key: str, 
        index_name: str,
        top_results: int = 5
    ):
        """
        Initialize Azure AI Search client
        
        Args:
            service_endpoint: Azure AI Search service endpoint
            api_key: Azure AI Search API key
            index_name: Name of the search index
            top_results: Number of top results to return (default: 5)
        """
        self.client = SearchClient(
            endpoint=service_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )
        self.index_name = index_name
        self.top_results = top_results
        logger.info(f"Initialized Azure AI Search tool with index: {index_name}")
    
    async def search_documents(
        self,
        query: Annotated[str, "Natural language search query for finding legal documents"],
        document_type: Annotated[
            Optional[str], 
            "Optional filter by document type (e.g., 'contract', 'brief', 'NDA', 'agreement')"
        ] = None,
        date_from: Annotated[
            Optional[str], 
            "Optional start date filter in ISO format (YYYY-MM-DD)"
        ] = None,
        date_to: Annotated[
            Optional[str], 
            "Optional end date filter in ISO format (YYYY-MM-DD)"
        ] = None,
    ) -> str:
        """
        Search for legal documents using semantic search.
        
        This tool searches through the indexed legal document corpus to find
        the most relevant documents based on your query. It uses semantic search
        to understand the meaning and context of your query, not just keywords.
        
        Use cases:
        - "Find all real estate contracts from 2024"
        - "Search for NDAs with confidentiality clauses"
        - "Locate merger agreements mentioning specific parties"
        - "Find case briefs related to intellectual property"
        
        Args:
            query: Natural language search query describing what you're looking for
            document_type: Filter results by document type (contract, NDA, brief, etc.)
            date_from: Only return documents dated on or after this date (YYYY-MM-DD)
            date_to: Only return documents dated on or before this date (YYYY-MM-DD)
            
        Returns:
            Formatted string with search results including document titles, excerpts, and metadata
        """
        try:
            logger.info(f"Searching documents with query: '{query}'")
            
            # Build filter expression
            filter_expressions = []
            if document_type:
                filter_expressions.append(f"document_type eq '{document_type}'")
            if date_from:
                filter_expressions.append(f"document_date ge {date_from}")
            if date_to:
                filter_expressions.append(f"document_date le {date_to}")
            
            filter_str = " and ".join(filter_expressions) if filter_expressions else None
            
            # Execute semantic search
            results = self.client.search(
                search_text=query,
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="default",
                top=self.top_results,
                filter=filter_str,
                include_total_count=True,
            )
            
            # Format results
            output = self._format_search_results(results, query)
            
            logger.info(f"Search completed successfully")
            return output
            
        except Exception as e:
            error_msg = f"Error searching documents: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def get_document_by_id(
        self,
        document_id: Annotated[str, "The unique identifier of the document to retrieve"],
    ) -> str:
        """
        Retrieve a specific legal document by its unique ID.
        
        Use this tool when you need to access the full content of a specific
        document that you've identified through search or that the user
        has referenced by ID.
        
        Args:
            document_id: The unique document identifier
            
        Returns:
            Formatted string with the complete document information
        """
        try:
            logger.info(f"Retrieving document: {document_id}")
            
            result = self.client.get_document(key=document_id)
            
            # Format document
            output = self._format_document(result)
            
            logger.info(f"Document retrieved successfully")
            return output
            
        except Exception as e:
            error_msg = f"Error retrieving document {document_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _format_search_results(self, results: Any, query: str) -> str:
        """
        Format search results into a readable string
        
        Args:
            results: Search results from Azure AI Search
            query: Original search query
            
        Returns:
            Formatted search results
        """
        output_parts = []
        output_parts.append("=== LEGAL DOCUMENT SEARCH RESULTS ===\n")
        output_parts.append(f"Query: {query}\n")
        
        result_count = 0
        for result in results:
            result_count += 1
            
            # Extract key fields (adjust based on your index schema)
            doc_id = result.get("id", "N/A")
            title = result.get("title", "Untitled Document")
            doc_type = result.get("document_type", "Unknown")
            date = result.get("document_date", "N/A")
            content_preview = result.get("content", "")
            
            # Get semantic search score if available
            score = result.get("@search.score", "N/A")
            
            # Truncate content preview
            if content_preview and len(content_preview) > 500:
                content_preview = content_preview[:500] + "..."
            
            output_parts.append(f"\n--- Result {result_count} ---")
            output_parts.append(f"Document ID: {doc_id}")
            output_parts.append(f"Title: {title}")
            output_parts.append(f"Type: {doc_type}")
            output_parts.append(f"Date: {date}")
            output_parts.append(f"Relevance Score: {score}")
            output_parts.append(f"\nContent Preview:")
            output_parts.append(content_preview)
            output_parts.append("")
        
        if result_count == 0:
            output_parts.append("No documents found matching your query.")
            output_parts.append("\nTry:")
            output_parts.append("- Using different keywords")
            output_parts.append("- Broadening your search criteria")
            output_parts.append("- Removing date or type filters")
        else:
            output_parts.append(f"\n--- Total Results: {result_count} ---")
            output_parts.append(f"Use 'get_document_by_id' tool with a Document ID to retrieve full content.")
        
        return "\n".join(output_parts)
    
    def _format_document(self, document: Dict[str, Any]) -> str:
        """
        Format a single document into a readable string
        
        Args:
            document: Document data from Azure AI Search
            
        Returns:
            Formatted document
        """
        output_parts = []
        output_parts.append("=== LEGAL DOCUMENT DETAILS ===\n")
        
        # Extract fields (adjust based on your index schema)
        doc_id = document.get("id", "N/A")
        title = document.get("title", "Untitled Document")
        doc_type = document.get("document_type", "Unknown")
        date = document.get("document_date", "N/A")
        author = document.get("author", "N/A")
        parties = document.get("parties", "N/A")
        content = document.get("content", "No content available")
        
        output_parts.append(f"Document ID: {doc_id}")
        output_parts.append(f"Title: {title}")
        output_parts.append(f"Type: {doc_type}")
        output_parts.append(f"Date: {date}")
        output_parts.append(f"Author: {author}")
        output_parts.append(f"Parties: {parties}")
        output_parts.append(f"\n--- FULL CONTENT ---")
        output_parts.append(content)
        
        return "\n".join(output_parts)


def create_search_tool(
    service_endpoint: str, 
    api_key: str, 
    index_name: str,
    top_results: int = 5
) -> List[callable]:
    """
    Factory function to create search tool functions
    
    Args:
        service_endpoint: Azure AI Search service endpoint
        api_key: Azure AI Search API key
        index_name: Name of the search index
        top_results: Number of top results to return
        
    Returns:
        List of callable tool functions for use with agent
    """
    tool = SearchTool(service_endpoint, api_key, index_name, top_results)
    return [
        tool.search_documents,
        tool.get_document_by_id,
    ]
