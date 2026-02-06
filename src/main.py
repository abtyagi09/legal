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
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

try:
    from agent_framework.azure import AzureAIClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False

from src.config import load_config

# Import new agent module
from src.agent import LegalDocumentAgent, AgentConfig

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

# Global config and agent
config = None
legal_agent: Optional[LegalDocumentAgent] = None

# In-memory session storage (for production, use Redis or similar)
conversation_history = {}

# Helper function to get user ID from Azure AD authentication
def get_user_id(request: Request) -> Optional[str]:
    """Extract user ID from Azure Container Apps Easy Auth headers"""
    import base64
    import json
    
    principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    if principal_header:
        try:
            principal_data = base64.b64decode(principal_header).decode('utf-8')
            principal = json.loads(principal_data)
            logger.info(f"Principal data: {principal}")
            
            # Try multiple ways to get user ID
            user_id = principal.get('userId')
            if user_id:
                return user_id
            
            # Check claims for oid (object id)
            claims = {claim['typ']: claim['val'] for claim in principal.get('claims', [])}
            user_id = claims.get('oid') or claims.get('sub') or claims.get('http://schemas.microsoft.com/identity/claims/objectidentifier')
            
            if user_id:
                return user_id
                
            # Last resort - use first claim value
            if principal.get('claims'):
                return principal['claims'][0].get('val')
                
        except Exception as e:
            logger.error(f"Error parsing user principal: {e}")
    return None

# Pydantic models
class ToolConfig(BaseModel):
    data_source: Optional[str] = "auto"
    api_url: Optional[str] = ""
    enabled_tools: Optional[dict] = None

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    security_enabled: Optional[bool] = True
    enable_functions: Optional[bool] = True
    tool_config: Optional[ToolConfig] = None

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


