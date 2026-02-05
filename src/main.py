"""
Legal Document Management AI Agent - Main Application
Built with Microsoft Agent Framework, Azure AI Search, and Azure Document Intelligence
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchFieldDataType
from azure.search.documents.models import VectorizedQuery
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from openai import AsyncAzureOpenAI

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

try:
    from agent_framework.azure import AzureAIClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False

from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Legal Document Agent", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global config
config = None

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class SearchQuery(BaseModel):
    query: str
    top: int = 5

class DocumentInfo(BaseModel):
    id: str
    title: str
    content: str
    upload_date: str


class LegalDocumentAgent:
    """
    Legal Document Management AI Agent
    
    Provides intelligent search and document management capabilities for legal professionals
    using Microsoft Agent Framework with Azure AI services.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the Legal Document Agent
        
        Args:
            config_path: Path to configuration file
        """
        logger.info("Initializing Legal Document Agent...")
        
        # Load configuration
        self.config = load_config(config_path)
        logger.info("Configuration loaded successfully")
        
        # Agent client will be initialized in async context
        self.agent = None
        self.credential = None
        
    async def initialize(self):
        """Initialize async resources"""
        logger.info("Setting up Azure credentials...")
        self.credential = DefaultAzureCredential()
        
        # Create tools
        logger.info("Initializing AI tools...")
        
        # Document Intelligence tool
        doc_intel_tool = create_document_intelligence_tool(
            endpoint=self.config.doc_intel_endpoint,
            api_key=self.config.doc_intel_api_key,
            model=self.config.get("document_intelligence", "model", default="prebuilt-document")
        )
        
        # Azure AI Search tools
        search_tools = create_search_tool(
            service_endpoint=self.config.search_endpoint,
            api_key=self.config.search_api_key,
            index_name=self.config.search_index_name,
            top_results=self.config.get("search", "top_results", default=5)
        )
        
        # Combine all tools
        all_tools = [doc_intel_tool] + search_tools
        
        logger.info(f"Initialized {len(all_tools)} tools for the agent")
        
        # Create the Azure AI client
        logger.info("Creating AI agent...")
        client = AzureAIClient(
            project_endpoint=self.config.foundry_endpoint,
            model_deployment_name=self.config.foundry_model_deployment,
            credential=self.credential,
        )
        
        # Create agent using the agents property
        self.agent = await client.agents.create_agent(
            name=self.config.agent_name,
            instructions=self.config.agent_instructions,
            tools=all_tools,
        )
        
        logger.info("✓ Legal Document Agent initialized successfully!")
        return self
    
    async def cleanup(self):
        """Cleanup async resources"""
        if self.agent:
            await self.agent.__aexit__(None, None, None)
        if self.credential:
            await self.credential.close()
    
    async def run_interactive(self):
        """
        Run the agent in interactive mode
        
        Allows users to chat with the agent via command line
        """
        print("\n" + "="*60)
        print("🏛️  LEGAL DOCUMENT MANAGEMENT AI AGENT")
        print("="*60)
        print("\nWelcome! I'm your AI assistant for legal document management.")
        print("I can help you:")
        print("  • Search for legal documents semantically")
        print("  • Extract information from documents")
        print("  • Analyze contracts, briefs, and legal files")
        print("  • Answer questions about your legal documents")
        print("\nType 'quit' or 'exit' to end the session.")
        print("="*60 + "\n")
        
        # Create a persistent thread for conversation context
        thread = self.agent.get_new_thread()
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Goodbye! Thank you for using Legal Document Agent.")
                    break
                
                # Process the query with streaming
                print("\n🤖 Agent: ", end="", flush=True)
                
                async for chunk in self.agent.run_stream(user_input, thread=thread):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                
                print()  # New line after response
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"\n❌ Error: {str(e)}")
    
    async def run_single_query(self, query: str) -> str:
        """
        Run a single query against the agent
        
        Args:
            query: User query
            
        Returns:
            Agent response
        """
        logger.info(f"Processing query: {query}")
        
        thread = self.agent.get_new_thread()
        response_parts = []
        
        async for chunk in self.agent.run_stream(query, thread=thread):
            if chunk.text:
                response_parts.append(chunk.text)
        
        response = "".join(response_parts)
        logger.info("Query processed successfully")
        
        return response


@app.on_event("startup")
async def startup_event():
    """Initialize configuration on startup"""
    global config
    config = load_config()
    logger.info("Configuration loaded successfully")
    logger.info(f"Search endpoint: {config.search_endpoint}")
    logger.info(f"Search index: {config.search_index_name}")
    
    # Ensure search index exists
    try:
        await ensure_search_index()
        logger.info("Search index creation/verification completed")
    except Exception as e:
        logger.error(f"Failed to create search index: {e}", exc_info=True)


async def ensure_search_index():
    """Create search index if it doesn't exist"""
    index_client = SearchIndexClient(
        endpoint=config.search_endpoint,
        credential=AzureKeyCredential(config.search_api_key)
    )
    
    try:
        # Define the index schema
        index = SearchIndex(
            name=config.search_index_name,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String, sortable=True),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="upload_date", type=SearchFieldDataType.String, sortable=True),
                SimpleField(name="file_name", type=SearchFieldDataType.String),
            ]
        )
        
        await index_client.create_or_update_index(index)
        logger.info(f"Search index '{config.search_index_name}' ready")
    finally:
        await index_client.close()


