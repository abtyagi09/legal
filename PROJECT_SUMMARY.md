# Legal Document Management AI Agent - Project Summary

## 📋 Overview

A production-ready AI agent application built with Microsoft Agent Framework that provides intelligent document search and management capabilities for legal professionals.

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LEGAL DOCUMENT AGENT                        │
│                     (Azure Container Apps)                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Legal Document Agent (Python)                    │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │         Microsoft Agent Framework (agent-framework)           │ │
│  │                                                               │ │
│  │  ┌──────────────────────────────────────────────────────┐   │ │
│  │  │  Agent Core                                          │   │ │
│  │  │  • Multi-turn conversation with Thread persistence  │   │ │
│  │  │  • Streaming responses                               │   │ │
│  │  │  • Tool orchestration & function calling            │   │ │
│  │  │  • Context management                                │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  │                                                               │ │
│  │  ┌──────────────────┐  ┌────────────────────────────────┐   │ │
│  │  │  AI Model        │  │  Tools                         │   │ │
│  │  │                  │  │  1. Document Intelligence Tool │   │ │
│  │  │  GPT-5 or        │  │  2. Search Documents Tool      │   │ │
│  │  │  Claude Sonnet   │  │  3. Get Document By ID Tool    │   │ │
│  │  │  4.5             │  │                                │   │ │
│  │  └──────────────────┘  └────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                    │                           │
                    │                           │
        ┌───────────▼──────────┐    ┌──────────▼────────────┐
        │  Microsoft Foundry   │    │   Azure AI Services   │
        │  (AI Foundry)        │    │                       │
        │                      │    │  ┌─────────────────┐  │
        │  ┌────────────────┐ │    │  │ Azure AI Search │  │
        │  │  GPT-5 Model   │ │    │  │                 │  │
        │  │  Deployment    │ │    │  │ • Semantic      │  │
        │  │                │ │    │  │   Search        │  │
        │  │  200K context  │ │    │  │ • Vector Search │  │
        │  │  Streaming     │ │    │  │ • Filters       │  │
        │  └────────────────┘ │    │  │ • Index: legal- │  │
        └─────────────────────┘    │  │   documents     │  │
                                   │  └─────────────────┘  │
                                   │                       │
                                   │  ┌─────────────────┐  │
                                   │  │   Document      │  │
                                   │  │   Intelligence  │  │
                                   │  │                 │  │
                                   │  │ • Text Extract  │  │
                                   │  │ • Table Extract │  │
                                   │  │ • Key-Value     │  │
                                   │  │   Pairs         │  │
                                   │  │ • Layout        │  │
                                   │  │   Analysis      │  │
                                   │  └─────────────────┘  │
                                   └───────────────────────┘
```

### Data Flow

```
┌──────────┐
│  User    │
│  Query   │
└────┬─────┘
     │
     │ "Find all contracts from 2024"
     ▼
┌─────────────────────────────────┐
│  Legal Document Agent           │
│  • Receives query               │
│  • Analyzes intent              │
│  • Selects appropriate tool(s)  │
└────┬────────────────────┬───────┘
     │                    │
     │ Tool 1: Search     │ Tool 2: Document Intelligence
     │                    │
     ▼                    ▼
┌────────────────┐   ┌─────────────────────────┐
│ Azure AI       │   │ Azure Document          │
│ Search         │   │ Intelligence            │
│                │   │                         │
│ • Execute      │   │ • Analyze document      │
│   semantic     │   │ • Extract text/tables   │
│   search       │   │ • Return structured     │
│ • Apply        │   │   data                  │
│   filters      │   │                         │
│ • Return top   │   │                         │
│   results      │   │                         │
└────┬───────────┘   └─────────┬───────────────┘
     │                         │
     │ Results                 │ Extracted Content
     │                         │
     └──────────┬──────────────┘
                │
                ▼
     ┌──────────────────────┐
     │  GPT-5 Model         │
     │  • Synthesize info   │
     │  • Generate response │
     │  • Format output     │
     └──────────┬───────────┘
                │
                │ Streaming Response
                ▼
          ┌──────────┐
          │   User   │
          │ Response │
          └──────────┘
