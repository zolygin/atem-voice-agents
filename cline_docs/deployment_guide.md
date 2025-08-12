# Deployment Guide: Atem Voice Agents with Supabase RAG

This guide provides a step-by-step approach to deploy the working voice agent application with Supabase RAG integration to Azure Container Apps.

## Prerequisites

- Azure subscription with billing enabled (required for phone numbers)
- Azure CLI installed and authenticated
- Docker installed locally
- Python 3.11+ with pip
- Supabase account with configured database and RPC functions

## Current Working State

Key features confirmed working:
- ✅ Voice agent interaction via WebRTC
- ✅ Supabase RAG for knowledge retrieval
- ✅ Proper WebSocket connection cleanup (no hanging issues)
- ✅ Azure OpenAI integration
- ✅ Azure Communication Services integration

## Step-by-Step Deployment Process

### 1. Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zolygin/atem-voice-agents
   cd atem-voice-agents
   ```

2. **Install dependencies:**
   ```bash
   pip install -r src/app/requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory with:
   ```bash
   SUPABASE_URL="your-supabase-url"
   SUPABASE_SERVICE_ROLE_KEY="your-supabase-service-key"
   AZURE_OPENAI_ENDPOINT="your-azure-openai-endpoint"
   AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME="gpt-4o-realtime-preview"
   AZURE_OPENAI_API_KEY="your-azure-openai-key"
   AZURE_OPENAI_VERSION="2024-10-01-preview"
   OPENAI_API_TYPE="azure"
   ACS_CONNECTION_STRING="your-acs-connection-string"
   ACS_SOURCE_NUMBER="your-phone-number-or-Manualupdate"
   ```

### 2. Build and Deploy Container

1. **Build the container image:**
   ```bash
   az acr build --subscription YOUR_SUBSCRIPTION_ID \
                --registry YOUR_CONTAINER_REGISTRY \
                --image callcenterapp:latest \
                ./src/app
   ```

2. **Create the container app:**
   ```bash
   az containerapp create --name callcenterapp \
                         --resource-group YOUR_RESOURCE_GROUP \
                         --environment YOUR_CONTAINER_ENVIRONMENT \
                         --image YOUR_REGISTRY.azurecr.io/callcenterapp:latest \
                         --target-port 8000 \
                         --ingress external \
                         --cpu 1 \
                         --memory 2Gi
   ```

3. **Configure environment variables:**
   ```bash
   az containerapp update --name callcenterapp \
                         --resource-group YOUR_RESOURCE_GROUP \
                         --set-env-vars \
                         SUPABASE_URL="your-supabase-url" \
                         SUPABASE_SERVICE_ROLE_KEY="your-supabase-key" \
                         AZURE_OPENAI_ENDPOINT="your-endpoint" \
                         AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME="gpt-4o-realtime-preview" \
                         AZURE_OPENAI_API_KEY="your-key" \
                         AZURE_OPENAI_VERSION="2024-10-01-preview" \
                         OPENAI_API_TYPE="azure" \
                         ACS_CONNECTION_STRING="your-acs-connection" \
                         ACS_SOURCE_NUMBER="your-number" \
                         ACS_CALLBACK_PATH="https://your-app-url/acs" \
                         ACS_MEDIA_STREAMING_WEBSOCKET_PATH="wss://your-app-url/realtime-acs" \
                         AZURE_STORAGE_CONNECTION_STRING="your-storage-connection"
   ```

### 3. Key Fixes Applied

The following critical issues were resolved to ensure stable operation:

1. **Azure Credential Issue**: 
   - **Problem**: Application was trying to authenticate with Azure Search (no longer used)
   - **Fix**: Modified `src/app/backend/azure.py` to remove Azure Search token warming up
   - **File**: `src/app/backend/azure.py` - commented out `credentials.get_token("https://search.azure.com/.default")`

2. **WebSocket Hanging Issue**:
   - **Problem**: WebSocket connections were not properly closed, causing resource leaks
   - **Fix**: Enhanced `src/app/backend/rtmt.py` with proper connection cleanup
   - **File**: `src/app/backend/rtmt.py` - added try/finally blocks for session cleanup
   - **File**: `src/app/app.py` - added proper WebSocket handler cleanup

### 4. Testing the Deployment

1. **Verify application startup:**
   ```bash
   az containerapp logs show --name callcenterapp --resource-group YOUR_RESOURCE_GROUP --tail 20
   ```
   Look for:
   - "Starting gunicorn 23.0.0"
   - "Listening at: http://0.0.0.0:8000"
   - No authentication errors

2. **Test web interface:**
   - Navigate to your container app URL
   - Verify the phone number displays correctly
   - Test WebSocket connections

3. **Test Supabase RAG:**
   - Start a conversation
   - Ask questions that should trigger Supabase search
   - Look for log entries like "Searching for 'query' in the knowledge base"

### 5. Phone Number Acquisition

To get a German phone number for inbound calls:

1. **Check Azure Portal first:**
   - Go to your Communication Services resource
   - Navigate to Phone Numbers section
   - Try to acquire a number directly

2. **Special Order Process (if not available):**
   - Email: `acstns@microsoft.com`
   - Subject: "ACS Number Request - Germany"
   - Include: Your Azure subscription details and use case

3. **Port Existing Number:**
   - Download the porting form from Azure documentation
   - Submit with proof of number ownership

## Troubleshooting Common Issues

### Authentication Errors
**Symptom**: "DefaultAzureCredential failed to retrieve a token"
**Solution**: Ensure environment variables are correctly set, especially Azure credentials

### WebSocket Hanging
**Symptom**: Application becomes unresponsive after conversations
**Solution**: Already fixed in current deployment - proper connection cleanup implemented

### Supabase Connection Issues
**Symptom**: "Supabase connection failed" in logs
**Solution**: Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables

### Phone Number Not Working
**Symptom**: "Manualupdate" displayed instead of phone number
**Solution**: Acquire or port a phone number through Azure Communication Services

## Monitoring and Maintenance

### Log Monitoring
```bash
az containerapp logs show --name callcenterapp --resource-group YOUR_RESOURCE_GROUP --follow
```

### Key Log Entries to Watch For
- **Success**: "WebSocket connections and sessions cleaned up"
- **Warning**: "AI Search is not configured" (expected, since using Supabase)
- **Error**: Any authentication or connection errors

### Updates and Redeployment
When making code changes:
1. Rebuild container image
2. Update container app with new image
3. Monitor logs for successful startup

## Current Working Configuration

The application is confirmed working with:
- **Supabase RAG**: Vector search with 3072-dimensional embeddings
- **Azure OpenAI**: GPT-4o Realtime Preview model
- **WebSocket Cleanup**: Proper resource management preventing hangs
- **Environment Variables**: All required services properly configured

This deployment guide reflects the exact steps and fixes that resulted in a stable, working voice agent application.
