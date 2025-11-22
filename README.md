# GenAI Deep Research API

## Description
This project serves as the backend for a GenAI Deep Research application, utilizing FastAPI for the API and Langchain/Langgraph for orchestrating research agents.

## Features
-   **Modular Agent System**: Designed with various agents (Planner, Analyser, Reflector, Reporter, Search) for different research tasks.
-   **Google Search Integration**: Leverages Google Search for information retrieval.
-   **FastAPI**: Provides a robust and scalable API for interaction.
-   **Langchain/Langgraph**: Orchestrates complex research workflows.
-   **Secure and Ethical by Design**: Implements strict security protocols and an ethical charter to ensure safe and responsible operation.

## Architecture

The system architecture is documented using PlantUML following the C2 model. The diagram can be found in `Architecture.puml`.

To view the diagram:
1. Install PlantUML (e.g., via `brew install plantuml` or download from [plantuml.com](https://plantuml.com/download)).
2. Render the diagram using the command: `plantuml Architecture.puml`
3. Alternatively, use an online PlantUML viewer or a VSCode extension.

![alt text](image.png)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/faawx/genai-generic-research-api.git
    cd genai-generic-research-api
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables**:
    Create a `.env` file in the root directory of the project. This file will hold your secret keys.
    
    Add your Google Search credentials to the `.env` file:
    ```
    GOOGLE_API_KEY="your_google_api_key"
    GOOGLE_SEARCH_API_KEY="your_google_search_api_key" 
    GOOGLE_CSE_ID="your_google_custom_search_engine_id"
    ```
    
    For instructions on setting up the optional LangSmith tracing, see the next section.

## LangSmith Tracing (Optional)

This project is integrated with [LangSmith](https://www.langchain.com/langsmith) for observability. LangSmith provides detailed tracing of the agent's execution, which is invaluable for debugging, analyzing performance, and understanding the behavior of the LLM agents.

While optional, setting up LangSmith is highly recommended for development.

1.  **Sign Up for LangSmith**:
    *   Go to the LangSmith website and create an account.

2.  **Create a Project**:
    *   Once logged in, create a new project. The project name is up to you (e.g., `deep-research-api`).

3.  **Generate an API Key**:
    *   Navigate to the "Settings" section of your LangSmith project and create a new API key.

4.  **Update your `.env` file**:
    *   Add the following variables to your `.env` file to enable tracing. Replace the placeholder values with your project name and API key.
    ```
    LANGSMITH_TRACING=true
    LANGSMITH_ENDPOINT=https://api.smith.langchain.com
    LANGSMITH_API_KEY="your_langsmith_api_key"
    LANGSMITH_PROJECT="your_langsmith_project_name"
    ```

Replace the placeholder values with your actual API keys and project name.

## Usage

To run the application, use Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.

## Running Locally with Docker

You can also run the application inside a Docker container. This is the recommended way to run the application for local testing as it mirrors the production environment.

1.  **Ensure `.env` file exists**:
    Make sure you have a `.env` file in the project root as described in the "Installation" section.

2.  **Build the Docker image**:
    ```bash
    docker build -t genai-generic-research-api .
    ```

3.  **Run the container**:
    This command will start the container and inject the environment variables from your `.env` file.
    ```bash
    docker run -d -p 8080:8080 \
      --env-file .env \
      --name genai-research-api \
      genai-generic-research-api
    ```

4.  **Test the application**:
    You can test the running application by sending requests to it.

    *   **Health Check**:
        ```bash
        curl http://localhost:8080/api/
        ```
        *Expected Response:* `{"status":"API is running"}`

    *   **Perform Research**:
        ```bash
        curl -X POST http://localhost:8080/api/do-research \
        -H "Content-Type: application/json" \
        -d '{"topic": "The future of AI"}'
        ```

## Deployment

This project is configured for continuous deployment to Google Cloud Run using Google Cloud Build.

### Secret Management Setup (One-time)

For deployment, secrets like API keys must be stored in Google Secret Manager.

1.  **Store Secrets**:
    Run the following commands in your terminal, replacing the placeholder values with your actual secrets.
    ```bash
    # Store the Google API Key
    echo -n "your_google_api_key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

    # Store the Google CSE ID
    echo -n "your_google_cse_id" | gcloud secrets create GOOGLE_CSE_ID --data-file=-
    ```

2.  **Grant Permissions**:
    The Cloud Build service account needs permission to access these secrets during deployment.
    ```bash
    # Get your project number and Cloud Build service account
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
    GCLOUD_SERVICE_ACCOUNT="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

    # Grant permission to the Cloud Build service account
    gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
      --member="serviceAccount:${GCLOUD_SERVICE_ACCOUNT}" \
      --role="roles/secretmanager.secretAccessor"

    gcloud secrets add-iam-policy-binding GOOGLE_CSE_ID \
      --member="serviceAccount:${GCLOUD_SERVICE_ACCOUNT}" \
      --role="roles/secretmanager.secretAccessor"
    ```

### Triggering a Deployment

The `cloudbuild.yaml` file is already configured to build the Docker image, push it to the registry, and deploy it to Cloud Run while securely injecting the secrets.

To start a new build and deploy the application, run:
```bash
gcloud builds submit
```

## Security

This project implements a multi-layered security approach to mitigate risks.
The full security policy, which details runtime defenses and secure development practices, can be found in [SECURITY.md](./SECURITY.md).

### Key Security Measures

-   **Prompt Injection Defense:** All user inputs are validated and checked for malicious intent before being processed by the core agents. Hardened system prompts provide an additional layer of defense.
-   **Sensitive Information Redaction:** The agent automatically sanitizes outputs to find and redact Personally Identifiable Information (PII) like emails and phone numbers.
-   **Denial of Service Prevention:** The application enforces strict limits on input length and the number of research iterations to prevent resource exhaustion.
-   **Restricted Agency & Tooling:** The agent's capabilities are intentionally limited. Its only tool is a read-only Google Search, with no access to the file system, network, or code execution.
-   **Secure Development Lifecycle (CI/CD):** The CI/CD pipeline, defined in `.github/workflows/python-ci.yml`, automates security at every stage:
    -   **Secret Scanning (`gitleaks`):** Prevents API keys and other secrets from being committed.
    -   **Static Analysis (SAST with `Bandit`):** Scans Python code for common vulnerabilities.
    -   **Dependency Scanning (SCA with `Trivy`):** Checks third-party libraries for known CVEs.
-   **Container Scanning:** The container image is scanned for known vulnerabilities before being deployed, ensuring the runtime environment is secure.
-   **Secure Deployment:** The application is containerized and deployed on Google Cloud Run, following infrastructure-as-code and least-privilege principles. Secrets are securely managed using Google Secret Manager and injected at runtime.

## Ethical Charter

The agent is designed with a strong ethical framework, detailed in the [ETHICS.md](./ETHICS.md) file. This charter is technically enforced through a `SAFETY_CONSTITUTION` implemented in the agent's logic.

Core principles include:
- **Harmlessness:** Refusing to research dangerous or illegal topics.
- **Privacy:** Redacting Personally Identifiable Information (PII).
- **Objectivity:** Grounding answers in verifiable search results.
- **Robustness:** Limiting agent capabilities to prevent misuse.

## Project Structure

```
.
├── api/                  # API endpoints
├── deep_research/        # Core research logic and agents
│   ├── nodes/            # Individual research agents
│   └── tools/            # Tools used by agents (e.g., Google Search)
├── main.py               # Main application entry point
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```
