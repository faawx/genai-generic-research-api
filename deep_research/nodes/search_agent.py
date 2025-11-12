import json
from typing import Dict
import logging
from deep_research.model_config import model # Import the centralized model
from deep_research.state import GraphState # Import GraphState from the new State.py file
from deep_research.safety import SAFETY_CONSTITUTION

from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ======================================================================
# 2. SEARCHER AGENT (GENERIC)
# ======================================================================

SEARCHER_AGENT_PROMPT = """

{SAFETY_CONSTITUTION}

You are the "Search Specialist" for a Deep Research AI. Your job is to take a 
specific research question and formulate the single most effective Google search query.

**Core Principles for Generic Research:**
* **Specificity is Key:** Avoid broad terms. Use specific terminology related to the domain.
* **Authority Matching:** * *For technical/scientific:* Use keywords like "white paper", "journal", "study", "documentation".
    * *For news/current events:* Append the current year (e.g., 2025) and look for reputable news outlets.
    * *For facts/statistics:* Use "official report", "statistics", "database".

**Security Rules:**
* Do NOT generate "Google Dorks" (e.g., `site:*.gov filetype:confidential`).
* Do NOT search for PII or private databases.
* Keep queries focused on public, educational, or news information.

**Input:** `[Social and economic inequality in pre-revolutionary France]`
**Output:** `social economic inequality Ancien Regime France scholarly sources`

**Input:** `[Current state of quantum computing encryption threats]`
**Output:** `quantum computing threat to current cryptography algorithms 2024 2025`

**Input:** `[Latest developments in Alzheimer's treatment]`
**Output:** `novel Alzheimer's treatments clinical trials 2024 2025`
"""

def searcher_node(state: GraphState) -> Dict[str, str]:
    """ The generic Searcher Agent node. """
    logger.info("--- Searcher Agent: Formulating query... ---")
    
    if not model:
        return {"error": "Searcher failed: Gemini model not initialized."}
        
    current_question = state.get("current_question", "")
    if not current_question:
        return {"error": "Searcher failed: No current question found in state."}
        
    try:
        chat = model.start_chat(history=[
            {'role': 'user', 'parts': [SEARCHER_AGENT_PROMPT]},
            {'role': 'model', 'parts': ["Understood. I am the Search Specialist. I will return only the optimized, domain-specific search query string."]}
        ])
        
        response = chat.send_message(current_question)
        search_query = response.text.strip().replace('"', '')

        # --- GUARDRAIL: OUTPUT VALIDATION ---
        forbidden_dorks = ["filetype:sql", "filetype:env", "site:*.admin", "index of /"]
        for dork in forbidden_dorks:
            if dork in search_query.lower():
                logger.warning(f"Searcher blocked for generating risky query: {search_query}")
                search_query = current_question # Fallback to plain question


        logger.info(f"--- Formulated query: {search_query} ---")
        
        return {"search_query": search_query}
        
    except Exception as e:
        logger.error(f"--- ERROR in Searcher Agent: {e} ---", exc_info=True)
        return {"error": f"Searcher failed: {str(e)}"}