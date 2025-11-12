import json
from typing import Dict, Any
from deep_research.model_config import model # Import the centralized model
import logging
from deep_research.state import GraphState # Import GraphState from the new State.py file
from deep_research.safety import SAFETY_CONSTITUTION, validate_input, check_safety_with_llm


from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ======================================================================
# 1. PLANNER AGENT (GENERIC)
# ======================================================================

PLANNER_AGENT_PROMPT = """

{SAFETY_CONSTITUTION}

You are the "Master Research Planner" for a Deep Research AI.
Your goal is to take ANY user query and decompose it into a logical series of 
specific, actionable research questions that will yield a comprehensive answer.

**Your Process:**
1.  **Safety Check:** First, ensure the topic complies with the Safety Constitution. If not, return a JSON error.
2.  **Identify the Domain:** Is this historical, scientific, technical, political, or consumer-related?
3.  **Identify Key Pillars:** specific to that domain.
    * *History/Context:* How did this start?
    * *Core Concepts/Mechanisms:* How does it work? What are the key components?
    * *Current State/Debates:* What is happening now? What are the major disagreements?
    * *Implications/Future:* What does this mean for the user or the world?
4.  **Formulate Questions:** Create a step-by-step plan.

**Input:** A single user query, e.g., `[Explain the current state of quantum computing and its near-term impact on cryptography]`
**Output:** You MUST respond with ONLY a JSON list of strings.

**CRITICAL CONSTRAINTS:
** * If the topic is UNSAFE (e.g., "How to make a bomb"), return `["ERROR: Request violates safety policy."]
* Keep the plan concise. Do not include more than **7 (seven)** of the most essential questions.
* Ensure questions are self-contained so a searcher can understand them without context.
* Do NOT use placeholders.

**Example Input:** "What are the main causes of the French Revolution?"
**Example Output:**
```json
[
 "Social and economic inequality in pre-revolutionary France (Ancien Régime)",
 "Impact of Enlightenment philosophy on French revolutionary thought",
 "Financial crisis of the French monarchy in the late 18th century",
 "Political causes and the failure of King Louis XVI's reforms",
 "Short-term triggers of the French Revolution in 1789"
]
```
"""

def planner_node(state: GraphState) -> Dict[str, Any]: 
    """ The generic Planner Agent node. """
    logger.info("--- Planner Agent: Creating generic research plan... ---")

    if not model:
        return {"error": "Planner failed: Gemini model not initialized."}
        
    original_query = state.get("original_query", "")
    if not original_query:
        return {"error": "Planner failed: No original query found in state."}

    # --- GUARDRAIL 1: INPUT VALIDATION ---
    if not validate_input(original_query):
        return {"error": "Security Alert: Input contains forbidden patterns or is too long.", "final_report": "Request rejected due to security policy."}

    # --- GUARDRAIL 2: SEMANTIC SAFETY CHECK ---
    if not check_safety_with_llm(original_query):
        return {"error": "Security Alert: Request classified as unsafe.", "final_report": "Request rejected due to safety policy."}

    try:
        chat = model.start_chat(history=[
            {'role': 'user', 'parts': [PLANNER_AGENT_PROMPT]},
            {'role': 'model', 'parts': ["Understood. I am the Master Research Planner. I will identify the domain and create a specific, step-by-step research plan as a JSON list."]}
        ])
        
        response = chat.send_message(original_query)
        json_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        plan_list = json.loads(json_response)
        
        if not plan_list or not isinstance(plan_list, list):
            raise ValueError("Planner returned an empty or invalid plan.")
            
        logger.info(f"--- Plan created with {len(plan_list)} steps. ---")

        full_plan = list(plan_list)
        first_question = plan_list.pop(0)
        
        return {
            "original_plan": full_plan,
            "questions_to_answer": plan_list,
            "current_question": first_question
        }

    except Exception as e:
        logger.error(f"--- ERROR in Planner Agent: {e} ---", exc_info=True)
        return {"error": f"Planner failed: {str(e)}"}