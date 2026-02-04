"""
Azure Document Intelligence Tool for Legal Document Agent
Provides document analysis and text extraction capabilities
"""
from typing import Annotated, Optional, Dict, Any
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential
import logging

logger = logging.getLogger(__name__)


class DocumentIntelligenceTool:
    """
    Tool for analyzing legal documents using Azure Document Intelligence
    
    Capabilities:
    - Extract text, tables, and key-value pairs from documents
    - Analyze document layout and structure
    - Extract specific legal document elements
    """
    
    def __init__(self, endpoint: str, api_key: str, model: str = "prebuilt-document"):
        """
        Initialize Document Intelligence client
        
        Args:
            endpoint: Azure Document Intelligence endpoint
            api_key: Azure Document Intelligence API key
            model: Model to use for analysis (default: prebuilt-document)
        """
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        self.model = model
        logger.info(f"Initialized Document Intelligence tool with model: {model}")
    
    async def analyze_document(
        self,
        document_url: Annotated[str, "URL or path to the document to analyze"],
        extract_tables: Annotated[bool, "Whether to extract tables from the document"] = True,
        extract_key_values: Annotated[bool, "Whether to extract key-value pairs"] = True,
    ) -> str:
        """
        Analyze a legal document and extract structured information.
        
        This tool processes legal documents (PDFs, images, etc.) and extracts:
        - Full text content with layout preservation
        - Tables and their data
        - Key-value pairs (e.g., "Date: 2024-01-01")
        - Document structure (paragraphs, sections)
        
        Args:
            document_url: URL or file path to the document (supports PDF, JPEG, PNG, BMP, TIFF)
            extract_tables: Whether to extract table data
            extract_key_values: Whether to extract key-value pairs
            
        Returns:
            Formatted string containing extracted document information
        """
        try:
            logger.info(f"Analyzing document: {document_url}")
            
            # Build features list based on parameters
            features = []
            if extract_key_values:
                features.append("keyValuePairs")
            
            # Start document analysis
            poller = self.client.begin_analyze_document(
                model_id=self.model,
                analyze_request=AnalyzeDocumentRequest(url_source=document_url),
                features=features if features else None,
            )
            
            # Wait for analysis to complete
            result: AnalyzeResult = poller.result()
            
            # Format results
            output = self._format_analysis_result(result, extract_tables, extract_key_values)
            
            logger.info(f"Document analysis completed successfully")
            return output
            
        except Exception as e:
            error_msg = f"Error analyzing document: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _format_analysis_result(
        self, 
        result: AnalyzeResult, 
        include_tables: bool, 
        include_key_values: bool
    ) -> str:
        """
        Format the analysis result into a readable string
        
        Args:
            result: Analysis result from Document Intelligence
            include_tables: Whether to include table data
            include_key_values: Whether to include key-value pairs
            
        Returns:
            Formatted analysis result
        """
        output_parts = []
        
        # Add document summary
        output_parts.append("=== DOCUMENT ANALYSIS RESULT ===\n")
        
        # Extract full text content
        if result.content:
            output_parts.append("--- DOCUMENT CONTENT ---")
            output_parts.append(result.content)
            output_parts.append("")
        
        # Extract key-value pairs (useful for forms and structured documents)
        if include_key_values and result.key_value_pairs:
            output_parts.append("--- KEY-VALUE PAIRS ---")
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key_text = kv_pair.key.content if kv_pair.key.content else "N/A"
                    value_text = kv_pair.value.content if kv_pair.value.content else "N/A"
                    output_parts.append(f"{key_text}: {value_text}")
            output_parts.append("")
        
        # Extract tables
        if include_tables and result.tables:
            output_parts.append("--- TABLES ---")
            for table_idx, table in enumerate(result.tables, 1):
                output_parts.append(f"\nTable {table_idx} ({table.row_count} rows, {table.column_count} columns):")
                
                # Create a simple table representation
                table_data = {}
                for cell in table.cells:
                    row_idx = cell.row_index
                    col_idx = cell.column_index
                    if row_idx not in table_data:
                        table_data[row_idx] = {}
                    table_data[row_idx][col_idx] = cell.content or ""
                
                # Format table as text
                for row_idx in sorted(table_data.keys()):
                    row_cells = [table_data[row_idx].get(col_idx, "") 
                                for col_idx in range(table.column_count)]
                    output_parts.append(" | ".join(row_cells))
            output_parts.append("")
        
        # Add metadata
        if result.pages:
            output_parts.append(f"--- METADATA ---")
            output_parts.append(f"Total Pages: {len(result.pages)}")
        
        return "\n".join(output_parts)


def create_document_intelligence_tool(
    endpoint: str, 
    api_key: str, 
    model: str = "prebuilt-document"
) -> callable:
    """
    Factory function to create a document intelligence tool function
    
    Args:
        endpoint: Azure Document Intelligence endpoint
        api_key: Azure Document Intelligence API key
        model: Model to use for analysis
        
    Returns:
        Callable tool function for use with agent
    """
    tool = DocumentIntelligenceTool(endpoint, api_key, model)
    return tool.analyze_document
