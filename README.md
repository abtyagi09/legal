# Legal Document Management AI Agent

An intelligent web application for legal document management with AI-powered search and analysis. Upload PDFs, Word documents, and images to automatically extract text and search through them using natural language queries powered by GPT-5.

## Features

- **Multi-Format Document Upload**: Supports PDF, DOCX, DOC, images (JPG, PNG, BMP, TIFF), and text files
- **Intelligent Text Extraction**: Azure Document Intelligence with managed identity authentication
- **AI-Powered Q&A**: GPT-5 model provides contextual answers from your documents
- **Semantic Search**: Azure AI Search indexes and retrieves relevant document content
- **Modern Web Interface**: Drag-and-drop upload, real-time chat, and formatted responses
- **Secure & Scalable**: Deployed on Azure Container Apps with managed identities
- **Production-Ready**: Infrastructure as Code with Bicep, containerized deployment

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  (FastAPI Web App with HTML/CSS/JavaScript Frontend)           │
│                                                                 │
│  ┌─────────────────┐              ┌───────────────────┐       │
│  │  Document Upload│              │   Chat Interface  │       │
│  │  (Drag & Drop)  │              │  (Q&A with AI)    │       │
│  └────────┬────────┘              └─────────┬─────────┘       │
└───────────┼──────────────────────────────────┼─────────────────┘
            │                                  │
            ▼                                  ▼
┌───────────────────────────────────────────────────────────────┐
│              AZURE CONTAINER APPS (FastAPI Backend)           │
│                                                                │
│  ┌──────────────────────┐      ┌─────────────────────────┐   │
│  │  Document Upload API │      │     Chat API            │   │
│  │  POST /api/upload    │      │  POST /api/chat         │   │
│  └──────────┬───────────┘      └───────────┬─────────────┘   │
│             │                               │                 │
│             │                               │                 │
│  ┌──────────▼────────────┐      ┌──────────▼──────────────┐  │
│  │  Text Extraction      │      │  Search & AI Response   │  │
│  │  - Read file bytes    │      │  - Query search index   │  │
│  │  - Call Doc Intel API │      │  - Build context        │  │
│  │  - Extract text       │      │  - Call GPT-5 model     │  │
│  └──────────┬────────────┘      │  - Format HTML response │  │
│             │                    └──────────┬──────────────┘  │
│             │                               │                 │
│  ┌──────────▼────────────┐                 │                 │
│  │  Index Document       │                 │                 │
│  │  - Create search doc  │                 │                 │
│  │  - Upload to index    │◄────────────────┘                 │
│  └───────────────────────┘                                   │
└───────────────────────────────────────────────────────────────┘
            │                                  │
            │                                  │
   ┌────────▼───────────┐          ┌──────────▼────────────┐
   │   Azure Document   │          │   Azure AI Search     │
   │   Intelligence     │          │                       │
   │                    │          │  ┌─────────────────┐  │
   │  - Managed Identity│          │  │ legal-documents │  │
   │  - OCR & Text      │          │  │     -index      │  │
   │    Extraction      │          │  │                 │  │
   │  - PDF, Images,    │          │  │ Fields:         │  │
   │    DOCX Support    │          │  │ - id            │  │
   └────────────────────┘          │  │ - title         │  │
                                   │  │ - content       │  │
                                   │  │ - file_name     │  │
                                   │  │ - upload_date   │  │
                                   │  └─────────────────┘  │
            ┌──────────────────────┴───────────────────────┘
            │
   ┌────────▼──────────┐
   │  Azure AI Foundry │
   │                   │
   │  - GPT-5 Model    │
   │  - Managed Identity│
   │  - Context-aware  │
   │    Responses      │
   └───────────────────┘
```

### User Flow

#### Document Upload Flow

```
1. User Interaction
   └─► User drags/selects file (PDF, DOCX, JPG, PNG, etc.)
       └─► Frontend validates file
           └─► POST to /api/upload with multipart/form-data

2. Backend Processing
   └─► FastAPI receives file
       └─► Read file bytes into memory
           └─► Detect file type (.pdf, .jpg, .docx, .txt)
               │
               ├─► If .txt: Decode UTF-8 text
               │
               └─► If PDF/Image/DOCX:
                   └─► Call Azure Document Intelligence
                       └─► Use Managed Identity (no API keys)
                           └─► prebuilt-read model
                               └─► Extract all text content
                                   └─► Get structured result

3. Text Extraction
   └─► Document Intelligence processes document
       └─► OCR for images
       └─► Text extraction for PDFs
       └─► Structure parsing for DOCX
           └─► Returns: Plain text content

