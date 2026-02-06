"""
Agent configuration for the Legal Document Assistant
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for the Legal Document Agent"""
    
    # Required fields (no defaults)
    foundry_endpoint: str
    foundry_model_deployment: str
    search_endpoint: str
    search_index_name: str
    search_api_key: str
    doc_intel_endpoint: str
    
    # Optional/configurable fields (with defaults)
    foundry_api_version: str = "2024-08-01-preview"
    temperature: float = 0.1  # Low for consistent, factual responses
    max_tokens: int = 2000
    max_search_results: int = 3
    context_chars_per_document: int = 8000
    doc_intel_api_key: Optional[str] = None
    doc_intel_model: str = "prebuilt-layout"
    openai_endpoint: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_embedding_deployment: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    max_conversation_history: int = 10  # Number of messages to keep
    use_managed_identity: bool = True
    enable_function_calling: bool = True  # Enable integration actions
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables"""
        import os
        
        return cls(
            foundry_endpoint=os.getenv("FOUNDRY_ENDPOINT", ""),
            foundry_model_deployment=os.getenv("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o-mini"),
            search_endpoint=os.getenv("SEARCH_ENDPOINT", ""),
            search_index_name=os.getenv("SEARCH_INDEX_NAME", "legal-documents-index"),
            search_api_key=os.getenv("SEARCH_API_KEY", ""),
            doc_intel_endpoint=os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT", ""),
            doc_intel_api_key=os.getenv("DOCUMENT_INTELLIGENCE_API_KEY"),
            openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
            embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
        )
