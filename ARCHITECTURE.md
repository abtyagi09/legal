# Modular Architecture - Legal Document Agent

## Overview

This document outlines the new modular architecture that separates concerns into distinct layers:
- **Agent Layer**: Core AI agent using Microsoft Agent Framework
- **API Layer**: RESTful FastAPI backend
- **Frontend Layer**: Static HTML/CSS/JavaScript web application

## Directory Structure

```
src/
├── agent/                              # Agent Layer
│   ├── __init__.py
│   ├── legal_agent.py                  # Main LegalDocumentAgent class
│   ├── config.py                       # AgentConfig dataclass
│   └── instructions.py                 # Agent system instructions
│
├── tools/                              # Existing tools (no changes)
│   ├── __init__.py
│   ├── document_intelligence_tool.py
│   └── search_tool.py
│
├── api/                                # API Layer
│   ├── __init__.py
│   ├── app.py                          # FastAPI application setup
│   ├── models.py                       # Pydantic request/response models
│   ├── dependencies.py                 # Shared dependencies (agent instance, etc.)
│   └── endpoints/                      # Endpoint modules
│       ├── __init__.py
│       ├── auth.py                     # /api/userinfo, authentication
│       ├── documents.py                # /api/documents, /api/upload
│       ├── chat.py                     # /api/chat
│       └── health.py                   # /health
│
├── frontend/                           # Frontend Layer
│   ├── index.html                      # Main HTML file
│   ├── css/
│   │   └── styles.css                  # Extracted CSS
│   └── js/
│       ├── app.js                      # Main application logic
│       ├── auth.js                     # Authentication functions
│       ├── documents.js                # Document management
│       └── chat.js                     # Chat functionality
│
├── config.py                           # Shared configuration (legacy compatibility)
└── main.py                             # Entry point (backward compatible)
```

## Architecture Layers

### 1. Agent Layer (`src/agent/`)

**Purpose**: Encapsulates all AI agent logic using Microsoft Agent Framework patterns

**Components**:

- `legal_agent.py`: Main agent class
  ```python
  class LegalDocumentAgent:
      async def initialize()
      async def chat(message, session_id, user_id, security_enabled) -> AsyncGenerator
      async def get_response(message, session_id, user_id, security_enabled) -> str
      async def cleanup()
  ```

- `config.py`: Agent configuration
  ```python
  @dataclass
  class AgentConfig:
      foundry_endpoint: str
      foundry_model_deployment: str
      temperature: float = 0.1
      max_tokens: int = 2000
      # ... all agent settings
      
      @classmethod
      def from_env(cls)
  ```

- `instructions.py`: Agent system instructions
  ```python
  AGENT_INSTRUCTIONS = """..."""  # Complete agent prompt
  ```

**Benefits**:
- Single responsibility: AI/agent logic only
- Reusable across different interfaces (API, CLI, notebook)
- Testable independently
- Clear configuration management

### 2. API Layer (`src/api/`)

**Purpose**: RESTful API for all backend operations

**Components**:

#### `app.py` - FastAPI Application

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Legal Document Agent API")

# Mount static files
app.mount("/static", StaticFiles(directory="src/frontend"), name="static")

# Include routers
from .endpoints import auth, documents, chat, health
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(health.router)

@app.on_event("startup")
async def startup():
    # Initialize agent instance
    pass

@app.on_event("shutdown")
async def shutdown():
    # Cleanup resources
    pass
```

#### `dependencies.py` - Shared Dependencies

```python
from fastapi import Depends
from ..agent import LegalDocumentAgent, AgentConfig

# Global agent instance
_agent: LegalDocumentAgent = None

async def get_agent() -> LegalDocumentAgent:
    """Dependency to get the initialized agent"""
    global _agent
    if _agent is None:
        config = AgentConfig.from_env()
        _agent = LegalDocumentAgent(config)
        await _agent.initialize()
    return _agent
```

#### `endpoints/auth.py` - Authentication Endpoints

```python
from fastapi import APIRouter, Request
from ..models import UserInfo

router = APIRouter(prefix="/api", tags=["auth"])

@router.get("/userinfo", response_model=UserInfo)
async def get_user_info(request: Request):
    """Extract user from Azure AD headers"""
    pass

def get_user_id(request: Request) -> Optional[str]:
    """Helper to extract user ID"""
    pass
```

#### `endpoints/documents.py` - Document Endpoints

```python
from fastapi import APIRouter, UploadFile, File
from ..models import DocumentInfo, UploadResponse