```

### Component Details

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    AGENT COMPONENTS                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────────────────────────────────────────────────────┐
│ 1. Configuration Layer (config.py)                             │
│    • YAML-based configuration                                  │
│    • Service endpoint management                               │
│    • Credential validation                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 2. Tool Layer (src/tools/)                                     │
│                                                                 │
│    ┌──────────────────────────────────────┐                   │
│    │ Document Intelligence Tool           │                   │
│    │ • analyze_document()                 │                   │
│    │   - Extracts text, tables           │                   │
│    │   - Key-value pairs                 │                   │
│    │   - Document structure              │                   │
│    └──────────────────────────────────────┘                   │
│                                                                 │
│    ┌──────────────────────────────────────┐                   │
│    │ Search Tool                          │                   │
│    │ • search_documents()                 │                   │
│    │   - Semantic search                  │                   │
│    │   - Filters (type, date)            │                   │
│    │ • get_document_by_id()              │                   │
│    │   - Retrieve full document          │                   │
│    └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 3. Agent Layer (main.py)                                       │
│    • AzureAIClient initialization                              │
│    • Agent creation with tools                                 │
│    • Thread management for conversations                       │
│    • Streaming response handling                               │
│    • Interactive CLI mode                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 4. Deployment Layer                                            │
│    • Docker containerization                                   │
│    • Azure Container Apps                                      │
│    • Managed Identity                                          │
│    • Auto-scaling                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Subscription                       │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Resource Group: legal-agent-rg                        │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────┐          │   │
│  │  │  Azure Container Apps Environment       │          │   │
│  │  │                                          │          │   │
│  │  │  ┌────────────────────────────────────┐ │          │   │
│  │  │  │  Container App: legal-agent        │ │          │   │
│  │  │  │  • Image: ACR/legal-doc-agent     │ │          │   │
│  │  │  │  • CPU: 2.0, Memory: 4Gi          │ │          │   │
│  │  │  │  • Min replicas: 1, Max: 5        │ │          │   │
│  │  │  │  • Ingress: External (HTTPS)      │ │          │   │
│  │  │  │  • Managed Identity: Enabled      │ │          │   │
│  │  │  └────────────────────────────────────┘ │          │   │
│  │  └─────────────────────────────────────────┘          │   │
│  │                                                         │   │
│  │  ┌──────────────────┐  ┌──────────────────┐          │   │
│  │  │ Azure AI Search  │  │    Document      │          │   │
│  │  │                  │  │  Intelligence    │          │   │
│  │  │ • Standard tier  │  │                  │          │   │
│  │  │ • Semantic       │  │  • S0 tier       │          │   │
│  │  │   config         │  │  • prebuilt-doc  │          │   │
│  │  └──────────────────┘  └──────────────────┘          │   │
│  │                                                         │   │
│  │  ┌──────────────────┐  ┌──────────────────┐          │   │
│  │  │ Container        │  │  Key Vault       │          │   │
│  │  │ Registry (ACR)   │  │                  │          │   │
│  │  │                  │  │  • API Keys      │          │   │
│  │  │ • legal-agent    │  │  • Secrets       │          │   │
│  │  │   images         │  │  • Certificates  │          │   │
│  │  └──────────────────┘  └──────────────────┘          │   │
│  │                                                         │   │
│  │  ┌──────────────────┐  ┌──────────────────┐          │   │
│  │  │ Application      │  │  Log Analytics   │          │   │
│  │  │ Insights         │  │  Workspace       │          │   │
│  │  │                  │  │                  │          │   │
│  │  │ • Metrics        │  │  • Container     │          │   │
│  │  │ • Traces         │  │    logs          │          │   │
│  │  │ • Alerts         │  │  • Query logs    │          │   │
│  │  └──────────────────┘  └──────────────────┘          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  External: Microsoft Foundry Project                   │   │
│  │  • GPT-5 Model Deployment                              │   │
│  │  • Project endpoint: https://*.api.azureml.ms         │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Key Features

1. **Semantic Document Search**
   - Natural language queries across legal documents
   - Filter by document type, date, and metadata
   - Retrieve specific documents by ID

2. **Document Analysis**
   - Extract text, tables, and key-value pairs
   - Analyze document structure and layout
   - Support for PDFs, images, and scanned documents

3. **AI-Powered Insights**
   - Summarize complex legal documents
   - Identify key clauses and obligations
   - Answer questions about document content

4. **Production-Ready**
   - Containerized with Docker
   - Deployable to Azure Container Apps
   - Managed identity support
   - Comprehensive logging and monitoring

## 🔧 Technology Stack

- **Agent Framework**: Microsoft Agent Framework (Python)
- **AI Model**: GPT-5 (Microsoft Foundry)
- **Search**: Azure AI Search with semantic search
- **Document Processing**: Azure Document Intelligence
- **Deployment**: Docker + Azure Container Apps
- **Authentication**: Azure Managed Identity / API Keys

## 📁 Project Structure

```
c:\agents\legal/
├── src/
│   ├── main.py                    # Main agent application
│   ├── config.py                  # Configuration loader
│   └── tools/
│       ├── __init__.py
│       ├── document_intelligence_tool.py
│       └── search_tool.py
├── config.example.yaml            # Configuration template
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container definition
├── docker-compose.yaml            # Local orchestration
├── .gitignore                     # Git ignore rules
├── .env.example                   # Environment variables template
├── README.md                      # Main documentation
├── DEPLOYMENT.md                  # Deployment guide
└── QUICKSTART.md                  # Quick start guide
```

## 🚀 Quick Commands

### Azure Deployment (Recommended)
```bash
# One-command deployment to Azure
azd up