4. Indexing
   └─► Create search document:
       {
         "id": "uuid",
         "title": "filename.pdf",
         "content": "extracted text...",
         "upload_date": "2026-02-04T19:00:00",
         "file_name": "filename.pdf"
       }
       └─► Upload to Azure AI Search index
           └─► Index for semantic search
               └─► Return success with preview

5. User Feedback
   └─► Display: "✓ Successfully indexed: filename.pdf"
       └─► Show document in documents list
```

#### Chat/Search Flow

```
1. User Query
   └─► User types: "What is the invoice amount?"
       └─► POST to /api/chat with { "message": "..." }

2. Semantic Search
   └─► Query Azure AI Search index
       └─► Search across all document content
           └─► Retrieve top 3 relevant results
               └─► Get: title, content (1500 chars), file_name

3. Context Building
   └─► For each search result:
       Document: invoice.pdf
       Content: INVOICE\nAmount: $9,990...
       └─► Combine into context text

4. AI Model Call
   └─► Call Azure AI Foundry (GPT-5)
       └─► System Message: "You are a helpful legal document assistant..."
       └─► User Message: 
           "Based on these documents:
            [context text]
            
            User question: What is the invoice amount?"
       └─► Model processes context
           └─► Generates answer with HTML formatting

5. Response Formatting
   └─► AI Answer: 
       "<div>The invoice amount is <strong>$9,990</strong>
        (subtotal $9,250 + 8% tax $740)</div>"
       └─► Add source documents:
           "📚 Sources: invoice.pdf"
       └─► Wrap in styled HTML container

6. Display Response
   └─► Frontend receives HTML response
       └─► Renders with innerHTML
           └─► Shows formatted answer with:
               - Styled content box
               - Preserved line breaks
               - Source attribution
               - Professional formatting
```

### Technology Stack

**Frontend**
- HTML5 with modern CSS (flexbox, grid)
- Vanilla JavaScript (async/await, fetch API)
- Drag-and-drop file upload
- Real-time chat interface

**Backend**
- **FastAPI**: Modern Python web framework
- **Python 3.11**: Async/await support
- **Uvicorn**: ASGI server
- **Azure SDK**: Identity, Search, AI, Document Intelligence

**Azure Services**
- **Azure Container Apps**: Managed containers with auto-scaling
- **Azure Document Intelligence**: OCR and text extraction (managed identity)
- **Azure AI Search**: Semantic search and indexing
- **Azure AI Foundry**: GPT-5 model deployment (managed identity)
- **Azure Container Registry**: Private container images
- **Azure Key Vault**: Secrets management
- **Application Insights**: Monitoring and logging

**Security**
- Managed identities (no API keys in code)
- Role-based access control (RBAC)
- HTTPS only
- Environment variable configuration

## Prerequisites

- Python 3.10+
- Azure Subscription
- Microsoft Foundry project with deployed GPT-5 model
- Azure AI Search service
- Azure Document Intelligence service
- Docker (for containerization)
- Azure CLI (for deployment)

## Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd legal
pip install -r requirements.txt
```

### 2. Configure Azure Services

Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your Azure endpoints and credentials.

### 3. Run Locally

```bash
python -m uvicorn src.main:app --reload
```

Visit http://localhost:8000 to access the application.

## Deployment

### Deploy to Azure Container Apps

1. **Build and push Docker image:**

```bash
docker build -t <your-registry>.azurecr.io/legal-agent:latest .
docker push <your-registry>.azurecr.io/legal-agent:latest
```

2. **Deploy infrastructure:**

```bash
cd infra
az deployment group create \
  --resource-group <your-rg> \
  --template-file main.bicep \
  --parameters main.parameters.json
```

3. **Configure managed identity permissions:**

```bash
# Grant Document Intelligence access
az role assignment create \
  --assignee <container-app-identity> \
  --role "Cognitive Services User" \
  --scope <doc-intel-resource-id>
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## API Endpoints

### Upload Document
```http
POST /api/upload
Content-Type: multipart/form-data

file: <binary-file>
```

**Response:**
```json
{
  "status": "success",
  "document_id": "uuid",
  "filename": "invoice.pdf",
  "extracted_length": 1234,
  "extraction_method": "document_intelligence",
  "preview": "INVOICE\nAmount: $9,990...",
  "message": "Document uploaded and indexed successfully"
}
```

### Chat Query
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What is the invoice amount?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "<div>...formatted HTML response...</div>",
  "session_id": "session-uuid"
}
```

### List Documents
```http
GET /api/documents
```

**Response:**
```json
[
  {
    "Title": "invoice.pdf",
    "ContentLength": 1234,
    "ContentPreview": "INVOICE\nAmount...",
    "UploadDate": "2026-02-04T19:00:00Z"
  }
]
```

## Configuration

### Environment Variables (Production)

