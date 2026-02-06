"""
Legal Document Agent - Main agent class
"""

import logging
from typing import AsyncGenerator, Dict, Optional
from urllib.parse import urlparse

from azure.identity.aio import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from .config import AgentConfig
from .instructions import AGENT_INSTRUCTIONS
from tools.search_tool import SearchTool
from tools.document_intelligence_tool import DocumentIntelligenceTool
from tools.integration_actions import IntegrationActions, INTEGRATION_TOOLS

logger = logging.getLogger(__name__)


class LegalDocumentAgent:
    """
    Legal Document Agent for intelligent document search and analysis
    
    Uses Microsoft Agent Framework patterns with Azure AI Foundry models
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Legal Document Agent
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.credential = None
        self.client = None
        self.search_tool = None
        self.doc_intel_tool = None
        self.integration_actions = None
        self.conversations: Dict[str, list] = {}  # Session storage
        self.enable_functions = config.enable_function_calling if hasattr(config, 'enable_function_calling') else True
        
    async def initialize(self):
        """Initialize async resources"""
        logger.info("Initializing Legal Document Agent...")
        
        # Initialize credential
        if self.config.use_managed_identity:
            self.credential = DefaultAzureCredential()
            logger.info("Using managed identity for authentication")
        
        # Initialize AI Foundry client
        await self._initialize_ai_client()
        
        # Initialize search tool
        self.search_tool = SearchTool(
            service_endpoint=self.config.search_endpoint,
            api_key=self.config.search_api_key,
            index_name=self.config.search_index_name
        )
        
        # Initialize document intelligence tool
        self.doc_intel_tool = DocumentIntelligenceTool(
            endpoint=self.config.doc_intel_endpoint,
            api_key=self.config.doc_intel_api_key
        )
        
        # Initialize integration actions
        self.integration_actions = IntegrationActions()
        await self.integration_actions.initialize()
        
        logger.info("✓ Legal Document Agent initialized successfully")
        
    async def _initialize_ai_client(self):
        """Initialize the AI Foundry client"""
        # Extract base URL from foundry endpoint
        parsed = urlparse(self.config.foundry_endpoint)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        logger.info(f"Initializing AI Foundry client with base URL: {base_url}")
        
        if self.config.use_managed_identity and self.credential:
            # Get token for AI Foundry
            token_response = await self.credential.get_token("https://ai.azure.com/.default")
            
            self.client = AsyncAzureOpenAI(
                azure_endpoint=base_url,
                azure_ad_token=token_response.token,
                api_version=self.config.foundry_api_version
            )
            logger.info("Using managed identity for AI Foundry")
        else:
            # Fallback to API key if configured
            logger.warning("Managed identity not available, using API key authentication")
            
    async def cleanup(self):
        """Cleanup async resources"""
        if self.integration_actions:
            await self.integration_actions.cleanup()
        if self.credential:
            await self.credential.close()
        if self.client:
            await self.client.close()
            
    async def chat(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        security_enabled: bool = True,
        enable_functions: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Chat with the agent (streaming response)
        
        Args:
            message: User message
            session_id: Conversation session ID
            user_id: User ID for security filtering
            security_enabled: Whether to apply security filters
            enable_functions: Whether to enable function calling for integration actions
            
        Yields:
            Response chunks as they're generated
        """
        try:
            # Get or create conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            conversation = self.conversations[session_id]
            
            # Search for relevant documents
            logger.info(f"Searching documents for: {message}")
            
            # Build security filter if needed
            filter_expr = None
            if security_enabled and user_id:
                filter_expr = f"allowed_users/any(u: u eq '{user_id}')"
            elif security_enabled:
                filter_expr = "allowed_users/any(u: u eq 'anonymous')"
            
            # Search using Azure AI Search directly for better control
            from azure.search.documents.models import QueryType
            results = self.search_tool.client.search(
                search_text=message,
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="default",
                top=self.config.max_search_results,
                filter=filter_expr,
                select=["title", "content", "file_name"]
            )
            
            # Collect results (SearchClient.search() is synchronous)
            search_results = []
            for result in results:
                search_results.append({
                    'title': result.get('title', 'Untitled'),
                    'content': result.get('content', '')[:self.config.context_chars_per_document],
                    'file_name': result.get('file_name', '')
                })
            
            logger.info(f"Found {len(search_results)} documents")
            
            # Build context from search results
            context = self._build_context(search_results)
            
            # Build messages for AI
            messages = self._build_messages(message, context, conversation)
            
            # Prepare function calling arguments
            call_params = {
                "model": self.config.foundry_model_deployment,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True
            }
            
            # Add tools if function calling is enabled (both globally and for this request)
            if self.enable_functions and enable_functions:
                call_params["tools"] = INTEGRATION_TOOLS
                call_params["tool_choice"] = "auto"
            
            # Call AI model with streaming
            response = await self.client.chat.completions.create(**call_params)
            
            # Stream response with function calling support
            full_response = ""
            tool_calls = []
            
            async for chunk in response:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # Check for tool calls
                if delta.tool_calls:
                    # Accumulate tool calls
                    for tool_call_chunk in delta.tool_calls:
                        if tool_call_chunk.index >= len(tool_calls):
                            tool_calls.append({
                                "id": tool_call_chunk.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call_chunk.function.name if tool_call_chunk.function.name else "",
                                    "arguments": tool_call_chunk.function.arguments if tool_call_chunk.function.arguments else ""
                                }
                            })
                        else:
                            # Append to existing tool call arguments
                            if tool_call_chunk.function.arguments:
                                tool_calls[tool_call_chunk.index]["function"]["arguments"] += tool_call_chunk.function.arguments
                
                # Regular content streaming
                if delta.content:
                    content = delta.content
                    full_response += content
                    yield content
            
            # Process tool calls if any
            if tool_calls:
                yield "\n\n<div style='padding: 10px; background: #f0f8ff; border-left: 4px solid #0078D4; margin: 10px 0;'>🔧 Executing actions...</div>\n\n"
                
                for tool_call in tool_calls:
                    tool_result = await self._execute_tool_call(tool_call)
                    yield tool_result
            
            # Update conversation history
            conversation.append({"role": "user", "content": message})
            conversation.append({"role": "assistant", "content": full_response})
            
            # Trim conversation history
            if len(conversation) > self.config.max_conversation_history:
                conversation[:] = conversation[-self.config.max_conversation_history:]
                
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            yield f"<div class='error'>Error: {str(e)}</div>"
            
    def _build_context(self, search_results: list) -> str:
        """Build context string from search results"""
        if not search_results:
            return "No relevant documents found."
        
        context_parts = []
        for idx, result in enumerate(search_results, 1):
            title = result.get("title", "Untitled")
            content = result.get("content", "")[:self.config.context_chars_per_document]
            
            context_parts.append(f"[DOCUMENT {idx}: {title}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _build_messages(self, user_message: str, context: str, conversation: list) -> list:
        """Build message list for AI model"""
        # Detect if this is a document content question
        doc_keywords = ['summarize', 'what does', 'analyze', 'review', 'explain', 'find in', 
                       'extract from', 'show me from', 'according to', 'in the document',
                       'in the nda', 'in the contract', 'in the agreement', 'in the policy',
                       'confidentiality', 'obligations', 'terms', 'provisions', 'clauses']
        
        is_doc_question = any(keyword in user_message.lower() for keyword in doc_keywords)
        
        system_content = AGENT_INSTRUCTIONS
        if is_doc_question:
            system_content += "\n\n🚨 IMPORTANT: This is a DOCUMENT CONTENT question. Answer from the provided documents below. DO NOT use any tools like search_cases, search_invoices, etc."
        
        messages = [
            {"role": "system", "content": system_content}
        ]
        
        # Add conversation history (last N messages)
        messages.extend(conversation)
        
        # Add current query with context
        if is_doc_question:
            user_content = f"""Based on these documents:

{context}

User question: {user_message}

IMPORTANT: 
1. Answer this question using ONLY the document content provided above. Do NOT call any external functions or tools.
2. ALWAYS cite your sources by mentioning which document(s) you found the information in.
3. At the end of your response, add: <p><em>Source: [document name]</em></p>
4. Include an HTML comment with source numbers like: <!-- SOURCES: 1,2 -->"""
        else:
            user_content = f"""Based on these documents:

{context}

User question: {user_message}

Remember to cite sources when using information from the documents above."""
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def _format_tool_result(self, function_name: str, data: dict) -> str:
        """Format tool result data in natural language HTML"""
        try:
            if function_name == "get_case_details":
                case = data
                attorney = case.get("attorney", {})
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #212529;'>{case.get('title', 'Unknown Case')}</h4>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Case Number:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('case_number', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Type:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('type', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Status:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><span style='padding: 2px 8px; background: #17a2b8; color: white; border-radius: 3px; font-size: 0.85em;'>{case.get('status', 'N/A')}</span></td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Client:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('client', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Filed Date:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('filed_date', 'N/A')}</td></tr>
                """
                if attorney:
                    html += f"""
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Attorney:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('name', 'N/A')} ({attorney.get('specialty', 'N/A')})</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Contact:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('email', 'N/A')}</td></tr>
                    """
                if case.get('next_hearing'):
                    html += f"""<tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Next Hearing:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('next_hearing')}</td></tr>"""
                if case.get('estimated_value'):
                    html += f"""<tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Estimated Value:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>${case.get('estimated_value'):,.2f}</td></tr>"""
                html += "</table>"
                return html
            
            elif function_name == "search_cases":
                cases = data if isinstance(data, list) else []
                if not cases:
                    return "<p>No cases found.</p>"
                html = f"<p><strong>Found {len(cases)} case(s):</strong></p><ul style='margin: 10px 0; padding-left: 20px;'>"
                for case in cases:
                    status_color = "#28a745" if case.get("status") == "Active" else "#6c757d"
                    html += f"""
                    <li style='margin: 5px 0;'>
                        <strong>{case.get('title', 'Unknown')}</strong> ({case.get('case_number', 'N/A')})<br>
                        <span style='font-size: 0.9em; color: #6c757d;'>Type: {case.get('type', 'N/A')} | Status: <span style='color: {status_color};'>{case.get('status', 'N/A')}</span> | Client: {case.get('client', 'N/A')}</span>
                    </li>
                    """
                html += "</ul>"
                return html
            
            elif function_name == "get_invoice":
                invoice = data
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #212529;'>Invoice {invoice.get('invoice_number', 'N/A')}</h4>
                <table style='width: 100%; border-collapse: collapse; margin-bottom: 10px;'>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Client:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{invoice.get('client_name', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Date:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{invoice.get('date', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Status:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>
                        <span style='padding: 2px 8px; background: {"#28a745" if invoice.get("status") == "PAID" else "#ffc107"}; color: white; border-radius: 3px; font-size: 0.85em;'>{invoice.get('status', 'N/A')}</span>
                    </td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Total:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>${invoice.get('total', 0):,.2f}</strong></td></tr>
                </table>
                """
                items = invoice.get('items', [])
                if items:
                    html += "<p><strong>Line Items:</strong></p><ul style='margin: 5px 0; padding-left: 20px;'>"
                    for item in items:
                        html += f"<li>{item.get('description', 'N/A')}: ${item.get('amount', 0):,.2f}</li>"
                    html += "</ul>"
                return html
            
            elif function_name == "search_invoices":
                invoices = data if isinstance(data, list) else []
                if not invoices:
                    return "<p>No invoices found.</p>"
                html = f"<p><strong>Found {len(invoices)} invoice(s):</strong></p><ul style='margin: 10px 0; padding-left: 20px;'>"
                for inv in invoices:
                    status_color = "#28a745" if inv.get("status") == "PAID" else "#ffc107"
                    html += f"""
                    <li style='margin: 5px 0;'>
                        <strong>{inv.get('invoice_number', 'N/A')}</strong> - {inv.get('client_name', 'N/A')}<br>
                        <span style='font-size: 0.9em; color: #6c757d;'>Date: {inv.get('date', 'N/A')} | Amount: ${inv.get('total', 0):,.2f} | Status: <span style='color: {status_color};'>{inv.get('status', 'N/A')}</span></span>
                    </li>
                    """
                html += "</ul>"
                return html
            
            elif function_name == "get_client_invoices":
                client_name = data.get('client_name', 'Unknown Client')
                invoices = data.get('invoices', [])
                total = data.get('total_amount', 0)
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #212529;'>Invoices for {client_name}</h4>
                <p><strong>Total Amount: ${total:,.2f}</strong></p>
                """
                if invoices:
                    html += "<ul style='margin: 10px 0; padding-left: 20px;'>"
                    for inv in invoices:
                        status_color = "#28a745" if inv.get("status") == "PAID" else "#ffc107"
                        html += f"""
                        <li style='margin: 5px 0;'>
                            {inv.get('invoice_number', 'N/A')} - ${inv.get('total', 0):,.2f}
                            <span style='padding: 2px 6px; margin-left: 5px; background: {status_color}; color: white; border-radius: 3px; font-size: 0.8em;'>{inv.get('status', 'N/A')}</span>
                            <br><span style='font-size: 0.9em; color: #6c757d;'>{inv.get('date', 'N/A')}</span>
                        </li>
                        """
                    html += "</ul>"
                return html
            
            elif function_name == "get_attorney_info":
                attorney = data
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #212529;'>{attorney.get('name', 'Unknown Attorney')}</h4>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Specialty:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('specialty', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Experience:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('years_experience', 0)} years</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Hourly Rate:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>${attorney.get('hourly_rate', 0):,.2f}/hour</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Bar Number:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('bar_number', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Email:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('email', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Phone:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{attorney.get('phone', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Available:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{"✓ Yes" if attorney.get('available') else "✗ No"}</td></tr>
                </table>
                """
                return html
            
            elif function_name == "get_legal_rates":
                rates = data.get('rates', []) if isinstance(data, dict) else data
                if not rates:
                    return "<p>No rates available.</p>"
                html = "<p><strong>Legal Service Rates:</strong></p><table style='width: 100%; border-collapse: collapse;'>"
                html += "<tr style='background: #e9ecef;'><th style='padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;'>Service</th><th style='padding: 8px; text-align: right; border-bottom: 2px solid #dee2e6;'>Rate</th></tr>"
                for rate in rates:
                    html += f"""
                    <tr>
                        <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{rate.get('service', 'N/A')}</td>
                        <td style='padding: 8px; text-align: right; border-bottom: 1px solid #dee2e6;'>${rate.get('rate', 0):,.2f}/{rate.get('unit', 'hour')}</td>
                    </tr>
                    """
                html += "</table>"
                return html
            
            elif function_name == "calculate_legal_estimate":
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #212529;'>Cost Estimate</h4>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Service:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{data.get('service_type', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Hours:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{data.get('hours', 0)}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Hourly Rate:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>${data.get('hourly_rate', 0):,.2f}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 2px solid #212529;'><strong>Total Estimate:</strong></td><td style='padding: 5px; border-bottom: 2px solid #212529;'><strong style='font-size: 1.1em; color: #28a745;'>${data.get('estimated_cost', 0):,.2f}</strong></td></tr>
                </table>
                """
                return html
            
            elif function_name == "create_legal_case":
                # Format new case details
                case = data
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #28a745;'>✓ Case Created: {case.get('title', 'Unknown Case')}</h4>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Case Number:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('case_number', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Type:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('type', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Status:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><span style='padding: 2px 8px; background: #17a2b8; color: white; border-radius: 3px; font-size: 0.85em;'>{case.get('status', 'N/A')}</span></td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Client:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('client', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Filed Date:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('filed_date', 'N/A')}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'><strong>Attorney ID:</strong></td><td style='padding: 5px; border-bottom: 1px solid #dee2e6;'>{case.get('attorney_id', 'N/A')}</td></tr>
                </table>
                """
                return html
            
            elif function_name == "update_case_status":
                # Format case update confirmation
                case = data
                html = f"""
                <h4 style='margin: 0 0 10px 0; color: #28a745;'>✓ Case Updated: {case.get('title', case.get('case_number', 'Unknown'))}</h4>
                <p><strong>New Status:</strong> <span style='padding: 2px 8px; background: #17a2b8; color: white; border-radius: 3px; font-size: 0.9em;'>{case.get('status', 'N/A')}</span></p>
                <p style='font-size: 0.9em; color: #6c757d;'>Case Number: {case.get('case_number', 'N/A')}</p>
                """
                return html
            
            elif function_name in ["call_external_api", "email", "teams"]:
                # Communication actions - show confirmation
                return f"<p>✓ Action completed successfully</p>"
            
            # Return None to use default JSON formatting
            return None
            
        except Exception as e:
            logger.error(f"Error formatting {function_name} result: {e}")
            return None
    
    async def get_response(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        security_enabled: bool = True
    ) -> str:
        """
        Get complete response (non-streaming)
        
        Args:
            message: User message
            session_id: Conversation session ID
            user_id: User ID for security filtering
            security_enabled: Whether to apply security filters
            
        Returns:
            Complete response string
        """
        response_parts = []
        async for chunk in self.chat(message, session_id, user_id, security_enabled):
            response_parts.append(chunk)
        return "".join(response_parts)
    
    async def _execute_tool_call(self, tool_call: Dict) -> str:
        """
        Execute a function/tool call
        
        Args:
            tool_call: Tool call definition from AI model
            
        Returns:
            HTML formatted result
        """
        import json
        
        function_name = tool_call["function"]["name"]
        
        try:
            # Parse arguments
            arguments = json.loads(tool_call["function"]["arguments"])
            
            logger.info(f"Executing tool: {function_name} with args: {arguments}")
            
            result = None
            
            # Import database tools on first use
            try:
                from ..tools.database_tools import db_tools
                use_database = True
            except ImportError:
                use_database = False
                logger.warning("Database tools not available, falling back to API")
            
            # Execute the appropriate function - prioritize database over API
            if use_database and function_name in ["search_cases", "get_case_details", "create_legal_case", 
                                                    "update_case_status", "get_attorney_info", "search_invoices", 
                                                    "get_invoice", "get_legal_rates"]:
                # Use database tools
                if function_name == "search_cases":
                    result = await db_tools.search_cases_db(**arguments)
                elif function_name == "get_case_details":
                    result = await db_tools.get_case_details_db(**arguments)
                elif function_name == "create_legal_case":
                    result = await db_tools.create_legal_case_db(**arguments)
                elif function_name == "update_case_status":
                    result = await db_tools.update_case_status_db(**arguments)
                elif function_name == "get_attorney_info":
                    result = await db_tools.get_attorney_info_db(**arguments)
                elif function_name == "search_invoices":
                    result = await db_tools.search_invoices_db(**arguments)
                elif function_name == "get_invoice":
                    result = await db_tools.get_invoice_db(**arguments)
                elif function_name == "get_legal_rates":
                    result = await db_tools.get_legal_rates_db(**arguments)
            
            # Fallback to integration actions (API-based)
            elif function_name == "call_external_api":
                result = await self.integration_actions.call_external_api(**arguments)
                
            elif function_name == "send_email_notification":
                result = await self.integration_actions.send_email_notification(**arguments)
                
            elif function_name == "send_teams_notification":
                result = await self.integration_actions.send_teams_notification(**arguments)
                
            elif function_name == "generate_invoice":
                result = await self.integration_actions.generate_invoice(**arguments)
                
            elif function_name == "create_legal_case":
                result = await self.integration_actions.create_legal_case(**arguments)
                
            elif function_name == "update_case_status":
                result = await self.integration_actions.update_case_status(**arguments)
                
            elif function_name == "search_cases":
                result = await self.integration_actions.search_cases(**arguments)
                
            elif function_name == "get_case_details":
                result = await self.integration_actions.get_case_details(**arguments)
                
            elif function_name == "get_attorney_info":
                result = await self.integration_actions.get_attorney_info(**arguments)
                
            elif function_name == "get_legal_rates":
                result = await self.integration_actions.get_legal_rates(**arguments)
                
            elif function_name == "calculate_legal_estimate":
                result = await self.integration_actions.calculate_legal_estimate(**arguments)
                
            elif function_name == "search_invoices":
                result = await self.integration_actions.search_invoices(**arguments)
                
            elif function_name == "get_invoice":
                result = await self.integration_actions.get_invoice(**arguments)
                
            elif function_name == "get_client_invoices":
                result = await self.integration_actions.get_client_invoices(**arguments)
                
            else:
                result = {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
            
            # Format result as HTML
            if result.get("success"):
                html = f"""
                <div style='padding: 15px; background: #d4edda; border-left: 4px solid #28a745; border-radius: 4px; margin: 10px 0;'>
                    <p style='margin: 0 0 10px 0;'><strong>✓ Action Completed: {function_name}</strong></p>
                    <p style='margin: 0; color: #155724;'>{result.get('message', 'Success')}</p>
                """
                
                # Format data based on function type
                data = result.get("data")
                if function_name == "generate_invoice" and data and data.get("html"):
                    invoice_number = data.get("invoice_number")
                    total = data.get("total", 0)
                    html += f"""
                    <details style='margin-top: 10px;'>
                        <summary style='cursor: pointer; color: #0078D4;'>View Invoice {invoice_number} (${total:.2f})</summary>
                        {data["html"]}
                    </details>
                    """
                elif data:
                    formatted_content = self._format_tool_result(function_name, data)
                    if formatted_content:
                        html += f"""
                        <div style='margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;'>
                            {formatted_content}
                        </div>
                        <details style='margin-top: 10px;'>
                            <summary style='cursor: pointer; color: #6c757d; font-size: 0.9em;'>View Raw Data</summary>
                            <pre style='background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 0.85em;'>{json.dumps(data, indent=2)}</pre>
                        </details>
                        """
                    else:
                        # Fallback to raw JSON if no formatter exists
                        html += f"""
                        <details style='margin-top: 10px;'>
                            <summary style='cursor: pointer; color: #0078D4;'>View Details</summary>
                            <pre style='background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;'>{json.dumps(data, indent=2)}</pre>
                        </details>
                        """
                
                html += "</div>"
                return html
            else:
                error_msg = result.get("error", "Unknown error")
                return f"""
                <div style='padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; margin: 10px 0;'>
                    <p style='margin: 0; color: #721c24;'><strong>✗ Action Failed: {function_name}</strong></p>
                    <p style='margin: 5px 0 0 0; color: #721c24;'>{error_msg}</p>
                </div>
                """
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool arguments: {e}")
            return f"""
            <div style='padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; margin: 10px 0;'>
                <p style='margin: 0; color: #721c24;'><strong>✗ Invalid Arguments</strong></p>
                <p style='margin: 5px 0 0 0; color: #721c24;'>Failed to parse function arguments</p>
            </div>
            """
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}", exc_info=True)
            return f"""
            <div style='padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; margin: 10px 0;'>
                <p style='margin: 0; color: #721c24;'><strong>✗ Execution Error</strong></p>
                <p style='margin: 5px 0 0 0; color: #721c24;'>{str(e)}</p>
            </div>
            """
