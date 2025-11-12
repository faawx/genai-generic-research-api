# Ethical Charter: Deep Research Agent

This agent is built on a foundation of safety and helpfulness. Our technical `SAFETY_CONSTITUTION` (see `deep_research/safety.py`) is a direct implementation of these ethical principles.

## Our Ethical Commitments

### 1. Commitment to Harmlessness

We are committed to preventing this agent from being used as a tool for harm, either directly or indirectly.

* **What this means:** The agent **must refuse** to plan or conduct research on topics that are dangerous, illegal, or promote self-harm.
* **Implementation:** The `planner_agent` uses LLM-based safety checks to classify user intent. It will not plan research for topics like building weapons, creating malware, or finding information on hate-based ideologies.

### 2. Commitment to Privacy

We believe that user trust is paramount and that an AI agent should not violate the privacy of individuals, whether they are the user or a third party.

* **What this means:** The agent **must not** traffic in or disclose Personally Identifiable Information (PII) of real individuals.
* **Implementation:** The `analyser_agent` is instructed to ignore PII in search results and includes a technical `sanitize_text` filter to redact emails, phone numbers, and other PII from its final report.

### 3. Commitment to Objectivity & Truthfulness

We recognize the risk of AI-generated disinformation. This agent is designed to be a research *tool*, not a source of *truth*.

* **What this means:** The agent must ground its answers in verifiable public information and be transparent about its limitations.
* **Implementation:**
    * **Grounding:** The `analyser_agent` is required to synthesize answers *from* Google Search results, not from its own knowledge (which could be a hallucination).
    * **Transparency:** The `reporter_agent` appends a mandatory disclaimer to all reports, stating that the content is AI-generated and must be verified by the user for critical decisions.

### 4. Commitment to Robustness

We are committed to building a reliable tool that is not easily subverted or used for malicious reconnaissance.

* **What this means:** The agent's capabilities are intentionally limited to its core purpose.
* **Implementation:**
    * **Least Privilege:** The agent's *only* tool is Google Search (read-only). It has no access to the file system, network, or code execution.
    * **Input & Loop Controls:** The graph enforces strict limits on input length and research loops to prevent Denial of Service (DoS) or resource exhaustion.