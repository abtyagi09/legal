# Legal Document Management AI Agent

An AI-powered agent for intelligent legal document search and management, built with Microsoft Agent Framework, Azure AI Search, and Azure Document Intelligence.

## Features

- **Intelligent Document Search**: Leverage Azure AI Search for semantic search across legal documents
- **Document Processing**: Use Azure Document Intelligence to extract text, tables, and metadata from legal documents
- **AI-Driven Insights**: Powered by Microsoft Foundry AI models for natural language understanding
- **Container-Ready**: Deployable to Azure Container Apps for scalable production use
- **Legal-Optimized**: Tailored for legal document workflows including contracts, briefs, and case files

## Architecture

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   Legal Document Agent      │
│  (Agent Framework)          │
├─────────────────────────────┤
│ - GPT-5 Model               │
│ - Document Intelligence Tool│
│ - AI Search Tool            │
└──────┬──────────────┬───────┘
       │              │
       ▼              ▼
┌──────────────┐  ┌──────────────────┐
│   Document   │  │  Azure AI Search │
│ Intelligence │  │   Knowledge Base │
└──────────────┘  └──────────────────┘
```

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
