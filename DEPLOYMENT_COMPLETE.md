# 🎉 Mock Legal API Deployed!

## Deployment Summary

### Mock Legal API
- **URL**: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io
- **Status**: ✅ Running
- **Docs**: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/docs

### Your Legal Agent
- **URL**: https://ca-7alsezpsk27uq.wittymoss-05f49619.eastus2.azurecontainerapps.io
- **Status**: ✅ Running with Integration Actions

## Quick Test Examples

### 1. Get Legal Rates
```
User: "Call the API at https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/legal-rates and show me the rates"
```

### 2. Get Available Attorneys
```
User: "Fetch available attorneys from https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/attorneys?available_only=true"
```

### 3. Get Case Information
```
User: "Get details about case-001 from https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/cases/case-001"
```

### 4. Calculate Legal Fees
```
User: "Calculate the cost for Contract Review service for 5 hours using https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/calculate-estimate?service=Contract%20Review&hours=5"
```

### 5. Get Case Summary
```
User: "Call https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/case-summary and tell me about active cases"
```

### 6. Create New Case
```
User: "Create a new case via POST to https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/cases with title 'Smith v. Jones', type 'Contract Dispute', client 'John Smith', attorney_id 'att-001', and estimated_value 75000"
```

### 7. Multi-Step Workflow
```
User: "Get attorney att-001 from the legal API, then calculate their fees for 8 hours, and generate an invoice for client@example.com"
```

### 8. Integration Workflow
```
User: "Fetch the case summary, then send me an email with the statistics, and post a Teams notification about active cases"
```

## Available API Endpoints

### Attorneys
- `GET /attorneys` - List all attorneys
- `GET /attorneys?specialty=Corporate` - Filter by specialty
- `GET /attorneys?available_only=true` - Get available attorneys
- `GET /attorneys/{attorney_id}` - Get specific attorney

### Legal Rates
- `GET /legal-rates` - List all service rates
- `GET /legal-rates?service_type=contract` - Search rates
- `GET /legal-rates/{rate_id}` - Get specific rate
- `GET /calculate-estimate?service={service}&hours={hours}` - Calculate cost

### Cases
- `GET /cases` - List all cases
- `GET /cases?status=Active` - Filter by status
- `GET /cases?case_type=Contract` - Filter by type
- `GET /cases/{case_id}` - Get specific case
- `POST /cases` - Create new case
- `PUT /cases/{case_id}` - Update case

### Clients
- `GET /clients` - List all clients
- `GET /clients/{client_id}` - Get specific client

### Summary
- `GET /case-summary` - Get statistics
- `GET /` - API information

## Architecture

```
┌─────────────────────────────────────────┐
│   Your Legal Document Agent             │
│   ca-7alsezpsk27uq                      │
│   - Document search & analysis          │
│   - AI chat with RAG                    │
│   - Integration actions enabled         │
│   - Function calling support            │
└────────────┬────────────────────────────┘
             │
             │ Calls API via
             │ integration actions
             │
             ▼
┌─────────────────────────────────────────┐
│   Mock Legal Services API               │
│   ca-mock-legal-api                     │
│   - Attorney management                 │
│   - Legal rates & pricing               │
│   - Case management                     │
│   - Client information                  │
│   - Cost calculations                   │
└─────────────────────────────────────────┘
```

## Features Enabled

### Integration Actions ✅
1. **Call External API** - Make HTTP requests to any endpoint
2. **Send Email Notifications** - Email clients and team
3. **Send Teams Notifications** - Post to Teams channels
4. **Generate Invoices** - Create professional invoices
5. **Legal Case Management** - Create, read, update cases (via API)

### Function Calling ✅
The agent automatically detects when to use these actions based on user requests.

## Management Commands

### View Mock API Logs
```bash
az containerapp logs show --name ca-mock-legal-api --resource-group rg-legal-agent-dev --tail 50 --follow $false
```

### Restart Mock API
```bash
az containerapp revision restart --name ca-mock-legal-api --resource-group rg-legal-agent-dev --revision ca-mock-legal-api--0000001
```

### Update Mock API
```bash
docker build -f Dockerfile.mock-api -t cr7alsezpsk27uq.azurecr.io/mock-legal-api:latest .
docker push cr7alsezpsk27uq.azurecr.io/mock-legal-api:latest
az containerapp update --name ca-mock-legal-api --resource-group rg-legal-agent-dev --image cr7alsezpsk27uq.azurecr.io/mock-legal-api:latest
```

### Delete Mock API
```bash
az containerapp delete --name ca-mock-legal-api --resource-group rg-legal-agent-dev --yes
```

## Sample Mock Data

### Attorneys
- **Sarah Johnson** - Corporate Law ($500/hr) - Available
- **Michael Chen** - IP Law ($450/hr) - Available  
- **Emily Rodriguez** - Contract Law ($400/hr) - Unavailable

### Legal Services
- Contract Review: $350/hr
- Legal Consultation: $300/hr
- Document Drafting: $400/hr
- Court Representation: $600/hr
- Legal Research: $250/hr

### Cases
- **case-001**: ABC Corp v. XYZ Inc. (Contract Dispute, Active)
- **case-002**: Smith v. Johnson LLC (Employment, Settlement)
- **case-003**: TechStart Inc. v. Competitor Co. (IP, Discovery)

### Clients
- ABC Corporation (Business, 2 active cases)
- John Smith (Individual, 1 active case)

## Testing Checklist

- [ ] Mock API is accessible at the public URL
- [ ] Agent can call the mock API endpoints
- [ ] Agent parses JSON responses correctly
- [ ] Agent can create new cases via POST
- [ ] Agent can update cases via PUT
- [ ] Agent generates invoices using API data
- [ ] Multi-step workflows complete successfully
- [ ] Error handling works for API failures
- [ ] Teams/email notifications include API data

## Next Steps

1. ✅ Mock API deployed and running
2. ✅ Agent has access to the API
3. 🔄 Test integration scenarios
4. 📝 Add more mock endpoints as needed
5. 🔐 Consider adding API authentication
6. 📊 Monitor usage and performance
7. 🚀 Extend with real database if needed

## Cost Optimization

The mock API is configured with:
- **CPU**: 0.5 vCPU (minimal)
- **Memory**: 1 GB (sufficient for testing)
- **Replicas**: Min 1, Max 1 (always on for testing)

To reduce costs for non-production:
```bash
# Scale to zero when not in use
az containerapp update --name ca-mock-legal-api --resource-group rg-legal-agent-dev --min-replicas 0 --max-replicas 1
```

## Troubleshooting

### API Returns 502/503
```bash
az containerapp logs show --name ca-mock-legal-api --resource-group rg-legal-agent-dev --tail 100
```

### Agent Can't Connect
- Check API URL is correct
- Verify API is running: `curl https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/`
- Check network policies allow communication

### CORS Issues
Mock API has CORS enabled for all origins. If issues persist, check agent logs.

---

**🎉 You're all set! Your legal agent can now interact with the mock legal API for testing integration actions!**

Try the examples above to see the integration in action.
