# Quick Start Guide - Legal Document Agent

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd c:\agents\legal
pip install -r requirements.txt --pre
```

> **Note**: The `--pre` flag is **required** while Agent Framework is in preview.

### Step 2: Setup Configuration

```bash
# Copy the example configuration
cp config.example.yaml config.yaml
```

Edit `config.yaml` and update these required fields:

```yaml
foundry:
  project_endpoint: "https://your-project.api.azureml.ms"
  model_deployment_name: "gpt-5"  # or your deployed model name

search:
  service_endpoint: "https://your-search-service.search.windows.net"
  api_key: "your-search-api-key"
  index_name: "legal-documents-index"

document_intelligence:
  endpoint: "https://your-doc-intel.cognitiveservices.azure.com/"
  api_key: "your-doc-intel-api-key"
```

### Step 3: Run the Agent

```bash
python src/main.py
```

That's it! You can now start chatting with your legal document agent.

## 💬 Example Queries

Try these queries to get started:

- "Search for all contracts from 2024"
- "Find NDAs with confidentiality clauses"
- "Extract key terms from document ID: doc-12345"
- "Summarize the merger agreement"
- "List all documents related to real estate"

## 🔧 Need Azure Services?

If you don't have the Azure services set up yet:

1. **Microsoft Foundry**: Visit [ai.azure.com](https://ai.azure.com) to create a project and deploy a model
2. **Azure AI Search**: Follow the [DEPLOYMENT.md](DEPLOYMENT.md#2-create-azure-ai-search-service) guide
3. **Document Intelligence**: Follow the [DEPLOYMENT.md](DEPLOYMENT.md#3-create-azure-document-intelligence-service) guide

## 📚 More Information

- [Full README](README.md) - Complete feature documentation
- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [Model Selection](README.md#model-selection) - Choosing the right AI model

## ⚠️ Important Notes

- Ensure your Azure AI Search index has legal documents indexed
- Use **GPT-5** or **Claude Sonnet 4.5** for best results
- The `--pre` flag is required for pip install (Agent Framework is in preview)
- Keep your API keys secure and never commit them to version control

## 🆘 Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'agent_framework'`  
**Solution**: Install with `--pre` flag: `pip install -r requirements.txt --pre`

**Issue**: `Configuration file not found`  
**Solution**: Copy `config.example.yaml` to `config.yaml` and update values

**Issue**: `Authentication failed`  
**Solution**: Verify your API keys in `config.yaml` are correct

For more help, see [DEPLOYMENT.md#troubleshooting](DEPLOYMENT.md#troubleshooting).