```bash
FOUNDRY_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/project-name
FOUNDRY_MODEL_DEPLOYMENT=gpt-5-chat
SEARCH_ENDPOINT=https://your-search.search.windows.net
SEARCH_INDEX_NAME=legal-documents-index
SEARCH_API_KEY=<search-key>
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com/
KEYVAULT_ENDPOINT=https://your-keyvault.vault.azure.net/
APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>
```

### config.yaml (Local Development)

```yaml
foundry:
  project_endpoint: "https://..."
  model_deployment_name: "gpt-5-chat"

search:
  service_endpoint: "https://..."
  api_key: "..."
  index_name: "legal-documents-index"

document_intelligence:
  endpoint: "https://..."
  api_key: "..."
```

## Usage Examples

### Upload a Document

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@invoice.pdf"
```

### Search Documents

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all invoices from 2024"}'
```

### Extract Information

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the total amount due?"}'
```

## Project Structure

```
legal/
├── src/
│   ├── main.py                 # FastAPI application and endpoints
│   ├── config.py               # Configuration management
│   └── tools/
│       ├── document_intelligence_tool.py
│       └── search_tool.py
├── infra/                      # Bicep infrastructure templates
│   ├── main.bicep
│   ├── main.parameters.json
│   └── core/
│       ├── ai/                 # AI service modules
│       ├── host/               # Container Apps modules
│       ├── monitor/            # Monitoring modules
│       └── security/           # Security modules
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yaml         # Local development setup
├── requirements.txt            # Python dependencies
├── config.example.yaml         # Configuration template
└── README.md                   # This file
```

## Development

### Run with Docker Compose

```bash
docker-compose up
```

### Run Tests

```bash
pytest tests/
```

### View Logs

```bash
# Local
tail -f logs/agent.log

# Azure
az containerapp logs show \
  --name <app-name> \
  --resource-group <rg> \
  --follow
```
       └─► Add source documents:
           "📚 Sources: invoice.pdf"
       └─► Wrap in styled HTML container

6. Display Response
   └─► Frontend receives HTML response
       └─► Renders with innerHTML
           └─► Shows formatted answer with:
               - Styled content box
               - Preserved line breaks
               - Source attribution
               - Professional formatting
```

### Technology Stack

## Prerequisites

- Python 3.10+
- Azure Subscription
- Microsoft Foundry (formerly Azure AI Foundry) project with deployed model (recommended: GPT-5 or Claude Sonnet 4.5)
- Azure AI Search service
- Azure Document Intelligence service
- Docker (for containerization)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Note: The `--pre` flag is required while Agent Framework is in preview.

### 2. Configure Azure Services

Copy the example configuration and update with your Azure credentials:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your service endpoints and credentials.

### 3. Run the Agent

```bash
python src/main.py
```

## Configuration

The agent requires the following Azure services:

- **Microsoft Foundry Project**: For AI model deployment (GPT-5 recommended)
- **Azure AI Search**: For document indexing and semantic search
- **Azure Document Intelligence**: For document analysis and text extraction

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Usage Examples

### Search Legal Documents
```python
response = await agent.run(
    "Find all contracts related to real estate from 2024",
    thread=thread
)
```

### Extract Document Information
```python
response = await agent.run(
    "Extract key clauses from the NDA document",
    thread=thread
)
```

### Analyze Document Content
```python
response = await agent.run(
    "Summarize the main points of the merger agreement",
    thread=thread
)
```

## Project Structure

```
legal-doc-agent/
├── src/
│   ├── main.py                 # Main agent application
│   ├── tools/
│   │   ├── document_intelligence_tool.py
│   │   └── search_tool.py
│   └── config.py               # Configuration loader
├── config.yaml                 # Azure service configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yaml         # Local container orchestration
└── README.md                   # This file
```

## Deployment

### Local Development
```bash
python src/main.py
```

### Docker Container
```bash
docker build -t legal-doc-agent .
docker run -p 8000:8000 legal-doc-agent
```

### Azure (Recommended - One Command!)
```powershell
# Deploy everything to Azure with azd
azd up
```

See [AZD_DEPLOYMENT.md](AZD_DEPLOYMENT.md) for Azure Developer CLI deployment or [DEPLOYMENT.md](DEPLOYMENT.md) for manual deployment guide.

## Model Selection

This agent uses **GPT-5** from Microsoft Foundry for optimal performance:
- **Quality Index**: 0.9058 (top-tier reasoning)
- **Context Window**: 200K input / 100K output
- **Capabilities**: Advanced reasoning, multimodal support, excellent for complex legal analysis

Alternative models:
- **Claude Sonnet 4.5**: Excellent for coding and complex agents (0.921 quality)
- **GPT-4.1**: Strong instruction following and long-context understanding

## License

MIT

## Support

For issues and questions, please open a GitHub issue or contact your Azure support team.
