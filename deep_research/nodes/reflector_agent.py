import json
from deep_research.model_config import model # Import the centralized model
import logging
from deep_research.state import GraphState # Import GraphState from the new State.py file
    
from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ======================================================================
# 4. REFLECTOR AGENT (GENERIC)
# ======================================================================

REFLECTOR_SYSTEM_PROMPT = """
You are the "Research Coordinator". Your job is to ensure completeness and depth.

**Task:**
Review the latest answer. Does it raise new, *critical* questions that must be answered 
to fully address the user's original intent?

**Rules for Generic Research:**
1.  **STRONGLY PREFER AN EMPTY LIST.** Do not add a new question unless it 
    is absolutely critical.
2.  **DO NOT REPHRASE.** Do not add questions that are just minor 
    variations of questions in the original plan or current queue.
3.  **NO TRIVIA.** Do not add questions about "best food" or "cool 
    sights" unless it was the point of the original query.
4.  **Output Format:** You MUST respond with ONLY a JSON list of strings.

**Output:** ONLY a JSON list of new question strings (or an empty list `[]`).
"""

def reflector_node(state: GraphState) -> dict:
    """ Generic Reflector Agent node. """
    logger.info("--- Reflector Agent: Reflecting on answer... ---")
    
    if not model:
        return {"error": "Reflector failed: Gemini model not initialized."}

    latest_answer_json = state["synthesized_answers"][-1]
    latest_answer = json.loads(latest_answer_json)
    original_plan = state["original_plan"]
    current_queue = list(state["questions_to_answer"])

    try:
        chat = model.start_chat(history=[
            {'role': 'user', 'parts': [REFLECTOR_SYSTEM_PROMPT]},
            {'role': 'model', 'parts': ["Understood. I will review the findings and only add critical new questions if necessary."]}
        ])
        
        prompt = f"""
        **Original Plan:** {json.dumps(original_plan)}
        **Current Queue:** {json.dumps(current_queue)}
        **Latest Q&A:** Question: "{latest_answer['question']}" Answer: "{latest_answer['answer']}"
        """
        
        response = chat.send_message(prompt)
        new_tasks = json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
        
    except Exception as e:
        logger.error(f"--- Reflector Error: {e} ---")
        new_tasks = []

    if new_tasks:
        logger.info(f"--- New tasks found: {new_tasks} ---")
        for task in new_tasks:
            if task not in original_plan and task not in current_queue:
                current_queue.append(task)
    
    current_count = state.get("loop_count", 0) + 1
    if not current_queue:
        return {"decision": "complete", "loop_count": current_count}
    else:
        return {
            "decision": "continue",
            "questions_to_answer": current_queue,
            "current_question": current_queue.pop(0),
            "loop_count": current_count
        }