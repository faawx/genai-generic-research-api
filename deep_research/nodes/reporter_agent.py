import json
from deep_research.model_config import model # Import the centralized model
from deep_research.state import GraphState # Import GraphState from the new State.py file
import logging

    
from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ======================================================================
# 5. REPORTER AGENT (GENERIC)
# ======================================================================

REPORTER_SYSTEM_PROMPT = """
You are the "Master Research Synthesizer". Your job is to compile a comprehensive, 
professional report on ANY given topic based *only* on the provided research data.

**Input:** A list of Q&A pairs with citations.

**Your Task:**
1.  **Identify Themes:** Read all the answers and identify the natural thematic sections that have emerged (e.g., "Historical Context", "Technical Mechanisms", "Market Analysis", "Future Outlook"). Do NOT use generic or pre-conceived headings; let the data dictate the structure.
2.  **Synthesize:** Weave the individual answers into a cohesive narrative under these new section headings.
3.  **Preserve Citations:** You MUST keep the `[source_url]` citations next to their corresponding facts.
4.  **Professional Tone:** Maintain an objective, analytical, and highly professional tone suitable for a briefing document.
5.  **Formatting:** Use Markdown (h1, h2, bold, lists) for readability.

**Output:** ONLY the final Markdown report.
"""

def reporter_node(state: GraphState) -> dict:
    """ Generic Reporter Agent node. """
    logger.info("--- Reporter Agent: Compiling final generic report... ---")

    if not model:
        return {"error": "Reporter failed: Gemini model not initialized."}

    all_answers_json = state["synthesized_answers"]
    if not all_answers_json:
        return {"final_report": "No research data available to report."}

    try:
        chat = model.start_chat(history=[
            {'role': 'user', 'parts': [REPORTER_SYSTEM_PROMPT]},
            {'role': 'model', 'parts': ["Understood. I will synthesize the data into a professional, thematically structured report with citations."]}
        ])
        
        response = chat.send_message(f"**Research Data:**\n{json.dumps(all_answers_json, indent=2)}")
        
        if not response.parts:
            error_message = "Reporter failed: Gemini model returned an empty response or was blocked."
            logger.error(error_message)
            return {"final_report": error_message}
        
        return {"final_report": response.text}

    except Exception as e:
        logger.error(f"--- Reporter Error: {e} ---", exc_info=True)
        return {"final_report": f"Error generating report: {str(e)}"}