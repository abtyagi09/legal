# Mock Legal API - Testing Guide

## Quick Start

### 1. Start the Mock API Server

```bash
# From the project root directory
python mock_legal_api.py
```

The API will be available at: `http://localhost:3001`

Interactive documentation: `http://localhost:3001/docs`

### 2. Test with Your Agent

Open your deployed agent at: https://ca-7alsezpsk27uq.wittymoss-05f49619.eastus2.azurecontainerapps.io

**Note:** Your Azure Container App cannot directly access `localhost:3001`. You have two options:

**Option A: Deploy Mock API to Azure** (recommended for testing)
```bash
# Build and push mock API
docker build -f Dockerfile.mock-api -t cr7alsezpsk27uq.azurecr.io/mock-legal-api:latest .
docker push cr7alsezpsk27uq.azurecr.io/mock-legal-api:latest

# Deploy to Container Apps
az containerapp create \
  --name ca-mock-legal-api \
  --resource-group rg-legal-agent-dev \
  --environment cae-7alsezpsk27uq \
  --image cr7alsezpsk27uq.azurecr.io/mock-legal-api:latest \
  --target-port 3001 \
  --ingress external
```

**Option B: Use Public Tunnel** (quick testing)
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 3001

# Use the ngrok URL in your agent
# Example: https://abc123.ngrok.io
```

## Available Endpoints

### 1. Attorneys

**Get all attorneys:**
```
GET http://localhost:3001/attorneys
```

**Filter by specialty:**
```
GET http://localhost:3001/attorneys?specialty=Corporate
```

**Get available attorneys only:**
```
GET http://localhost:3001/attorneys?available_only=true
```

**Get specific attorney:**
```
GET http://localhost:3001/attorneys/att-001
```

### 2. Legal Rates

**Get all service rates:**
```
GET http://localhost:3001/legal-rates
```

**Search for specific service:**
```
GET http://localhost:3001/legal-rates?service_type=contract
```

**Calculate estimate:**
```
GET http://localhost:3001/calculate-estimate?service=Contract%20Review&hours=3
```

### 3. Cases

**Get all cases:**
```
GET http://localhost:3001/cases
```

**Filter by status:**
```
GET http://localhost:3001/cases?status=Active
```

**Filter by type:**
```
GET http://localhost:3001/cases?case_type=Contract
```

**Get specific case:**
```
GET http://localhost:3001/cases/case-001
```

**Create new case:**
```
POST http://localhost:3001/cases
Body: {
  "title": "New Case v. Defendant",
  "type": "Contract Dispute",
  "client": "Test Client",
  "attorney_id": "att-001",
  "estimated_value": 50000
}
```

**Update case:**
```
PUT http://localhost:3001/cases/case-001
Body: {
  "status": "Settlement Negotiation",
  "next_hearing": "2026-03-15"
}
```

### 4. Clients

**Get all clients:**
```
GET http://localhost:3001/clients
```

**Get specific client:**
```
GET http://localhost:3001/clients/client-001
```

### 5. Summary Statistics

**Get case summary:**
```
GET http://localhost:3001/case-summary
```

## Test Scenarios with Your Agent

### Scenario 1: Get Legal Rates
```
User: "Call the API at http://localhost:3001/legal-rates and tell me the hourly rate for contract review"

Expected: Agent calls API, parses response, shows rate is $350/hour
```

### Scenario 2: Find Available Attorney
```
User: "Get available attorneys from http://localhost:3001/attorneys?available_only=true and recommend one for a contract case"

Expected: Agent lists available attorneys and recommends based on specialty
```

### Scenario 3: Get Case Information
```
User: "Fetch details about case case-001 from http://localhost:3001/cases/case-001"

Expected: Agent displays case details including attorney and status
```

### Scenario 4: Calculate Legal Fees
```
User: "Call http://localhost:3001/calculate-estimate?service=Contract Review&hours=5 and show me the total cost"

Expected: Agent calculates and shows $1,750 (5 hours × $350)
```

### Scenario 5: Get Attorney Info and Generate Invoice
```
User: "Get attorney details from http://localhost:3001/attorneys/att-001, then generate an invoice for 3 hours of their services to client@example.com"