# Or step-by-step
azd provision  # Create Azure resources
azd deploy     # Deploy application
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt --pre

# Run agent
python src/main.py
```

### Docker
```bash
# Build
docker build -t legal-document-agent .

# Run with Docker Compose
docker-compose up -d
```

### Manual Azure Deployment
```bash
# Build and push to ACR
az acr build --registry <acr-name> --image legal-document-agent:latest .

# Deploy to Container Apps
az containerapp create --name legal-agent --image <acr-name>.azurecr.io/legal-document-agent:latest ...
```

## 🎨 Model Selection

**Primary Recommendation: GPT-5**
- Quality Index: 0.9058 (excellent reasoning)
- Context: 200K input / 100K output
- Best for: Complex legal analysis, multi-step reasoning

**Alternative: Claude Sonnet 4.5**
- Quality Index: 0.921 (top-tier)
- Context: 200K input / 64K output
- Best for: Coding-heavy tasks, complex agents

## 🔐 Security Features

- Managed Identity support (no hard-coded keys)
- Azure Key Vault integration for secrets
- Non-root container user
- Network isolation with VNet
- Rate limiting
- Comprehensive audit logging

## 📊 Configuration

Required Azure services:
1. **Microsoft Foundry** - AI model deployment
2. **Azure AI Search** - Document indexing and search
3. **Azure Document Intelligence** - Document analysis
4. **Azure Container Apps** - Hosting (optional)
5. **Azure Key Vault** - Secret management (recommended)

## 🎯 Use Cases

- Contract analysis and review
- Legal document search and retrieval
- NDA and agreement processing
- Case file management
- Due diligence document review
- Compliance documentation search

## 📈 Scaling

- **Horizontal**: Auto-scale based on request volume
- **Vertical**: Adjust CPU/memory per container
- **Cost Optimization**: Scale to zero during off-hours
- **Performance**: Streaming responses for better UX

## 🧪 Testing

Example queries to test:
```
- "Find all real estate contracts from 2024"
- "Extract key clauses from the NDA"
- "Search for documents mentioning ABC Corporation"
- "Summarize the merger agreement document"
```

## 📚 Documentation

- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - One-command Azure deployment
- **[AZD_DEPLOYMENT.md](AZD_DEPLOYMENT.md)** - Complete azd deployment guide
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute local setup
- **[README.md](README.md)** - Features, setup, usage examples
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Manual production deployment guide

## 🔄 Next Steps

1. **Setup Azure Services** - Create required Azure resources
2. **Index Documents** - Upload legal documents to Azure AI Search
3. **Configure Agent** - Update config.yaml with credentials
4. **Test Locally** - Run and test with sample queries
5. **Deploy to Azure** - Deploy to Container Apps for production
6. **Monitor** - Set up Application Insights for monitoring
7. **Customize** - Adjust agent instructions for your workflows

## 🏆 Best Practices Applied

✅ Microsoft Agent Framework for modern agent development  
✅ Streaming responses for better UX  
✅ Multi-turn conversations with thread persistence  
✅ Tool-based architecture for extensibility  
✅ Semantic search for intelligent document retrieval  
✅ Container-based deployment for scalability  
✅ Managed identity for secure authentication  
✅ Comprehensive error handling and logging  
✅ Production-ready Docker configuration  
✅ Documentation for all deployment scenarios  

## 🤝 Contributing

To extend this agent:

1. **Add new tools** - Create new tool files in `src/tools/`
2. **Customize prompts** - Update agent instructions in `config.yaml`
3. **Add API endpoints** - Extend `main.py` with FastAPI routes
4. **Enhance search** - Add more filters and query capabilities
5. **Integrate services** - Connect to additional Azure services

## 📞 Support

- **Microsoft Agent Framework**: [GitHub](https://github.com/microsoft/agent-framework)
- **Azure Documentation**: [Microsoft Learn](https://learn.microsoft.com/azure)
- **AI Toolkit**: VS Code extension for model management

---

**Built with ❤️ using Microsoft Agent Framework and Azure AI Services**
