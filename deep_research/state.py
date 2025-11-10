from typing import TypedDict, List, Optional

# --- Graph State Definition ---
# This defines the full state of the main graph.
class GraphState(TypedDict):
    original_query: str              # The initial user query
    original_plan: Optional[List[str]] # The full plan from the Planner
    questions_to_answer: List[str]   # The queue of questions
    current_question: Optional[str]  # The question being worked on
    search_query: Optional[str]      # The query for the search tool
    search_results: Optional[str]    # The JSON string from the search tool
    synthesized_answers: List[str]   # List of JSON answer strings
    decision: Optional[str]          # 'continue' or 'complete'
    final_report: Optional[str]      # The final Markdown report
    error: Optional[str]             # To hold any error messages
