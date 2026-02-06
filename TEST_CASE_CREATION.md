# Testing Case Creation with Agent

## ✅ Deployment Complete
Both services are now deployed and configured:
- **Agent URL**: https://ca-7alsezpsk27uq.wittymoss-05f49619.eastus2.azurecontainerapps.io
- **Mock API URL**: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io
- **Revision**: ca-7alsezpsk27uq--20260205163841

## 🔧 What Was Fixed
The agent now has the correct default API URL configured for all case management functions:
- `create_legal_case()` - Create new cases
- `update_case_status()` - Update case status
- `search_cases()` - Search for cases
- `get_case_details()` - Get case details
- `get_attorney_info()` - Get attorney information
- `get_legal_rates()` - Get service rates
- `calculate_legal_estimate()` - Calculate cost estimates

All functions now default to: `https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io`

## 🧪 Test the Case Creation

Navigate to the agent and try these commands:

### Test 1: Create Your Requested Case
```
Create a new case with title 'Smith v. Jones', type 'Contract Dispute', client 'John Smith', and attorney_id 'att-001'
```

### Test 2: Verify Case Was Created
```
Search for cases with status 'open'
```

### Test 3: Get Case Details
```
Show me the details for case case-001
```

### Test 4: Complete Workflow
```
1. Find available Corporate Law attorneys
2. Create a new case titled 'Tech Inc v. Startup LLC'
3. Type: 'Contract Dispute'
4. Client: 'Tech Inc'
5. Calculate the cost for 10 hours of Contract Review work
6. Generate an invoice for the client
```

### Test 5: Multi-Step Integration
```
Get attorney att-001 info, create a case for them with title 'Estate Planning - Johnson Family', type 'Estate Planning', client 'Johnson Family', then calculate fees for 5 hours of Legal Consultation and generate an invoice
```

## 📊 Expected Results

The agent should:
1. ✅ Call the `create_legal_case` function
2. ✅ Send POST request to mock API
3. ✅ Receive case data back (including case_number)
4. ✅ Display formatted response with case details

**Sample Response:**
```
Case created successfully: CASE-2026-0205-0001

Case Details:
- Case ID: case-004
- Case Number: CASE-2026-0205-0001
- Title: Smith v. Jones
- Type: Contract Dispute
- Client: John Smith
- Attorney: att-001 (Sarah Johnson)
- Status: open
- Priority: medium
- Created: 2026-02-05
```

## 🔍 Verification

If the agent creates the case successfully, you can verify directly with curl:
```bash
curl https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io/cases
```

This should show your newly created case in the list!

## 🎯 Next Steps

Once case creation works:
1. Test other integration actions (email notifications, invoices)
2. Try complex multi-step workflows
3. Combine multiple API calls in one request
4. Add more custom tools for legal-specific operations

## 🐛 Troubleshooting

If the agent doesn't execute the function call:
1. Check agent logs: `az containerapp logs show --name ca-7alsezpsk27uq --resource-group rg-legal-agent-dev --tail 100`
2. Verify function calling is enabled in config (should be by default)
3. Try being more explicit: "Use the create_legal_case function to..."
4. Check that the AI model supports function calling (gpt-4o-mini does)

## 📝 Notes

- The mock API will return case numbers in format: `CASE-YYYY-MMDD-####`
- Case IDs are auto-generated (e.g., `case-004`, `case-005`)
- Attorney att-001 is Sarah Johnson (Corporate Law, $500/hr)
- All created cases start with status "open" and priority "medium"
