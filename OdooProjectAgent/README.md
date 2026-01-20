# OdooProjectAgent - Logic Apps Integration Guide

## 📨 Request Schema (from Logic Apps)

When Logic Apps receives an email, it should send this JSON to the Azure Function:

```json
{
  "from": "luc@dkm-customs.com",
  "to": "projects@dkm-customs.com",
  "subject": "New Project: ACME Invoice Processing",
  "body": "Full email body text here...",
  "bodyPreview": "First 100 characters preview...",
  "hasAttachments": true,
  "attachments": [
    {
      "name": "invoice_001.pdf",
      "contentType": "application/pdf",
      "size": 12345
    },
    {
      "name": "spec_document.xlsx",
      "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size": 54321
    }
  ],
  "receivedDateTime": "2026-01-20T15:00:00Z",
  "importance": "high"
}
```

## 🔧 Logic App Configuration

### Trigger: "When a new email arrives (V3)"
- **Folder**: Inbox
- **Include Attachments**: Yes
- **Importance**: Any

### Condition: Check if email is from Luc
```
@equals(triggerOutputs()?['body/from'], 'luc@dkm-customs.com')
```

### Action: HTTP - POST to Azure Function
**URL**: `https://your-function-app.azurewebsites.net/api/OdooProjectAgent`

**Method**: POST

**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**Body**:
```json
{
  "from": "@{triggerOutputs()?['body/from']}",
  "to": "@{triggerOutputs()?['body/to']}",
  "subject": "@{triggerOutputs()?['body/subject']}",
  "body": "@{triggerOutputs()?['body/body']}",
  "bodyPreview": "@{triggerOutputs()?['body/bodyPreview']}",
  "hasAttachments": "@{triggerOutputs()?['body/hasAttachments']}",
  "attachments": "@{triggerOutputs()?['body/attachments']}",
  "receivedDateTime": "@{triggerOutputs()?['body/receivedDateTime']}",
  "importance": "@{triggerOutputs()?['body/importance']}"
}
```

## ✅ What the AI Agent Does

1. **Receives** rich email metadata from Logic Apps
2. **Enriches** the context with sender, attachments, timestamps
3. **Parses** using AI to extract:
   - Client name
   - Flow type
   - Required tools (Logic Apps, Azure Functions, AI services)
   - Input/output formats
4. **Validates** the extracted data
5. **Creates** a deterministic Odoo project with:
   - Consistent naming: `{Client} – {Flow Type}`
   - Structured description
   - Email metadata for traceability
6. **Returns** project ID and confirmation

## 📋 Simplified Schema (Backward Compatible)

The function also supports a simple schema for testing:

```json
{
  "email_body": "Client ACME sends PDFs by email. Output Excel.",
  "subject": "New ACME Flow"
}
```

## 🎯 AI Intelligence Features

The AI agent automatically:
- ✅ Detects client names from email content
- ✅ Identifies Azure services mentioned (Logic Apps, Functions, AI Document Intelligence)
- ✅ Recognizes file types from attachments
- ✅ Determines input source (Email, HTTP, Blob)
- ✅ Extracts output format requirements
- ✅ Normalizes variations ("Excel file" → "Excel", "PDF documents" → "PDF")

## 🧪 Test Locally

```powershell
$body = @{
    from = "luc@dkm-customs.com"
    to = "projects@dkm-customs.com"
    subject = "New Project: ACME Invoice Processing"
    body = "Hi Team, We need a flow for ACME. They send PDFs by email. Extract with Azure AI Document Intelligence. Process with Logic App 'la-acme-processor'. Output Excel."
    hasAttachments = $true
    attachments = @(
        @{
            name = "invoice.pdf"
            contentType = "application/pdf"
            size = 12345
        }
    )
    receivedDateTime = "2026-01-20T15:00:00Z"
    importance = "high"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:7073/api/OdooProjectAgent" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

## 📊 Success Response

```json
{
  "success": true,
  "project_id": 42,
  "project_name": "ACME – Invoice Processing",
  "flow_fingerprint": {
    "client": "ACME",
    "flow_type": "Invoice Processing",
    "source": "Email",
    "output_format": "Excel",
    "attachments": ["PDF"]
  },
  "email_metadata": {
    "from": "luc@dkm-customs.com",
    "subject": "New Project: ACME Invoice Processing",
    "received": "2026-01-20T15:00:00Z",
    "attachment_count": 1
  }
}
```

## 🚀 Deployment

1. Deploy to Azure Functions
2. Configure Logic App with the function URL
3. Add function key to Logic App HTTP action
4. Test with a real email from Luc
5. Check Odoo for the created project

## 🔐 Security

- Function uses Azure Key Vault for OpenAI API key
- Odoo credentials in environment variables
- Logic App uses managed identity
- Function key authentication required