Expected: 
1. Agent fetches attorney (Sarah Johnson, $500/hour)
2. Calculates 3 × $500 = $1,500
3. Generates invoice with correct details
```

### Scenario 6: Create Case via API
```
User: "Create a new case via http://localhost:3001/cases with title 'Tech Corp v. Startup LLC', type 'Intellectual Property', client 'Tech Corp', and attorney att-002"

Expected: Agent POSTs to API and returns new case ID
```

### Scenario 7: Multi-Step Workflow
```
User: "Get the case summary from http://localhost:3001/case-summary, then send me an email with the statistics"

Expected:
1. Agent calls case summary API
2. Formats statistics
3. Sends email notification with summary
```

### Scenario 8: Complex Integration
```
User: "Find active contract cases, get the attorney details for each, calculate billing if they worked 10 hours this week, and generate invoices"

Expected:
1. GET /cases?case_type=Contract&status=Active
2. For each case, GET /attorneys/{attorney_id}
3. Calculate hours × rate
4. Generate invoices for each
```

## Testing Checklist

- [ ] Mock API starts without errors
- [ ] Can access API at http://localhost:3001
- [ ] Interactive docs work at http://localhost:3001/docs
- [ ] Agent can call GET endpoints
- [ ] Agent can call POST endpoints
- [ ] Agent can parse JSON responses
- [ ] Agent handles API errors gracefully
- [ ] Multi-step workflows complete successfully
- [ ] Invoice generation uses API data correctly
- [ ] Email notifications include API data

## Mock Data Available

### Attorneys
- Sarah Johnson (Corporate Law, $500/hr)
- Michael Chen (IP Law, $450/hr)
- Emily Rodriguez (Contract Law, $400/hr)

### Legal Services
- Contract Review: $350/hr
- Legal Consultation: $300/hr
- Document Drafting: $400/hr
- Court Representation: $600/hr
- Legal Research: $250/hr

### Cases
- ABC Corp v. XYZ Inc. (Contract Dispute)
- Smith v. Johnson LLC (Employment)
- TechStart Inc. v. Competitor Co. (IP)

### Clients
- ABC Corporation (Business)
- John Smith (Individual)

## Troubleshooting

### API Won't Start
```bash
# Check if port 3001 is in use
netstat -ano | findstr :3001

# Kill process using port
taskkill /PID <PID> /F

# Or use different port
uvicorn mock_legal_api:app --port 3002
```

### Agent Can't Connect (Localhost Issue)
Container Apps can't reach localhost. Use one of:
1. Deploy mock API to Azure Container Apps
2. Use ngrok tunnel
3. Test locally with `python src/main.py`

### CORS Errors
The API has CORS enabled. If you still see errors:
```python
# In mock_legal_api.py, update CORS settings:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ca-7alsezpsk27uq.wittymoss-05f49619.eastus2.azurecontainerapps.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### JSON Parse Errors
Ensure URLs are properly encoded:
```
❌ Wrong: service=Contract Review
✅ Right: service=Contract%20Review
```

## Extending the Mock API

### Add New Endpoint

```python
@app.get("/court-dates")
def get_court_dates():
    return {
        "upcoming": [
            {"case_id": "case-001", "date": "2026-03-20", "type": "Hearing"},
            {"case_id": "case-003", "date": "2026-04-15", "type": "Discovery"}
        ]
    }
```

### Add New Service Rate

```python
LEGAL_RATES.append({
    "id": "rate-006",
    "service": "Mediation",
    "rate": 350,
    "unit": "hour",
    "description": "Mediation services for dispute resolution",
    "typical_duration": "4-8 hours"
})
```

### Add Authentication

```python
from fastapi import Header, HTTPException

def verify_token(x_api_key: str = Header()):
    if x_api_key != "secret-key-123":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/secure-data")
def get_secure_data(api_key: str = Depends(verify_token)):
    return {"data": "sensitive information"}
```

## Production Considerations

For production use:
1. Replace mock data with real database
2. Add authentication/authorization
3. Add rate limiting
4. Add request validation
5. Add logging and monitoring
6. Use environment variables for config
7. Add comprehensive error handling
8. Implement data persistence
9. Add API versioning
10. Document with OpenAPI specs

## Next Steps

1. Start the mock API
2. Test each endpoint in your browser or with curl
3. Try the test scenarios with your agent
4. Create custom test scenarios
5. Extend with additional endpoints
6. Deploy to Azure for permanent testing

Enjoy testing your integration actions! 🚀
