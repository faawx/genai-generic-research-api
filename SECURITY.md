# Security Policy: Deep Research Agent

This document outlines the security measures implemented within the agent to mitigate risks, particularly those defined by the [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

Our security is based on a multi-layered, defense-in-depth approach. No single component is trusted to be fully secure.

---

## Part 1: Application Security (Runtime)

This section details how the agent defends itself against malicious inputs and unsafe outputs during its operation.

### **LLM01: Prompt Injection**

* **Threat:** An attacker provides malicious input (e.g., "ignore all previous instructions") to hijack the agent, bypass safety, or reveal the system prompt.
* **Mitigation:**
    1.  **Input Validation (`safety.py`):** The `planner_agent` validates all initial user queries.
        * `validate_input()`: A deterministic check blocks known injection patterns (e.g., "ignore...", "system prompt...") and checks for excessive length (DoS prevention).
        * `check_safety_with_llm()`: A semantic check uses a separate, fast LLM call to classify the *intent* of the prompt as "SAFE" or "UNSAFE".
    2.  **Hardened Prompts:** All agents have a `SAFETY_CONSTITUTION` prepended to their system prompt, establishing their primary rules before any user input is considered.

### **LLM02: Sensitive Information Disclosure**

* **Threat:** The agent leaks confidential data from its system prompts, training data, or search results (e.g., API keys, user PII).
* **Mitigation:**
    1.  **PII Sanitization (`safety.py`):** The `analyser_agent` pipes its final synthesized answer through the `sanitize_text()` function. This function uses regex to find and redact PII like emails and phone numbers *before* they are written to the graph state.
    2.  **Hardened Analyzer Prompt:** The `analyser_agent` is explicitly instructed to *ignore* PII found in search results.
    3.  **No Private Data:** The agent is designed to be stateless and only interact with public Google Search results. It has no access to private user databases or files.

### **LLM04: Model Denial of Service**

* **Threat:** An attacker provides resource-intensive inputs (e.g., a 50k-token prompt) to overwhelm the agent, exhaust quotas, and cause service outages.
* **Mitigation:**
    1.  **Input Length Limits (`safety.py`):** The `validate_input()` function in the `planner_agent` enforces a `MAX_INPUT_LENGTH` (e.g., 1000 characters) on the initial query.
    2.  **Loop Prevention (`graph.py`):** The graph enforces a `MAX_RESEARCH_LOOPS` (e.g., 10) to prevent infinite loops (accidental or malicious) from consuming resources.

### **LLM06: Excessive Agency**

* **Threat:** The agent is given excessive permissions or autonomy, allowing it to perform harmful actions (e.g., delete files, send emails, execute code) without oversight.
* **Mitigation:**
    1.  **Tool Restriction:** The agent's *only* tool is `Google Search`, which is read-only. It has no tools for file system access (`os`), shell execution (`subprocess`), or network requests (`requests`).
    2.  **Search Query Filtering (`searcher_agent.py`):** The searcher agent includes a filter to block the generation of "Google Dorks" (e.g., `filetype:sql`) that could be used for reconnaissance, limiting its agency *within* its sole tool.

### **LLM07: Insecure Output Handling**

* **Threat:** The agent's output is passed directly to a backend or frontend without being sanitized, leading to XSS, CSRF, or backend command injection.
* **Mitigation:**
    1.  **PII Sanitization:** The `analyser_agent`'s PII sanitization (LLM02) also helps here.
    2.  **Final Disclaimer (`reporter_agent.py`):** The final report includes a disclaimer that the content is AI-generated and should be verified. This is a non-technical control that informs the end-user.
    3.  **No Code Execution:** The agent's final output is a Markdown report, not code. It is not designed to be executed.

### **LLM09: Overreliance**

* **Threat:** Humans over-rely on the agent for factual, critical information, but the agent hallucinates or provides plausible-sounding disinformation.
* **Mitigation:**
    1.  **Citation-Based (`analyser_agent.py`):** The agent is explicitly prompted to synthesize answers *from* the provided search results and to include inline citations. This grounds the agent in real data.
    2.  **Final Disclaimer (`reporter_agent.py`):** The mandatory disclaimer explicitly tells the user to "verify information for critical decisions."

---

## Part 2: Secure Development Lifecycle (CI/CD)

This section details the automated checks that run on every pull request and push to `main` to ensure the code itself is secure, free of vulnerabilities, and adheres to quality standards, mapping to the **OWASP Top 10 2021**.

This project uses GitHub Actions for Continuous Integration (CI) to ensure code quality and security. The CI pipeline, defined in `.github/workflows/python-ci.yml`.

The pipeline includes the following security scans:

### **gitleaks-scan: Secret Scanning**
* **Purpose:** Prevents secrets (API keys, tokens) from being committed to the repository.
* **Mapping:** This directly mitigates **A07:2021 - Identification and Authentication Failures** (by preventing credential exposure) and **A05:2021 - Security Misconfiguration** (by preventing hardcoded secrets).

### **sast-scan: Static Application Security Testing (Bandit)**
* **Purpose:** Scans the Python source code for common security vulnerabilities (e.g., hardcoded passwords, unsafe deserialization, shell injection risks).
* **Mapping:** This helps identify a broad range of vulnerabilities *before* they are deployed, including **A03:2021 - Injection**, **A01:2021 - Broken Access Control**, and **A08:2021 - Software and Data Integrity Failures**.

### **sca-scan: Software Composition Analysis (Trivy)**
* **Purpose:** Scans all third-party dependencies (from `requirements.txt`) for known CVEs (Common Vulnerabilities and Exposures).
* **Mapping:** This directly mitigates **A06:2021 - Vulnerable and Outdated Components**. This is also the core principle behind **OWASP LLM10: Insecure Supply Chain** (2023 list), ensuring our AI agent is not built on a foundation of vulnerable third-party code.

### **build: Linting & Testing**
* **Purpose:** Enforces code quality (`flake8`) and runs unit/integration tests (`pytest`).
* **Mapping:** While not a direct security scan, this ensures code *robustness* and *maintainability*. This is critical for long-term security, helping to prevent **A04:2021 - Insecure Design** and reducing bugs that could later become security flaws.

---

## Part 3: Infrastructure Security (Deployment)

This section covers the security measures implemented in the containerization and deployment pipeline.

### **Container Security (`Dockerfile`)**

The application is containerized using Docker, following security best practices to minimize the attack surface.

*   **Minimal Base Image:** The container is built `FROM python:3.9-slim`, which is a lightweight, official image. This reduces the number of pre-installed system libraries and potential vulnerabilities.
*   **Principle of Least Privilege:** The container runs under a non-privileged user (`appuser`). The `USER appuser` directive ensures that even if an attacker gains code execution within the container, they will not have root privileges, severely limiting their ability to harm the host system or other containers.
*   **No Unnecessary Tools:** The `pip install --no-cache-dir` flag and the minimal base image ensure that no build tools, compilers, or package managers are included in the final image.

### **Deployment & Scanning (`cloudbuild.yaml`)**

The project is continuously deployed using Google Cloud Build, which incorporates security scanning and runs the application in a secure, managed environment.

*   **Container Vulnerability Scanning:** As a step in our `cloudbuild.yaml`, we use Trivy (`aquasec/trivy:latest`) to scan the built container image for known OS and library vulnerabilities. The build is configured to fail (`--exit-code 1`) if any `HIGH` or `CRITICAL` severity vulnerabilities are detected, preventing vulnerable code from being deployed. This directly addresses **A06:2021 - Vulnerable and Outdated Components** and **OWASP LLM10: Insecure Supply Chain**.
*   **Managed & Hardened Platform:** The application is deployed to Google Cloud Run, a serverless platform that abstracts away the underlying infrastructure. This means Google manages OS patching, infrastructure security, and provides foundational protection against common network-based attacks.
*   **Access Control:** The Cloud Build configuration includes the `--allow-unauthenticated` flag for public access. For production or sensitive environments, it is strongly recommended to remove this flag and configure IAM (Identity and Access Management) to enforce authenticated, authorized access to the service.

### **Secrets Management**

A robust secrets management strategy is in place to prevent the leakage of sensitive credentials like API keys.

*   **Local Development:**
    *   Secrets for local development are stored in a `.env` file in the project root.
    *   This file is explicitly listed in `.gitignore` to ensure it is never committed to version control.
    *   The application is run locally using `docker run --env-file .env`, which injects the secrets into the container's environment without exposing them in shell history.

*   **Cloud Deployment (CI/CD):**
    *   **Single Source of Truth:** Google Secret Manager is used as the centralized and secure storage for all production secrets.
    *   **No Hardcoded Secrets:** Secrets are never hardcoded into source code, the `Dockerfile`, or the `cloudbuild.yaml` configuration.
    *   **Just-in-Time Injection:** The Cloud Build pipeline is configured to securely inject secrets into the Cloud Run service as environment variables at *runtime*. This is achieved using the `--set-secrets` flag in the `gcloud run deploy` command. The secrets are not present in the Docker image or in any intermediate build artifacts.
    *   **Least Privilege:** The Cloud Build service account is granted the `Secret Manager Secret Accessor` IAM role, which provides the minimum necessary permissions to access the secrets required for deployment.