router = APIRouter(prefix="/api", tags=["documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index document"""
    pass

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(security: bool = True):
    """List documents with optional security filtering"""
    pass

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete document (owner only)"""
    pass
```

#### `endpoints/chat.py` - Chat Endpoints

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ..models import ChatRequest, ChatResponse
from ..dependencies import get_agent

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat")
async def chat(
    request: ChatRequest,
    agent: LegalDocumentAgent = Depends(get_agent)
):
    """Chat with the agent (streaming)"""
    async def generate():
        async for chunk in agent.chat(
            request.message,
            request.session_id,
            request.user_id,
            request.security_enabled
        ):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/plain")
```

### 3. Frontend Layer (`src/frontend/`)

**Purpose**: Clean separation of UI from backend logic

**Components**:

#### `index.html` - Structure

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <!-- HTML structure only -->
    <script src="/static/js/auth.js"></script>
    <script src="/static/js/documents.js"></script>
    <script src="/static/js/chat.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

#### `css/styles.css` - All Styles

```css
/* Clean, organized CSS */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
}

/* Component styles */
.header { ... }
.panel { ... }
/* etc. */
```

#### `js/auth.js` - Authentication Logic

```javascript
// User authentication functions
async function loadUserInfo() { ... }
async function signOut() { ... }
function getUserId() { ... }
```

#### `js/documents.js` - Document Management

```javascript
// Document CRUD operations
async function uploadDocument(files) { ... }
async function loadDocuments() { ... }
async function deleteDocument(id) { ... }
```

#### `js/chat.js` - Chat Functionality

```javascript
// Chat with agent
async function sendMessage(message) { ... }
function displayMessage(message, isUser) { ... }
```

#### `js/app.js` - Main Application

```javascript
// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadUserInfo();
    await loadDocuments();
    setupEventListeners();
});
```

## Benefits of Modular Architecture

### 1. **Separation of Concerns**
- Agent logic is independent of API
- API is independent of frontend
- Each layer has single responsibility

### 2. **Maintainability**
- Easy to locate code (auth in auth.py, chat in chat.py)
- Changes in one layer don't affect others
- Clear interfaces between layers

### 3. **Testability**
- Test agent independently
- Test API endpoints with mocked agent
- Test frontend with mocked API

### 4. **Reusability**
- Agent can be used in CLI, notebook, or different API
- Frontend can consume different backends
- API can use different agents

### 5. **Scalability**
- Easy to add new endpoints
- Easy to add new agent capabilities
- Easy to enhance frontend features

### 6. **Development**
- Multiple developers can work simultaneously
- Frontend devs don't need Python knowledge
- Backend devs focus on business logic

## Migration Plan

### Phase 1: Create Agent Module ✅
- [x] Create `src/agent/` directory structure
- [x] Extract `LegalDocumentAgent` class
- [x] Create `AgentConfig` dataclass
- [x] Extract agent instructions

### Phase 2: Create API Module
- [ ] Create `src/api/` directory structure
- [ ] Create `app.py` with FastAPI setup
- [ ] Create `models.py` with Pydantic models
- [ ] Create `dependencies.py` for shared resources
- [ ] Create endpoint modules:
  - [ ] `auth.py`
  - [ ] `documents.py`
  - [ ] `chat.py`
  - [ ] `health.py`

### Phase 3: Extract Frontend
- [ ] Create `src/frontend/` directory
- [ ] Extract HTML to `index.html`
- [ ] Extract CSS to `css/styles.css`
- [ ] Extract JavaScript to modular files:
  - [ ] `js/auth.js`
  - [ ] `js/documents.js`
  - [ ] `js/chat.js`
  - [ ] `js/app.js`

### Phase 4: Integration & Testing
- [ ] Update `main.py` as entry point
- [ ] Test all endpoints
- [ ] Test frontend integration
- [ ] Update Dockerfile if needed

### Phase 5: Documentation & Deployment
- [ ] Update README.md
- [ ] Create API documentation (OpenAPI)
- [ ] Update deployment scripts
- [ ] Deploy to Azure

## Backward Compatibility

The existing `src/main.py` will remain as the entry point but will import from the new modular structure:

```python
# src/main.py
from src.api.app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Documentation

FastAPI will automatically generate OpenAPI documentation at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc UI

##Future Enhancements

With the modular architecture, we can easily add:
- GraphQL API layer
- WebSocket support for real-time chat
- Multiple frontend frameworks (React, Vue)
- CLI interface using the agent directly
- Jupyter notebook integration
- Unit and integration tests
- API versioning (/api/v1/, /api/v2/)

## Conclusion

The modular architecture provides:
- ✅ Clean separation of concerns
- ✅ Better maintainability
- ✅ Improved testability
- ✅ Reusable components
- ✅ Scalable structure
- ✅ Professional codebase

This architecture follows industry best practices and makes the codebase production-ready for enterprise use.