@app.on_event("startup")
async def startup_event():
    """Initialize configuration and agent on startup"""
    global config, legal_agent
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
    
    # Initialize the new agent module
    try:
        logger.info("Initializing Legal Document Agent...")
        # Create agent config from loaded config
        agent_config = AgentConfig(
            foundry_endpoint=config.foundry_endpoint,
            foundry_model_deployment=config.foundry_model_deployment,
            search_endpoint=config.search_endpoint,
            search_index_name=config.search_index_name,
            search_api_key=config.search_api_key,
            doc_intel_endpoint=config.doc_intel_endpoint,
            doc_intel_api_key=config.doc_intel_api_key
        )
        legal_agent = LegalDocumentAgent(agent_config)
        await legal_agent.initialize()
        logger.info("✓ Legal Document Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        logger.warning("Agent will be unavailable - chat functionality may not work")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    global legal_agent
    if legal_agent:
        try:
            await legal_agent.cleanup()
            logger.info("Agent cleanup completed")
        except Exception as e:
            logger.error(f"Error during agent cleanup: {e}")


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
                SimpleField(name="owner_id", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="allowed_users", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
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
        
        # Try multiple ways to get user ID
        user_id = (principal.get('userId') or 
                  claims.get('oid') or 
                  claims.get('sub') or 
                  claims.get('http://schemas.microsoft.com/identity/claims/objectidentifier') or 
                  '')
        
        logger.info(f"User info - ID: {user_id}, Claims: {list(claims.keys())}")
        
        return {
            "authenticated": True,
            "id": user_id,
            "name": claims.get('name', claims.get('preferred_username', 'User')),
            "email": claims.get('preferred_username', claims.get('email', '')),
            "auth_type": principal.get('auth_typ', 'aad')
        }
    except Exception as e:
        logger.error(f"Error decoding user principal: {e}")
        return {"authenticated": False}


@app.get("/api/toolinfo")
async def get_tool_info():
    """Get available tools and their descriptions"""
    from src.tools.integration_actions import INTEGRATION_TOOLS
    
    tool_info = {
        "available_tools": [],
        "default_api_url": "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io",
        "data_sources": ["database", "api", "auto"],
        "categories": {
            "case_management": ["search_cases", "get_case_details", "create_legal_case", "update_case_status"],
            "invoice_management": ["search_invoices", "get_invoice", "get_client_invoices", "generate_invoice"],
            "attorney_rates": ["get_attorney_info", "get_legal_rates", "calculate_legal_estimate"],
            "communication": ["send_email_notification", "send_teams_notification"],
            "external_api": ["call_external_api"]
        }
    }
    
    # Extract tool information from INTEGRATION_TOOLS
    for tool in INTEGRATION_TOOLS:
        func = tool.get("function", {})
        tool_info["available_tools"].append({
            "name": func.get("name"),
            "description": func.get("description"),
            "parameters": list(func.get("parameters", {}).get("properties", {}).keys())
        })
    
    return tool_info


@app.get("/architecture", response_class=HTMLResponse)
async def architecture():
    """Serve the architecture visualization page"""
    arch_file = Path("architecture.html")
    if arch_file.exists():
        return arch_file.read_text()
    return "<h1>Architecture page not found</h1>"


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
            .user-info { position: absolute; top: 20px; right: 30px; display: flex; flex-direction: column; align-items: flex-end; gap: 5px; background: rgba(255, 255, 255, 0.15); padding: 10px 20px; border-radius: 15px; backdrop-filter: blur(10px); }
            .user-name { font-size: 14px; font-weight: 500; }
            .user-id { font-size: 10px; color: rgba(255, 255, 255, 0.8); font-family: monospace; }
            .signout-btn { background: rgba(255, 255, 255, 0.9); color: #667eea; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; margin-top: 5px; }
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
            
            .settings-btn { position: fixed; top: 20px; right: 20px; background: rgba(255, 255, 255, 0.95); color: #667eea; border: none; padding: 12px 16px; border-radius: 50%; cursor: pointer; font-size: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: all 0.3s; z-index: 1000; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; }
            .settings-btn:hover { background: white; transform: scale(1.1); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3); }
            .settings-panel { position: fixed; top: 0; right: -400px; width: 400px; height: 100vh; background: white; box-shadow: -4px 0 20px rgba(0,0,0,0.1); transition: right 0.3s ease; z-index: 999; overflow-y: auto; }
            .settings-panel.open { right: 0; }
            .settings-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; display: flex; justify-content: space-between; align-items: center; }
            .settings-header h2 { font-size: 1.5em; margin: 0; }
            .close-settings { background: rgba(255, 255, 255, 0.2); border: none; color: white; font-size: 24px; cursor: pointer; padding: 5px 12px; border-radius: 50%; transition: all 0.2s; }
            .close-settings:hover { background: rgba(255, 255, 255, 0.3); transform: rotate(90deg); }
            .settings-content { padding: 30px; }
            .settings-section { margin-bottom: 30px; padding-bottom: 25px; border-bottom: 1px solid #e0e0e0; }
            .settings-section:last-child { border-bottom: none; }
            .settings-section h3 { color: #333; font-size: 1.1em; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
            .settings-item { margin-bottom: 20px; }
            .settings-item label { display: flex; align-items: flex-start; gap: 12px; cursor: pointer; }
            .settings-item input[type="checkbox"] { margin-top: 3px; width: 20px; height: 20px; cursor: pointer; accent-color: #667eea; }
            .settings-item .label-text { flex: 1; }
            .settings-item .label-title { font-weight: 600; color: #333; margin-bottom: 4px; }
            .settings-item .label-desc { font-size: 13px; color: #666; line-height: 1.4; }
            .settings-status { background: #e8eaff; border-left: 4px solid #667eea; padding: 12px; border-radius: 4px; font-size: 13px; color: #333; display: none; margin-top: 15px; }
            .settings-status.show { display: block; animation: fadeIn 0.3s; }
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            .settings-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100vh; background: rgba(0, 0, 0, 0.5); display: none; z-index: 998; }
            .settings-overlay.show { display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏛️ Legal Document Agent</h1>
                <p>AI-powered document management and intelligent search for legal professionals</p>
                <div class="user-info" id="userInfo" style="display: none;">
                    <span class="user-name" id="userName">👤 Loading...</span>
                    <span class="user-id" id="userId"></span>
                    <button class="signout-btn" onclick="signOut()">Sign Out</button>
                </div>
            </div>
            
            <!-- Settings Button -->
            <button class="settings-btn" onclick="toggleSettingsPanel()" title="Settings">⚙️</button>
            
            <!-- Architecture Button -->
            <a href="/architecture" target="_blank" class="settings-btn" style="right: 90px; text-decoration: none; display: flex; align-items: center; justify-content: center;" title="View Architecture">
                🏛️
            </a>
            
            <!-- Settings Overlay -->
            <div class="settings-overlay" id="settingsOverlay" onclick="toggleSettingsPanel()"></div>
            
            <!-- Settings Panel -->
            <div class="settings-panel" id="settingsPanel">
                <div class="settings-header">
                    <h2>⚙️ Settings</h2>
                    <button class="close-settings" onclick="toggleSettingsPanel()">×</button>
                </div>
                <div class="settings-content">
                    <!-- Security Settings -->
                    <div class="settings-section">
                        <h3>🔒 Security & Privacy</h3>
                        <div class="settings-item">
                            <label>
                                <input type="checkbox" id="settingsEnableSecurity" onchange="updateSecuritySetting()" checked>
                                <div class="label-text">
                                    <div class="label-title">Document-Level Security</div>
                                    <div class="label-desc">When enabled, you can only view and search documents you uploaded. Disable to see all documents in the system (if you have access).</div>
                                </div>
                            </label>
                        </div>
                    </div>
                    
                    <!-- Agent Features -->
                    <div class="settings-section">
                        <h3>🤖 Agent Features</h3>
                        <div class="settings-item">
                            <label>
                                <input type="checkbox" id="settingsEnableFunctions" onchange="updateFunctionsSetting()" checked>
                                <div class="label-text">
                                    <div class="label-title">Enable Integration Actions</div>
                                    <div class="label-desc">Allow the agent to call external APIs, send notifications, generate invoices, and manage legal cases. Recommended for full functionality.</div>
                                </div>
                            </label>
                        </div>
                    </div>
                    
                    <!-- Tool Configuration -->
                    <div class="settings-section">
                        <h3>🔧 Tool Configuration</h3>
                        
                        <!-- Data Source Preference -->
                        <div class="settings-item" style="border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 15px;">
                            <label style="font-weight: 600; color: #333; margin-bottom: 10px; display: block;">Data Source</label>
                            <select id="settingsDataSource" onchange="updateDataSourceSetting()" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                                <option value="database">SQLite Database (Local)</option>
                                <option value="api">External API</option>
                                <option value="auto">Auto (Database First, then API)</option>
                            </select>
                            <div style="font-size: 12px; color: #666; margin-top: 5px;">Choose where to retrieve case and invoice data</div>
                        </div>
                        
                        <!-- API Configuration -->
                        <div class="settings-item" style="border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 15px;">
                            <label style="font-weight: 600; color: #333; margin-bottom: 10px; display: block;">Legal API Endpoint</label>
                            <input type="text" id="settingsApiUrl" onchange="updateApiUrlSetting()" 
                                   placeholder="https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io" 
                                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; font-family: monospace;">
                            <div style="font-size: 12px; color: #666; margin-top: 5px;">Base URL for legal management API</div>
                        </div>
                        
                        <!-- Available Tools -->
                        <div style="margin-top: 20px;">
                            <label style="font-weight: 600; color: #333; margin-bottom: 10px; display: block;">Enabled Tools</label>
                            
                            <!-- Case Management Tools -->
                            <details style="margin-bottom: 10px; border: 1px solid #eee; border-radius: 4px; padding: 10px;">
                                <summary style="cursor: pointer; font-weight: 500; color: #0078d4;">📋 Case Management (4)</summary>
                                <div style="padding: 10px 0 5px 20px;">
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolSearchCases" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>search_cases - Search legal cases</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolGetCaseDetails" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>get_case_details - Get case information</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolCreateCase" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>create_legal_case - Create new case</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolUpdateCase" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>update_case_status - Update case status</span>
                                    </label>
                                </div>
                            </details>
                            
                            <!-- Invoice Management Tools -->
                            <details style="margin-bottom: 10px; border: 1px solid #eee; border-radius: 4px; padding: 10px;">
                                <summary style="cursor: pointer; font-weight: 500; color: #0078d4;">💰 Invoice Management (4)</summary>
                                <div style="padding: 10px 0 5px 20px;">
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolSearchInvoices" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>search_invoices - Search invoices</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolGetInvoice" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>get_invoice - Get invoice details</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolGetClientInvoices" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>get_client_invoices - Get client invoices</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolGenerateInvoice" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>generate_invoice - Generate new invoice</span>
                                    </label>
                                </div>
                            </details>
                            
                            <!-- Attorney & Rate Tools -->
                            <details style="margin-bottom: 10px; border: 1px solid #eee; border-radius: 4px; padding: 10px;">
                                <summary style="cursor: pointer; font-weight: 500; color: #0078d4;">👔 Attorney & Rates (3)</summary>
                                <div style="padding: 10px 0 5px 20px;">
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolGetAttorney" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>get_attorney_info - Get attorney info</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolGetRates" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>get_legal_rates - Get service rates</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolCalculateEstimate" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>calculate_legal_estimate - Calculate cost</span>
                                    </label>
                                </div>
                            </details>
                            
                            <!-- Communication Tools -->
                            <details style="margin-bottom: 10px; border: 1px solid #eee; border-radius: 4px; padding: 10px;">
                                <summary style="cursor: pointer; font-weight: 500; color: #0078d4;">📧 Communication (2)</summary>
                                <div style="padding: 10px 0 5px 20px;">
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolSendEmail" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>send_email_notification - Send emails</span>
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolSendTeams" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>send_teams_notification - Send Teams messages</span>
                                    </label>
                                </div>
                            </details>
                            
                            <!-- External API Tool -->
                            <details style="margin-bottom: 10px; border: 1px solid #eee; border-radius: 4px; padding: 10px;">
                                <summary style="cursor: pointer; font-weight: 500; color: #0078d4;">🌐 External API (1)</summary>
                                <div style="padding: 10px 0 5px 20px;">
                                    <label style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                                        <input type="checkbox" id="toolCallApi" onchange="updateToolSettings()" checked style="margin-right: 8px;">
                                        <span>call_external_api - Call custom APIs</span>
                                    </label>
                                </div>
                            </details>
                            
                            <button onclick="resetToolSettings()" style="width: 100%; margin-top: 10px; padding: 8px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; font-size: 13px;">
                                ↺ Reset to Defaults
                            </button>
                        </div>
                    </div>
                    
                    <!-- Settings Info -->
                    <div class="settings-section">
                        <h3>ℹ️ About Settings</h3>
                        <div style="font-size: 13px; color: #666; line-height: 1.6;">
                            <p style="margin-bottom: 10px;"><strong>Document Security:</strong> Controls whether you see only your documents or all accessible documents.</p>
                            <p style="margin-bottom: 10px;"><strong>Integration Actions:</strong> Enables advanced features like API calls, notifications, invoice generation, and case management.</p>
                            <p style="margin-bottom: 0;">💡 Settings are saved to your browser and persist across sessions.</p>
                        </div>
                    </div>
                    
                    <div class="settings-status" id="settingsStatus">✓ Settings saved</div>
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

            // Settings Panel Management
            function toggleSettingsPanel() {
                const panel = document.getElementById('settingsPanel');
                const overlay = document.getElementById('settingsOverlay');
                panel.classList.toggle('open');
                overlay.classList.toggle('show');
            }

            function showSettingsStatus() {
                const status = document.getElementById('settingsStatus');
                status.classList.add('show');
                setTimeout(() => status.classList.remove('show'), 2000);
            }

            function getSecurityEnabled() {
                const saved = localStorage.getItem('documentSecurityEnabled');
                return saved === null ? true : saved === 'true';
            }

            function getFunctionsEnabled() {
                const saved = localStorage.getItem('enableFunctions');
                return saved === null ? true : saved === 'true';
            }

            function updateSecuritySetting() {
                const enabled = document.getElementById('settingsEnableSecurity').checked;
                localStorage.setItem('documentSecurityEnabled', enabled);
                // Reload documents with new security setting
                loadDocuments();
                showSettingsStatus();
            }

            function updateFunctionsSetting() {
                const enabled = document.getElementById('settingsEnableFunctions').checked;
                localStorage.setItem('enableFunctions', enabled);
                showSettingsStatus();
            }
            
            function updateDataSourceSetting() {
                const source = document.getElementById('settingsDataSource').value;
                localStorage.setItem('dataSource', source);
                showSettingsStatus();
            }
            
            function updateApiUrlSetting() {
                const url = document.getElementById('settingsApiUrl').value.trim();
                if (url) {
                    localStorage.setItem('legalApiUrl', url);
                    showSettingsStatus();
                }
            }
            
            function getToolSettings() {
                const saved = localStorage.getItem('enabledTools');
                if (saved) {
                    try {
                        return JSON.parse(saved);
                    } catch (e) {
                        console.error('Error parsing tool settings:', e);
                    }
                }
                // Default: all tools enabled
                return {
                    search_cases: true,
                    get_case_details: true,
                    create_legal_case: true,
                    update_case_status: true,
                    search_invoices: true,
                    get_invoice: true,
                    get_client_invoices: true,
                    generate_invoice: true,
                    get_attorney_info: true,
                    get_legal_rates: true,
                    calculate_legal_estimate: true,
                    send_email_notification: true,
                    send_teams_notification: true,
                    call_external_api: true
                };
            }
            
            function updateToolSettings() {
                const tools = {
                    search_cases: document.getElementById('toolSearchCases').checked,
                    get_case_details: document.getElementById('toolGetCaseDetails').checked,
                    create_legal_case: document.getElementById('toolCreateCase').checked,
                    update_case_status: document.getElementById('toolUpdateCase').checked,
                    search_invoices: document.getElementById('toolSearchInvoices').checked,
                    get_invoice: document.getElementById('toolGetInvoice').checked,
                    get_client_invoices: document.getElementById('toolGetClientInvoices').checked,
                    generate_invoice: document.getElementById('toolGenerateInvoice').checked,
                    get_attorney_info: document.getElementById('toolGetAttorney').checked,
                    get_legal_rates: document.getElementById('toolGetRates').checked,
                    calculate_legal_estimate: document.getElementById('toolCalculateEstimate').checked,
                    send_email_notification: document.getElementById('toolSendEmail').checked,
                    send_teams_notification: document.getElementById('toolSendTeams').checked,
                    call_external_api: document.getElementById('toolCallApi').checked
                };
                localStorage.setItem('enabledTools', JSON.stringify(tools));
                showSettingsStatus();
            }
            
            function resetToolSettings() {
                if (confirm('Reset all tool settings to defaults?')) {
                    localStorage.removeItem('enabledTools');
                    localStorage.removeItem('dataSource');
                    localStorage.removeItem('legalApiUrl');
                    loadSettingsState();
                    showSettingsStatus();
                }
            }

            function toggleSecurity() {
                // Legacy function - now just redirects to settings panel behavior
                const enabled = document.getElementById('settingsEnableSecurity').checked;
                localStorage.setItem('documentSecurityEnabled', enabled);
                // Reload documents with new security setting
                loadDocuments();
            }

            function loadSettingsState() {
                // Load saved settings into the settings panel
                document.getElementById('settingsEnableSecurity').checked = getSecurityEnabled();
                document.getElementById('settingsEnableFunctions').checked = getFunctionsEnabled();
                
                // Load data source setting
                const dataSource = localStorage.getItem('dataSource') || 'auto';
                document.getElementById('settingsDataSource').value = dataSource;
                
                // Load API URL
                const apiUrl = localStorage.getItem('legalApiUrl') || '';
                document.getElementById('settingsApiUrl').value = apiUrl;
                document.getElementById('settingsApiUrl').placeholder = 'https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io';
                
                // Load tool settings
                const tools = getToolSettings();
                document.getElementById('toolSearchCases').checked = tools.search_cases !== false;
                document.getElementById('toolGetCaseDetails').checked = tools.get_case_details !== false;
                document.getElementById('toolCreateCase').checked = tools.create_legal_case !== false;
                document.getElementById('toolUpdateCase').checked = tools.update_case_status !== false;
                document.getElementById('toolSearchInvoices').checked = tools.search_invoices !== false;
                document.getElementById('toolGetInvoice').checked = tools.get_invoice !== false;
                document.getElementById('toolGetClientInvoices').checked = tools.get_client_invoices !== false;
                document.getElementById('toolGenerateInvoice').checked = tools.generate_invoice !== false;
                document.getElementById('toolGetAttorney').checked = tools.get_attorney_info !== false;
                document.getElementById('toolGetRates').checked = tools.get_legal_rates !== false;
                document.getElementById('toolCalculateEstimate').checked = tools.calculate_legal_estimate !== false;
                document.getElementById('toolSendEmail').checked = tools.send_email_notification !== false;
                document.getElementById('toolSendTeams').checked = tools.send_teams_notification !== false;
                document.getElementById('toolCallApi').checked = tools.call_external_api !== false;
            }

            // Store current user ID globally
            let currentUserId = null;

            // Load user information on page load
            async function loadUserInfo() {
                try {
                    const response = await fetch('/api/userinfo');
                    const data = await response.json();
                    
                    if (data.authenticated) {
                        currentUserId = data.id;
                        document.getElementById('userName').textContent = `👤 ${data.name}`;
                        document.getElementById('userId').textContent = `ID: ${data.id || 'N/A'}`;
                        document.getElementById('userInfo').style.display = 'flex';
                        
                    }
                    
                    // Load settings panel state
                    loadSettingsState();
                } catch (error) {
                    console.error('Error loading user info:', error);
                    // Still load settings even if user info fails
                    loadSettingsState();
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

                // Refresh document list after short delay to allow index to update
                setTimeout(() => loadDocuments(), 500);
                setTimeout(() => { status.style.display = 'none'; }, 5000);
            }

            async function deleteDocument(docId, docTitle) {
                if (!confirm(`Are you sure you want to delete "${docTitle}"?`)) {
                    return;
                }

                try {
                    const response = await fetch(`/api/documents/${docId}`, {
                        method: 'DELETE'
                    });

                    const result = await response.json();
                    
                    if (!response.ok) {
                        console.error('Delete failed:', result.detail);
                        return;
                    }
                    
                    console.log('Delete result:', result);
                    
                    // Reload document list after short delay to allow index to update
                    setTimeout(() => loadDocuments(), 500);
                } catch (error) {
                    console.error('Error deleting document:', error);
                }
            }

            async function loadDocuments() {
                try {
                    const securityEnabled = getSecurityEnabled();
                    const response = await fetch(`/api/documents?security=${securityEnabled}`);
                    const documents = await response.json();
                    
                    const list = document.getElementById('documentList');
                    if (documents.length === 0) {
                        list.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No documents yet. Upload some files to get started!</p>';
                        return;
                    }

                    list.innerHTML = documents.map(doc => {
                        const isOwner = currentUserId && doc.owner_id === currentUserId;
                        const buttonDisabled = !isOwner;
                        const buttonStyle = buttonDisabled 
                            ? 'padding: 6px 12px; background: #ccc; color: #666; border: none; border-radius: 4px; cursor: not-allowed; font-size: 13px;'
                            : 'padding: 6px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;';
                        const buttonTooltip = buttonDisabled 
                            ? 'Only the uploader can delete this document'
                            : 'Delete this document';
                        
                        return `
                            <div class="document-item" style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="flex: 1;">
                                    <div class="document-title">${doc.title}</div>
                                    <div class="document-meta">Uploaded: ${new Date(doc.upload_date).toLocaleDateString()}</div>
                                </div>
                                <button onclick="${buttonDisabled ? 'return false;' : `deleteDocument('${doc.id}', '${doc.title.replace(/'/g, "\\'")}')`}" 
                                        style="${buttonStyle}"
                                        ${buttonDisabled ? '' : `onmouseover="this.style.background='#c82333'" onmouseout="this.style.background='#dc3545'"`}
                                        ${buttonDisabled ? 'disabled' : ''}
                                        title="${buttonTooltip}">
                                    🗑️ Delete
                                </button>
                            </div>
                        `;
                    }).join('');
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

                // Add placeholder for agent response
                messagesDiv.innerHTML += '<div class="message agent-message" id="agent-response"></div>';
                const agentResponseDiv = document.getElementById('agent-response');
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                try {
                    const securityEnabled = getSecurityEnabled();
                    const functionsEnabled = getFunctionsEnabled();
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            message, 
                            session_id: sessionId, 
                            security_enabled: securityEnabled,
                            enable_functions: functionsEnabled
                        })
                    });

                    // Handle streaming response
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let fullResponse = '';

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value, { stream: true });
                        fullResponse += chunk;
                        agentResponseDiv.innerHTML = fullResponse;
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    }

                    // Remove the temporary ID after streaming completes
                    agentResponseDiv.removeAttribute('id');
                    
                } catch (error) {
                    agentResponseDiv.innerHTML = `<div style="background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px;">Error: ${error.message}</div>`;
                    agentResponseDiv.removeAttribute('id');
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
async def upload_document(file: UploadFile = File(...), request: Request = None):
    """Upload and index a document - supports PDF, DOCX, images (JPG, PNG, BMP, TIFF), and text files"""
    logger.info(f"Uploading file: {file.filename}, content_type: {file.content_type}")
    
    # Get current user ID
    user_id = get_user_id(request) if request else None
    logger.info(f"Upload by user: {user_id or 'anonymous'}")
    
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
                    
                    # Start analysis with prebuilt-layout model (better for tables and structured documents)
                    poller = await doc_client.begin_analyze_document(
                        "prebuilt-layout",
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
            "file_name": file.filename,
            "owner_id": user_id or "anonymous",
            "allowed_users": [user_id] if user_id else ["anonymous"]
        }
        
        # Add vector if generated successfully
        if content_vector:
            document["content_vector"] = content_vector
            logger.info(f"✓ Added {len(content_vector)}-dimensional embedding to document")
        
        logger.info(f"Indexing document - ID: {doc_id}, Content: {len(content_for_index)} chars, Method: {extraction_method}, Has Vector: {bool(content_vector)}, Owner: {user_id or 'anonymous'}")
        
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


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, request: Request = None):
    """Delete a document from the search index (only owner can delete)"""
    try:
        # Get current user ID
        user_id = get_user_id(request) if request else None
        logger.info(f"Delete request for document: {document_id} by user: {user_id or 'anonymous'}")
        
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            # First, verify the user owns this document
            document = await search_client.get_document(key=document_id)
            document_owner = document.get("owner_id")
            
            logger.info(f"Document owner: {document_owner}, Requesting user: {user_id}")
            
            # Check if user is the owner
            if user_id and document_owner and user_id != document_owner:
                logger.warning(f"User {user_id} attempted to delete document owned by {document_owner}")
                raise HTTPException(
                    status_code=403, 
                    detail="You can only delete documents that you uploaded"
                )
            
            # Delete the document from the index
            result = await search_client.delete_documents(documents=[{"id": document_id}])
            logger.info(f"Delete result: {result}")
            
            return {
                "status": "success",
                "message": f"Document {document_id} deleted successfully"
            }
            
        finally:
            await search_client.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def get_documents(request: Request = None, security: bool = True):
    """Get list of indexed documents"""
    try:
        # Get current user ID
        user_id = get_user_id(request) if request else None
        logger.info(f"Fetching documents for user: {user_id or 'anonymous'} (security: {security})")
        
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            # Build security filter
            security_filter = None
            if security:
                if user_id:
                    security_filter = f"allowed_users/any(u: u eq '{user_id}')"
                    logger.info(f"Applying document list filter for user {user_id}: {security_filter}")
                else:
                    security_filter = "allowed_users/any(u: u eq 'anonymous')"
                    logger.info(f"Applying document list filter for anonymous: {security_filter}")
            else:
                logger.info("Document-level security disabled - showing all documents")
            
            results = await search_client.search(
                search_text="*",
                select=["id", "title", "upload_date", "file_name", "content", "owner_id"],
                filter=security_filter,
                order_by=["upload_date desc"],
                top=50
            )
            
            documents = []
            async for result in results:
                documents.append({
                    "id": result["id"],
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", "")[:200] + "..." if result.get("content") else "",
                    "owner_id": result.get("owner_id"),
                    "content_length": len(result.get("content", "")),
                    "upload_date": result.get("upload_date", "")
                })
            
            return documents
            
        finally:
            await search_client.close()
            
    except Exception as e:
        logger.error(f"Error fetching documents: {e}", exc_info=True)
        return []


@app.get("/api/documents/{document_id}/content")
async def get_document_content(document_id: str):
    """Get the full extracted content of a specific document for debugging"""
    try:
        search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=AzureKeyCredential(config.search_api_key)
        )
        
        try:
            # Get the specific document
            result = await search_client.get_document(key=document_id)
            
            return {
                "id": result.get("id"),
                "title": result.get("title"),
                "file_name": result.get("file_name"),
                "upload_date": result.get("upload_date"),
                "content": result.get("content", ""),
                "content_length": len(result.get("content", "")),
                "has_vector": "content_vector" in result
            }
            
        finally:
            await search_client.close()
            
    except Exception as e:
        logger.error(f"Error getting document content: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}")


@app.post("/api/chat")
async def chat(message: ChatMessage, request: Request = None):
    """Chat with the agent using the new LegalDocumentAgent"""
    try:
        # Check if agent is initialized
        if not legal_agent:
            logger.error("Legal agent not initialized")
            return JSONResponse(
                status_code=503,
                content={"error": "Agent not available. Please try again later."}
            )
        
        # Get current user ID for security filtering
        user_id = get_user_id(request) if request else None
        security_enabled = message.security_enabled
        enable_functions = message.enable_functions
        tool_config = message.tool_config
        
        # Log tool configuration
        if tool_config:
            logger.info(f"Tool config - Data source: {tool_config.data_source}, API URL: {tool_config.api_url}")
            if tool_config.enabled_tools:
                enabled_count = sum(1 for v in tool_config.enabled_tools.values() if v)
                logger.info(f"Enabled tools: {enabled_count}/{len(tool_config.enabled_tools)}")
        
        logger.info(f"Chat query: {message.message} (User: {user_id or 'anonymous'}, Security: {security_enabled}, Functions: {enable_functions})")
        
        # Use streaming response for better UX
        async def generate_stream():
            """Generate streaming response from agent"""
            try:
                session_id = message.session_id or str(uuid.uuid4())
                
                # Stream response from agent
                async for chunk in legal_agent.chat(
                    message=message.message,
                    session_id=session_id,
                    user_id=user_id,
                    security_enabled=security_enabled,
                    enable_functions=enable_functions
                ):
                    yield chunk
                    
            except Exception as e:
                logger.error(f"Error in agent stream: {e}", exc_info=True)
                error_msg = f"<div style='padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px;'>"
                error_msg += f"<p style='margin: 0; color: #721c24;'><strong>Error:</strong> {str(e)}</p>"
                error_msg += "</div>"
                yield error_msg
        
        # Return streaming response
        from starlette.responses import StreamingResponse
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain"
        )
        
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


