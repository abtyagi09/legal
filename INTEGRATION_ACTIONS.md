# Integration Actions Guide

This guide explains how to use the integration actions (external API calls, notifications, and invoice generation) in your Legal Document Agent.

## Overview

The agent now supports **function calling** (also called tool use), which means it can automatically decide when to use integration actions based on user requests.

## Available Actions

### 1. Call External API

Call any REST API to fetch or send data.

**Example Requests:**
- "Call the weather API to get today's forecast"
- "Fetch data from https://api.example.com/legal-rates"
- "POST this contract data to our CRM system"

**Function Details:**
```python
call_external_api(
    url: str,              # API endpoint
    method: str = "GET",   # HTTP method
    headers: dict = None,  # Optional headers
    data: dict = None,     # Optional body data
    params: dict = None    # Optional query params
)
```

**Example:**
```
User: "Call the legal rates API at https://api.legalrates.com/v1/rates?state=CA"

Agent will automatically:
1. Recognize the need to call an external API
2. Execute call_external_api(url="https://api.legalrates.com/v1/rates", params={"state": "CA"})
3. Return the formatted results
```

### 2. Send Email Notification

Send email notifications to clients or team members.

**Example Requests:**
- "Send an email to john@example.com about the new contract"
- "Notify client@company.com that their document is ready"
- "Email me a summary of today's document uploads"

**Function Details:**
```python
send_email_notification(
    recipient: str,     # Email address
    subject: str,       # Email subject
    body: str,         # Email body (HTML supported)
    cc: str = None     # Optional CC recipients
)
```

**Integration Required:**
To actually send emails, integrate with your email service in `src/tools/integration_actions.py`:
- Azure Communication Services
- SendGrid
- AWS SES
- Office 365

**Example:**
```
User: "Send an email to client@example.com with subject 'Contract Ready' telling them their contract review is complete"

Agent will:
1. Generate appropriate email content
2. Call send_email_notification with the details
3. Confirm the email was sent
```

### 3. Send Teams Notification

Send notifications to Microsoft Teams channels via webhook.

**Example Requests:**
- "Notify the legal team in Teams that the contract needs review"
- "Send a Teams message about the new document upload"
- "Post to Teams channel about urgent case update"

**Function Details:**
```python
send_teams_notification(
    webhook_url: str,   # Teams incoming webhook URL
    title: str,         # Notification title
    message: str,       # Message content (Markdown)
    color: str = "0078D4"  # Theme color (hex)
)
```

**Setup:**
1. Go to your Teams channel → Connectors → Incoming Webhook
2. Create webhook and copy the URL
3. Provide the webhook URL in your request or store it as environment variable

**Example:**
```
User: "Send a Teams notification to https://outlook.office.com/webhook/xxx about the new contract upload"

Agent will:
1. Format the message appropriately
2. Send to the Teams webhook
3. Confirm delivery
```

### 4. Generate Invoice

Generate professional invoices for legal services.

**Example Requests:**
- "Generate an invoice for John Smith at john@example.com for legal consultation"
- "Create an invoice for ABC Corp with 5 hours of contract review at $300/hour"
- "Bill client@company.com for document review services"

**Function Details:**
```python
generate_invoice(
    client_name: str,           # Client name
    client_email: str,          # Client email
    invoice_number: str = None, # Auto-generated if not provided
    items: list = [],          # Line items
    due_date: str = None,      # ISO format date
    notes: str = None          # Payment terms/notes
)
```

**Item Format:**
```python
{
    "description": "Legal consultation",
    "amount": 300.00,
    "quantity": 2
}
```

**Example:**
```
User: "Generate an invoice for Jane Doe (jane@example.com) for 3 hours of contract review at $350 per hour"

Agent will:
1. Parse the billing details
2. Calculate totals (3 × $350 = $1,050)
3. Generate invoice with unique number
4. Return formatted HTML invoice
5. Optionally email it to the client
```

## How Function Calling Works

### Automatic Detection

The agent automatically detects when to use these actions based on user intent:

```
User: "Send an email to client@example.com and generate an invoice for them"

Agent Response:
1. 🔧 Executing actions...
2. ✓ Action Completed: send_email_notification
   Email notification queued successfully
3. ✓ Action Completed: generate_invoice
   Invoice INV-20260205-153045 generated successfully
   [View Invoice INV-20260205-153045 ($1,050.00)]
```

