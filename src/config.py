"""
Configuration loader for Legal Document Agent
Handles loading and validation of configuration from environment variables or YAML file
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for the legal document agent"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration from environment variables or YAML file
        
        Args:
            config_path: Path to the configuration YAML file (used if env vars not set)
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from environment variables or YAML file"""
        # Try environment variables first (for cloud deployment)
        if self._load_from_env():
            return
        
        # Fall back to YAML file (for local development)
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.example.yaml to config.yaml and update with your values."
            )
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def _load_from_env(self) -> bool:
        """
        Load configuration from environment variables
        
        Returns:
            True if all required env vars are present, False otherwise
        """
        # Check if we're running in Azure (Container Apps sets these)
        foundry_endpoint = os.getenv("FOUNDRY_ENDPOINT")
        if not foundry_endpoint:
            return False
        
        # Load from environment variables
        self._config = {
            "foundry": {
                "project_endpoint": foundry_endpoint,
                "model_deployment_name": os.getenv("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o-mini")
            },
            "openai": {
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                "embedding_deployment": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
                "embedding_dimensions": int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
            },
            "search": {
                "service_endpoint": os.getenv("SEARCH_ENDPOINT", ""),
                "api_key": os.getenv("SEARCH_API_KEY", ""),
                "index_name": os.getenv("SEARCH_INDEX_NAME", "legal-documents-index")
            },
            "document_intelligence": {
                "endpoint": os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT", ""),
                "api_key": os.getenv("DOCUMENT_INTELLIGENCE_API_KEY", "")
            },
            "keyvault": {
                "endpoint": os.getenv("KEYVAULT_ENDPOINT", "")
            },
            "agent": {
                "name": os.getenv("AGENT_NAME", "LegalDocumentAgent"),
                "instructions": os.getenv("AGENT_INSTRUCTIONS", "You are a helpful legal document assistant."),
                "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.3")),
                "streaming": os.getenv("AGENT_STREAMING", "true").lower() == "true"
            }
        }
        return True
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = [
            ("foundry", "project_endpoint"),
            ("foundry", "model_deployment_name"),
        ]
        
        missing_fields = []
        for section, field in required_fields:
            if section not in self._config:
                missing_fields.append(f"{section}.{field}")
            elif field not in self._config[section]:
                missing_fields.append(f"{section}.{field}")
            elif not self._config[section][field] or \
                 str(self._config[section][field]).startswith("YOUR_"):
                missing_fields.append(f"{section}.{field}")
        
        if missing_fields:
            raise ValueError(
                f"Missing or incomplete required configuration fields:\n" +
                "\n".join(f"  - {field}" for field in missing_fields) +
                "\n\nPlease update config.yaml or set environment variables."
            )
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            *keys: Configuration keys (e.g., "foundry", "project_endpoint")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @property
    def foundry_endpoint(self) -> str:
        """Get Microsoft Foundry project endpoint"""
        return self.get("foundry", "project_endpoint")
    
    @property
    def foundry_model_deployment(self) -> str:
        """Get Microsoft Foundry model deployment name"""
        return self.get("foundry", "model_deployment_name")
    
    @property
    def search_endpoint(self) -> str:
        """Get Azure AI Search service endpoint"""
        return self.get("search", "service_endpoint")
    
    @property
    def search_api_key(self) -> str:
        """Get Azure AI Search API key"""
        return self.get("search", "api_key")
    
    @property
    def search_index_name(self) -> str:
        """Get Azure AI Search index name"""
        return self.get("search", "index_name")
    
    @property
    def doc_intel_endpoint(self) -> str:
        """Get Azure Document Intelligence endpoint"""
        return self.get("document_intelligence", "endpoint")
    
    @property
    def doc_intel_api_key(self) -> str:
        """Get Azure Document Intelligence API key"""
        return self.get("document_intelligence", "api_key")
    
    @property
    def agent_name(self) -> str:
        """Get agent name"""
        return self.get("agent", "name", default="LegalDocumentAgent")
    
    @property
    def agent_instructions(self) -> str:
        """Get agent instructions"""
        return self.get("agent", "instructions", default="You are a helpful legal document assistant.")
    
    @property
    def agent_temperature(self) -> float:
        """Get agent temperature setting"""
        return self.get("agent", "temperature", default=0.3)
    
    @property
    def agent_streaming(self) -> bool:
        """Get agent streaming setting"""
        return self.get("agent", "streaming", default=True)
    
    @property
    def openai_endpoint(self) -> str:
        """Get Azure OpenAI endpoint for embeddings"""
        return self.get("openai", "endpoint", default="")
    
    @property
    def openai_api_key(self) -> str:
        """Get Azure OpenAI API key"""
        return self.get("openai", "api_key", default="")
    
    @property
    def openai_embedding_deployment(self) -> str:
        """Get Azure OpenAI embedding deployment name"""
        return self.get("openai", "embedding_deployment", default="text-embedding-3-small")
    
    @property
    def embedding_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.get("openai", "embedding_dimensions", default=1536)


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config object
    """
    return Config(config_path)