@app.get("/api/userinfo")
async def get_user_info(request: Request):
    """Get authenticated user information from Azure AD"""
    # Azure Container Apps Easy Auth passes user info in headers
    principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    
    if not principal_header:
        return {"authenticated": False}
    
    try:
        import base64
        import json
        
        # Decode the base64 encoded principal
        decoded = base64.b64decode(principal_header).decode('utf-8')
        principal = json.loads(decoded)
        
        # Extract user information
        claims = {claim['typ']: claim['val'] for claim in principal.get('claims', [])}
        
        return {
            "authenticated": True,
            "name": claims.get('name', claims.get('preferred_username', 'User')),
            "email": claims.get('preferred_username', claims.get('email', '')),
            "auth_type": principal.get('auth_typ', 'aad')
        }
    except Exception as e:
        logger.error(f"Error decoding user principal: {e}")
        return {"authenticated": False}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend application"""
    html_content = Path("static/index.html").read_text() if Path("static/index.html").exists() else """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal Document Agent</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; }
            .header h1 { font-size: 2em; margin-bottom: 10px; }
            .header p { opacity: 0.9; }
            .user-info { position: absolute; top: 20px; right: 30px; display: flex; align-items: center; gap: 15px; background: rgba(255, 255, 255, 0.15); padding: 10px 20px; border-radius: 25px; backdrop-filter: blur(10px); }
            .user-name { font-size: 14px; font-weight: 500; }
            .signout-btn { background: rgba(255, 255, 255, 0.9); color: #667eea; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }
            .signout-btn:hover { background: white; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
            .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .panel { background: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .panel h2 { color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
            .upload-zone { border: 2px dashed #667eea; border-radius: 8px; padding: 40px; text-align: center; background: #f8f9ff; transition: all 0.3s; cursor: pointer; }
            .upload-zone:hover { background: #e8eaff; border-color: #764ba2; }
            .upload-zone.dragover { background: #e8eaff; border-color: #764ba2; transform: scale(1.02); }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: transform 0.2s; }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3); }
            .btn:disabled { opacity: 0.5; cursor: not-allowed; }
            .chat-container { display: flex; flex-direction: column; height: 600px; }
            .messages { flex: 1; overflow-y: auto; padding: 20px; background: #f8f9ff; border-radius: 8px; margin-bottom: 15px; }
            .message { margin-bottom: 15px; padding: 12px 16px; border-radius: 8px; max-width: 80%; }
            .user-message { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-left: auto; }
            .agent-message { background: #e8eaff; color: #333; }
            .input-group { display: flex; gap: 10px; }
            .input-group input { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px; }
            .input-group input:focus { outline: none; border-color: #667eea; }
            .document-list { max-height: 400px; overflow-y: auto; }
            .document-item { padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 10px; transition: all 0.2s; }
            .document-item:hover { background: #f8f9ff; border-color: #667eea; }
            .document-title { font-weight: 600; color: #333; margin-bottom: 5px; }
            .document-meta { font-size: 12px; color: #666; }
            .status { padding: 10px; border-radius: 6px; margin-bottom: 15px; display: none; }
            .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏛️ Legal Document Agent</h1>
                <p>AI-powered document management and intelligent search for legal professionals</p>
                <div class="user-info" id="userInfo" style="display: none;">
                    <span class="user-name" id="userName">👤 Loading...</span>
                    <button class="signout-btn" onclick="signOut()">Sign Out</button>
                </div>
            </div>
            
            <div class="main-grid">
                <!-- Upload Panel -->
                <div class="panel">
                    <h2>📄 Upload Documents</h2>
                    <div id="uploadStatus" class="status"></div>
                    <div class="upload-zone" id="uploadZone">
                        <p style="font-size: 48px; margin-bottom: 10px;">📁</p>
                        <p style="font-size: 16px; color: #666; margin-bottom: 15px;">Drag and drop files here or click to browse</p>
                        <input type="file" id="fileInput" multiple accept=".pdf,.docx,.txt" style="display: none;">
                        <button class="btn" onclick="document.getElementById('fileInput').click()">Select Files</button>
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <h3 style="color: #333; margin-bottom: 15px;">📚 Recent Documents</h3>
                        <div id="documentList" class="document-list"></div>
                    </div>
                </div>
                
                <!-- Chat Panel -->
                <div class="panel">
                    <h2>💬 Chat with Agent</h2>
                    <div class="chat-container">
                        <div class="messages" id="messages">
                            <div class="message agent-message">
                                Hello! I'm your Legal Document AI Assistant. I can help you search through your documents, extract information, and answer questions about your legal files. How can I assist you today?
                            </div>
                        </div>
                        <div class="input-group">
                            <input type="text" id="chatInput" placeholder="Ask me anything about your documents..." onkeypress="if(event.key==='Enter') sendMessage()">
                            <button class="btn" onclick="sendMessage()">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let sessionId = null;

            // Load user information on page load
            async function loadUserInfo() {
                try {
                    const response = await fetch('/api/userinfo');
                    const data = await response.json();
                    
                    if (data.authenticated) {
                        document.getElementById('userName').textContent = `👤 ${data.name}`;
                        document.getElementById('userInfo').style.display = 'flex';
                    }
                } catch (error) {
                    console.error('Error loading user info:', error);
                }
            }

            function signOut() {
                // Azure Container Apps Easy Auth logout endpoint
                window.location.href = '/.auth/logout?post_logout_redirect_uri=' + encodeURIComponent(window.location.origin);
            }

            // Upload zone drag and drop
            const uploadZone = document.getElementById('uploadZone');
            const fileInput = document.getElementById('fileInput');

            uploadZone.addEventListener('click', () => fileInput.click());
            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('dragover');
            });
            uploadZone.addEventListener('dragleave', () => {
                uploadZone.classList.remove('dragover');
            });
            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
                handleFiles(e.dataTransfer.files);
            });

            fileInput.addEventListener('change', (e) => {
                handleFiles(e.target.files);
            });

            async function handleFiles(files) {
                const status = document.getElementById('uploadStatus');
                status.style.display = 'block';
                status.className = 'status';
                status.textContent = 'Uploading and indexing documents...';

                for (const file of files) {
                    try {
                        const formData = new FormData();
                        formData.append('file', file);

                        const response = await fetch('/api/upload', {
                            method: 'POST',
                            body: formData
                        });

                        if (!response.ok) throw new Error('Upload failed');
                        
                        const result = await response.json();
                        status.className = 'status success';
                        status.textContent = `✓ Successfully indexed: ${file.name}`;
                    } catch (error) {
                        status.className = 'status error';
                        status.textContent = `✗ Error uploading ${file.name}: ${error.message}`;
                    }
                }

                loadDocuments();
                setTimeout(() => { status.style.display = 'none'; }, 5000);
            }

            async function loadDocuments() {
                try {
                    const response = await fetch('/api/documents');
                    const documents = await response.json();
                    
                    const list = document.getElementById('documentList');
                    if (documents.length === 0) {
                        list.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No documents yet. Upload some files to get started!</p>';
                        return;
                    }

                    list.innerHTML = documents.map(doc => `
                        <div class="document-item">
                            <div class="document-title">${doc.title}</div>
                            <div class="document-meta">Uploaded: ${new Date(doc.upload_date).toLocaleDateString()}</div>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading documents:', error);
                }
            }

            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;

                const messagesDiv = document.getElementById('messages');
                
                // Add user message
                messagesDiv.innerHTML += `<div class="message user-message">${message}</div>`;
                input.value = '';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Add loading indicator
                messagesDiv.innerHTML += '<div class="message agent-message" id="loading"><div class="loading"></div> Thinking...</div>';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message, session_id: sessionId })
                    });

                    const data = await response.json();
                    sessionId = data.session_id;

                    // Remove loading indicator
                    document.getElementById('loading').remove();

                    // Add agent response
                    messagesDiv.innerHTML += `<div class="message agent-message">${data.response}</div>`;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } catch (error) {
                    document.getElementById('loading').remove();
                    messagesDiv.innerHTML += `<div class="message agent-message" style="background: #f8d7da; color: #721c24;">Error: ${error.message}</div>`;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
            }

            // Load documents on page load
            loadDocuments();
            
            // Load user information
            loadUserInfo();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        return {
            "status": "healthy",
            "configuration": "loaded",
            "foundry_configured": bool(config.foundry_endpoint),
            "search_configured": bool(config.search_endpoint),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text using Azure OpenAI"""
    try:
        if not config.openai_endpoint:
            logger.warning("Azure OpenAI endpoint not configured, skipping embedding generation")
            return []
        
        # Create OpenAI client with managed identity or API key
        from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
        from azure.core.credentials import AzureKeyCredential
        
        if config.openai_api_key:
            # Use API key if provided
            client = AsyncAzureOpenAI(
                azure_endpoint=config.openai_endpoint,
                api_key=config.openai_api_key,
                api_version="2024-02-01"
            )
            logger.info("Using Azure OpenAI with API key")
        else:
            # Use managed identity
            credential = AsyncDefaultAzureCredential()
            token_response = await credential.get_token("https://cognitiveservices.azure.com/.default")
            
            client = AsyncAzureOpenAI(
                azure_endpoint=config.openai_endpoint,
                azure_ad_token=token_response.token,
                api_version="2024-02-01"
            )
            logger.info("Using Azure OpenAI with managed identity")
        
        # Generate embedding
        # Truncate text to avoid token limits (max ~8000 tokens for text-embedding-3-small)
        text_for_embedding = text[:8000] if len(text) > 8000 else text
        
        response = await client.embeddings.create(
            model=config.openai_embedding_deployment,
            input=text_for_embedding
        )
        
        embedding = response.data[0].embedding
        logger.info(f"✓ Generated embedding vector with {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        logger.error(f"✗ Embedding generation failed: {e}", exc_info=True)
        return []


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document - supports PDF, DOCX, images (JPG, PNG, BMP, TIFF), and text files"""
    logger.info(f"Uploading file: {file.filename}, content_type: {file.content_type}")
    
    try:
        # Read file content
        content = await file.read()
        logger.info(f"File size: {len(content)} bytes")
        
        extracted_text = ""
        extraction_method = "unknown"
        
        # Get file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        # List of supported document and image formats
        doc_intel_formats = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'heif']
        
        # Try to extract text based on file type
        if file_ext == 'txt':
            # Simple text file
            extracted_text = content.decode('utf-8', errors='ignore')
            extraction_method = "text"
            logger.info(f"Extracted {len(extracted_text)} characters from text file")
        elif file_ext in doc_intel_formats:
            # Use Document Intelligence for PDF, DOCX, images, and other formats
            try:
                logger.info(f"Starting Document Intelligence analysis for {file_ext.upper()} file...")
                
                from azure.ai.formrecognizer.aio import DocumentAnalysisClient as AsyncDocumentAnalysisClient
                from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
                from io import BytesIO
                
                # Use async client with managed identity
                credential = AsyncDefaultAzureCredential()
                async with AsyncDocumentAnalysisClient(
                    endpoint=config.doc_intel_endpoint,
                    credential=credential
                ) as doc_client:
                    
                    # Start analysis with prebuilt-read model (supports text extraction from documents and images)
                    poller = await doc_client.begin_analyze_document(
                        "prebuilt-read",
                        document=BytesIO(content)
                    )
                    
                    logger.info("Waiting for Document Intelligence analysis to complete...")
                    result = await poller.result()
                    
                    # Extract text from result - content property has all text
                    if hasattr(result, 'content') and result.content:
                        extracted_text = result.content
                        extraction_method = "document_intelligence"
                        logger.info(f"✓ Successfully extracted {len(extracted_text)} characters using Document Intelligence")
                        logger.info(f"Preview: {extracted_text[:200]}...")
                    elif hasattr(result, 'pages') and result.pages:
                        # Fallback: extract from pages structure
                        text_parts = []
                        for page in result.pages:
                            if hasattr(page, 'lines'):
                                for line in page.lines:
                                    text_parts.append(line.content)
                        extracted_text = '\n'.join(text_parts)
                        extraction_method = "document_intelligence_pages"
                        logger.info(f"✓ Extracted {len(extracted_text)} characters from pages structure")
                    else:
                        logger.warning("⚠ No content found in Document Intelligence result")
                    
            except Exception as e:
                logger.error(f"✗ Document Intelligence failed: {str(e)}", exc_info=True)
                extraction_method = "error"
                extracted_text = ""
        else:
            # Unsupported format - try text fallback
            logger.warning(f"Unsupported file format: {file_ext}")
            try:
                decoded = content.decode('utf-8', errors='ignore')
                # Filter out binary junk - only keep printable text
                extracted_text = ''.join(c for c in decoded if c.isprintable() or c.isspace())
                if len(extracted_text) >= 50:
                    extraction_method = "fallback"
                    logger.info(f"Using fallback text extraction: {len(extracted_text)} characters")
                else:
                    extracted_text = ""
                    extraction_method = "unsupported"
            except Exception as decode_error:
                logger.error(f"Fallback extraction failed: {decode_error}")
                extracted_text = ""
                extraction_method = "error"
        
        # Validate extracted text
        if not extracted_text or len(extracted_text) < 10:
            logger.warning(f"⚠ Insufficient text extracted ({len(extracted_text)} chars). File: {file.filename}, Method: {extraction_method}")
            
            if extraction_method == "unsupported":
                extracted_text = f"Document '{file.filename}' format (.{file_ext}) is not supported. Supported formats: TXT, PDF, DOCX, DOC, JPG, JPEG, PNG, BMP, TIFF."
            elif extraction_method == "error":
                extracted_text = f"Document '{file.filename}' was uploaded but text extraction encountered an error. Please check the file format and try again."
            else:
                extracted_text = f"Document '{file.filename}' was uploaded but minimal text was extracted. The file may be empty, image-only, or require OCR processing."
        
        # Limit content size for indexing (Azure AI Search has limits)
        content_for_index = extracted_text[:50000] if len(extracted_text) > 50000 else extracted_text
        
        # Generate embedding vector for the content
        logger.info("Generating embedding vector for document...")
        content_vector = await generate_embedding(content_for_index)
        
        # Create document for indexing
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "title": file.filename,
            "content": content_for_index,
            "upload_date": datetime.utcnow().isoformat(),
            "file_name": file.filename
        }
        
        # Add vector if generated successfully
        if content_vector:
            document["content_vector"] = content_vector
            logger.info(f"✓ Added {len(content_vector)}-dimensional embedding to document")
        
        logger.info(f"Indexing document - ID: {doc_id}, Content: {len(content_for_index)} chars, Method: {extraction_method}, Has Vector: {bool(content_vector)}")
        
        # Index in Azure AI Search
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            result = await search_client.upload_documents(documents=[document])
            logger.info(f"Index result: {result}")
            logger.info(f"Successfully indexed document: {file.filename}")
        finally:
            await search_client.close()
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": file.filename,
            "extracted_length": len(extracted_text),
            "extraction_method": extraction_method,
            "preview": extracted_text[:200] if extracted_text else "No preview available",
            "message": "Document uploaded and indexed successfully" if len(extracted_text) > 50 else "Document uploaded but text extraction may have failed"
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def get_documents():
    """Get list of indexed documents"""
    try:
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            results = await search_client.search(
                search_text="*",
                select=["id", "title", "upload_date", "file_name", "content"],
                order_by=["upload_date desc"],
                top=50
            )
            
            documents = []
            async for result in results:
                documents.append({
                    "id": result["id"],
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", "")[:200] + "..." if result.get("content") else "",
                    "upload_date": result.get("upload_date", "")
                })
            
            return documents
            
        finally:
            await search_client.close()
            
    except Exception as e:
        logger.error(f"Error fetching documents: {e}", exc_info=True)
        return []


@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Chat with the agent using AI model with hybrid search (keyword + vector)"""
    try:
        logger.info(f"Chat query: {message.message}")
        
        # Generate query embedding for vector search
        logger.info("Generating query embedding for hybrid search...")
        query_vector = await generate_embedding(message.message)
        
        # Search for relevant documents using hybrid search
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            # Prepare vector query if embedding was generated
            vector_queries = []
            if query_vector:
                vector_queries.append(
                    VectorizedQuery(
                        vector=query_vector,
                        k_nearest_neighbors=10,  # Get more candidates for better filtering
                        fields="content_vector"
                    )
                )
                logger.info("✓ Using hybrid search (keyword + vector)")
            else:
                logger.info("⚠ Using keyword-only search (no embeddings)")
            
            # Perform hybrid search (combines keyword and vector search)
            results = await search_client.search(
                search_text=message.message,
                vector_queries=vector_queries if vector_queries else None,
                select=["title", "content", "file_name"],
                query_type="semantic" if not vector_queries else "simple",  # Use semantic ranking if no vectors
                semantic_configuration_name="default" if not vector_queries else None,
                top=5  # Get top 5 results for better context
            )
            
            context_docs = []
            result_count = 0
            async for result in results:
                result_count += 1
                content = result.get('content', '')
                if content:
                    # Get search score for ranking
                    score = result.get('@search.score', 0)
                    context_docs.append({
                        'title': result.get('title', 'Untitled'),
                        'content': content[:1500],  # Increased for better context
                        'score': score
                    })
            
            logger.info(f"Hybrid search found {result_count} results, {len(context_docs)} with content")
            
            # Generate AI response using the model
            if context_docs:
                logger.info("Context found, attempting to call AI model...")
                # Build context for the AI
                context_text = "\n\n".join([
                    f"Document: {doc['title']}\n{doc['content']}" 
                    for doc in context_docs
                ])
                
                # Call the AI model
                try:
                    logger.info("Importing AI inference client...")
                    from azure.ai.inference.aio import ChatCompletionsClient
                    from azure.ai.inference.models import SystemMessage, UserMessage
                    from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
                    from azure.core.credentials import AccessToken
                    
                    logger.info(f"Creating AI client with endpoint: {config.foundry_endpoint}")
                    
                    # Get token with correct scope for AI services
                    base_credential = AsyncDefaultAzureCredential()
                    token = await base_credential.get_token("https://cognitiveservices.azure.com/.default")
                    logger.info(f"✓ Got token with Cognitive Services scope")
                    
                    # Create a credential wrapper that returns the token
                    class TokenCredential:
                        def __init__(self, token):
                            self.token = token
                        
                        async def get_token(self, *scopes, **kwargs):
                            return self.token
                        
                        async def __aenter__(self):
                            return self
                        
                        async def __aexit__(self, *args):
                            pass
                    
                    credential = TokenCredential(token)
                    async with ChatCompletionsClient(
                        endpoint=config.foundry_endpoint,
                        credential=credential
                    ) as ai_client:
                        
                        logger.info(f"Calling AI model: {config.foundry_model_deployment}")
                        ai_response = await ai_client.complete(
                            model=config.foundry_model_deployment,
                            messages=[
                                SystemMessage(content="You are a helpful legal document assistant. Answer questions based on the provided document context. Format your response in HTML with proper styling. Use <div>, <p>, <strong>, <ul>, <li> tags as needed. Preserve important formatting like dates, amounts, and legal terms."),
                                UserMessage(content=f"Based on these documents:\n\n{context_text}\n\nUser question: {message.message}\n\nProvide a clear, well-formatted HTML response that directly answers the question.")
                            ],
                            temperature=0.7,
                            max_tokens=1000
                        )
                        
                        logger.info("✓ AI model response received")
                        ai_answer = ai_response.choices[0].message.content
                        
                        # Format the final response with sources
                        response = f"<div style='font-family: system-ui, -apple-system, sans-serif;'>"
                        response += f"<div style='padding: 15px; background: #f0f7ff; border-left: 4px solid #0078d4; border-radius: 4px; margin-bottom: 20px;'>"
                        response += ai_answer
                        response += "</div>"
                        
                        # Add source documents
                        response += f"<div style='margin-top: 20px;'><strong style='color: #666;'>📚 Sources ({len(context_docs)} documents):</strong></div>"
                        for doc in context_docs:
                            response += f"<div style='margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 13px; color: #555;'>"
                            response += f"📄 {doc['title']}"
                            response += "</div>"
                        response += "</div>"
                        
                except Exception as ai_error:
                    logger.error(f"AI model error: {ai_error}", exc_info=True)
                    # Fallback to search results
                    response = f"<div style='font-family: system-ui, -apple-system, sans-serif;'>"
                    response += f"<p><strong>Found {len(context_docs)} relevant document(s):</strong></p>"
                    
                    for doc in context_docs:
                        response += f"<div style='margin: 15px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #0078d4; border-radius: 4px;'>"
                        response += f"<div style='font-size: 16px; font-weight: 600; color: #0078d4; margin-bottom: 8px;'>📄 {doc['title']}</div>"
                        formatted_content = doc['content'].replace('\n', '<br>')
                        response += f"<div style='font-size: 14px; line-height: 1.6; color: #333;'>{formatted_content}"
                        if len(doc['content']) >= 1500:
                            response += "<span style='color: #666;'> ...</span>"
                        response += "</div></div>"
                    response += "</div>"
            else:
                response = f"<div style='padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;'>"
                response += f"<p style='margin: 0; color: #856404;'><strong>No documents found</strong></p>"
                response += f"<p style='margin: 8px 0 0 0; color: #856404;'>I searched for '{message.message}' but couldn't find matching documents. Try uploading documents first or ask about different topics.</p>"
                response += "</div>"
            
            session_id = message.session_id or str(uuid.uuid4())
            
            return ChatResponse(response=response, session_id=session_id)
            
        finally:
            await search_client.close()
            
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search_documents(query: SearchQuery):
    """Search documents using hybrid search (keyword + vector)"""
    try:
        # Generate query embedding
        query_vector = await generate_embedding(query.query)
        
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            # Prepare vector query if embedding was generated
            vector_queries = []
            if query_vector:
                vector_queries.append(
                    VectorizedQuery(
                        vector=query_vector,
                        k_nearest_neighbors=query.top,
                        fields="content_vector"
                    )
                )
                logger.info(f"Hybrid search with {len(query_vector)}-dim vector")
            
            results = await search_client.search(
                search_text=query.query,
                vector_queries=vector_queries if vector_queries else None,
                top=query.top
            )
            
            documents = []
            async for result in results:
                documents.append({
                    "id": result["id"],
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", "")[:500],
                    "upload_date": result.get("upload_date", ""),
                    "score": result.get("@search.score", 0)
                })
            
            return documents
            
        finally:
            await search_client.close()
            
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def main():
    """Main application entry point"""
    try:
        # Load configuration to verify it works
        global config
        config = load_config()
        logger.info("Configuration loaded successfully")
        logger.info(f"Foundry endpoint: {config.foundry_endpoint}")
        logger.info(f"Search endpoint: {config.search_endpoint}")
        logger.info("Starting web server...")
        
        # Start web server
        config_uvicorn = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info"
        )
        server = uvicorn.Server(config_uvicorn)
        await server.serve()
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error:\n{e}\n")
        print("Please ensure you have:")
        print("1. Copied config.example.yaml to config.yaml")
        print("2. Updated config.yaml with your Azure service credentials")
        
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        print(f"\n❌ Configuration Validation Error:\n{e}\n")
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
    # Run the agent
    asyncio.run(main())