### Enabling/Disabling Function Calling

In `src/agent/config.py`:

```python
enable_function_calling: bool = True  # Set to False to disable
```

Or via environment variable:
```bash
ENABLE_FUNCTION_CALLING=false
```

## Integration Setup

### Email Integration (Azure Communication Services)

```python
# In src/tools/integration_actions.py, update send_email_notification:

from azure.communication.email import EmailClient

email_client = EmailClient.from_connection_string(
    os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
)

message = {
    "senderAddress": "noreply@yourdomain.com",
    "recipients": {"to": [{"address": recipient}]},
    "content": {"subject": subject, "html": body}
}

poller = email_client.begin_send(message)
result = poller.result()
```

### Teams Webhook Setup

1. In Teams → Channel → Connectors → Incoming Webhook
2. Name it "Legal Agent Notifications"
3. Copy webhook URL
4. Store as environment variable: `TEAMS_WEBHOOK_URL`

### Invoice Storage

To save invoices to Azure Blob Storage:

```python
from azure.storage.blob.aio import BlobServiceClient

blob_service = BlobServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)

container_client = blob_service.get_container_client("invoices")
blob_client = container_client.get_blob_client(f"{invoice_number}.html")
await blob_client.upload_blob(invoice_html)
```

## Testing Integration Actions

### Test API Call

```
User: "Call the API at https://jsonplaceholder.typicode.com/posts/1"
```

### Test Email (Dry Run)

```
User: "Send a test email to test@example.com with subject 'Test' and body 'This is a test'"
```

### Test Invoice Generation

```
User: "Create a test invoice for Test Client (test@example.com) with one item: 'Legal Services' for $500"
```

## Security Considerations

1. **API Keys**: Store sensitive keys in Azure Key Vault
2. **Webhook URLs**: Validate webhook URLs before use
3. **Email Validation**: Validate email addresses before sending
4. **Rate Limiting**: Implement rate limiting for external calls
5. **Audit Logging**: Log all integration action executions

## Customization

### Adding New Actions

1. Add action method to `IntegrationActions` class
2. Add function definition to `INTEGRATION_TOOLS` array
3. Add case in `_execute_tool_call` method
4. Test the new action

### Example: Add SMS Notification

```python
async def send_sms_notification(self, phone: str, message: str):
    """Send SMS notification"""
    # Implementation here
    pass

# Add to INTEGRATION_TOOLS:
{
    "type": "function",
    "function": {
        "name": "send_sms_notification",
        "description": "Send SMS notification to a phone number",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Phone number"},
                "message": {"type": "string", "description": "SMS message"}
            },
            "required": ["phone", "message"]
        }
    }
}
```

## Troubleshooting

### Function Not Executing

1. Check `enable_function_calling = True` in config
2. Verify tool definitions are loaded
3. Check agent logs for tool call attempts
4. Ensure request clearly indicates need for action

### API Call Failures

1. Check network connectivity
2. Verify API endpoint URL
3. Check authentication headers
4. Review timeout settings (default: 30s)

### Email Not Sending

1. Verify email service integration
2. Check email service credentials
3. Validate recipient email format
4. Review email service quotas/limits

## Best Practices

1. **Clear Instructions**: Be specific about what action to perform
2. **Include Details**: Provide all necessary parameters
3. **Test First**: Test with safe endpoints before production
4. **Monitor Logs**: Check logs for execution details
5. **Handle Errors**: Implement error handling for failures
6. **Rate Limits**: Be aware of external service limits
7. **Async Operations**: Use async methods for better performance

## Examples

### Complete Workflow Example

```
User: "Search for contract with ABC Corp, then generate an invoice for $5000 and email it to billing@abccorp.com"

Agent will:
1. Search documents for "ABC Corp contract"
2. Display search results
3. Generate invoice with appropriate details
4. Send email with invoice attached
5. Confirm all actions completed
```

### Multi-Step Integration

```
User: "Check the legal rates API, then send me an email with the current rates, and notify the team in Teams"

Agent will:
1. Call external API to fetch rates
2. Format rates data
3. Send email notification with rates
4. Post Teams notification with summary
5. Confirm all steps completed
```

## Next Steps

1. Configure your email service integration
2. Set up Teams webhooks for notifications
3. Test each integration action
4. Customize invoice template
5. Add additional actions as needed
6. Deploy and monitor usage

For questions or issues, check the logs or raise an issue in the repository.
