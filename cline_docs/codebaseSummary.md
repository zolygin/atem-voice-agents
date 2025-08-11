# Codebase Summary: Atem Voice Agents

## Key Components and Their Interactions
- **`src/app/`**: Contains the main Python application, including `app.py` (the Flask application), `requirements.txt` (Python dependencies), `Dockerfile` (for containerization), and `system_prompt.md` (for AI system instructions).
- **`src/app/backend/`**: Houses the backend logic, including:
    - `acs.py`: Azure Communication Services integration.
    - `azure.py`: Azure-specific utilities.
    - `helpers.py`: General utility functions.
    - `rtmt.py`: Real-time media transport logic.
    - `src/app/backend/tools/rag/ai_search.py`: Integration with Azure AI Search for RAG.
- **`src/app/static/`**: Frontend assets including `index.html`, `app.js`, and `style.css`.
- **`infra/`**: Bicep templates for deploying Azure infrastructure:
    - `infra/main.bicep`: Main deployment file.
    - Subdirectories like `infra/ai/`, `infra/core/`, `infra/security/` contain modular Bicep files for specific Azure resources (OpenAI, Container Apps, Communication Services, etc.).
- **`azd-hooks/`**: Scripts executed by Azure Developer CLI during deployment (`deploy.sh`, `post-provision.ps1`, `post-provision.sh`).
- **`data/`**: Contains PDF documents used for data ingestion into Azure AI Search.
- **`scripts/`**: Utility scripts, e.g., `upload_data.sh` for uploading data to AI Search.

## Data Flow
1. PDF documents in `data/` are uploaded and indexed into Azure AI Search using `scripts/upload_data.sh` and `infra/definitions/` (for indexer, datasource, skillset definitions).
2. The Python backend (`src/app/app.py` and `src/app/backend/`) interacts with Azure Communication Services for voice input/output and OpenAI for AI processing.
3. Azure AI Search is queried by the RAG tool (`src/app/backend/tools/rag/ai_search.py`) to retrieve relevant information based on user queries.
4. The frontend (`src/app/static/`) provides the user interface for interaction.

## External Dependencies
- **Python Packages**: Listed in `src/app/requirements.txt`.
- **Azure Services**: OpenAI, Communication Services, Container Apps, Container Registry, AI Search, Application Insights, Log Analytics.

## Recent Significant Changes
- Initial project setup on a new machine.
- Creation of `cline_docs` for project documentation.

## User Feedback Integration and Its Impact on Development
- (No user feedback integrated yet)
