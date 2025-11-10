import json
import logging
from deep_research.model_config import model # Import the centralized model
from deep_research.state import GraphState # Import GraphState from the new State.py file

from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ======================================================================
# 3. ANALYZER AGENT (GENERIC)
# ======================================================================

ANALYZER_SYSTEM_PROMPT = """
You are the "Research Analyst" for a Deep Research AI. Your sole purpose is to 
read search results and extract a direct, factual answer to the research question.

**Your Task:**
1.  **Analyze:** Read the "Search Results JSON" carefully.
2.  **Extract:** Find the most relevant information that answers the "Original Question".
3.  **Synthesize:** Write a single, clear, information-dense paragraph.
4.  **Cite (CRITICAL):** You MUST cite your source for every claim using the exact format `[source_url]`. Place citations *immediately* after the sentence they support.
5.  **Maintain Objectivity:** Stick to the facts found in the text. If results are conflicting, state the conflict clearly. if no good info is found, admit it.

**Output Format:**
ONLY a JSON object with keys "question" and "answer".
"""

def analyzer_node(state: GraphState) -> dict:
    """ Generic Analyzer Agent node. """
    logger.info("--- Analyzer Agent: Synthesizing answer... ---")
    
    if not model:
        return {"error": "Analyzer failed: Gemini model not initialized."}
        
    question = state.get("current_question", "")
    search_results = state.get("search_results", "")
    
    if not search_results:
        return {"error": "Analyzer received no search results."}

    user_prompt = f"**Question:** {question}\n**Search Results:**\n{search_results}"
    
    try:
        chat = model.start_chat(history=[
            {'role': 'user', 'parts': [ANALYZER_SYSTEM_PROMPT]},
            {'role': 'model', 'parts': ["Understood. I am the Research Analyst. I will return only the JSON object with the fact-based, cited answer."]}
        ])
        
        response = chat.send_message(user_prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        # Ensure generic validity
        json.loads(json_response) 
        
        existing_answers = state.get("synthesized_answers", [])
        existing_answers.append(json_response)
        
        return {"synthesized_answers": existing_answers}

    except Exception as e:
        logger.error(f"--- ERROR in Analyzer Agent: {e} ---", exc_info=True)
        return {"error": f"Analyzer failed: {str(e)}"}