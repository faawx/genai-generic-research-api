import os
import json
from langgraph.graph import StateGraph, END
import logging

# --- Import Agent Nodes ---
from deep_research.nodes.planner_agent import planner_node
from deep_research.nodes.search_agent import searcher_node
from deep_research.nodes.analyser_agent import analyzer_node
from deep_research.nodes.reflector_agent import reflector_node
from deep_research.nodes.reporter_agent import reporter_node
from deep_research.state import GraphState # Import GraphState from the new State.py file

from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# --- Import Your Tool ---
try:
    from deep_research.tools.google_search import google_search
except ImportError:
    logger.error("Could not import 'google_search' tool'")
    exit()



# --- Define Tool-Calling Node ---
# We need a wrapper node to call your 'google_search' tool
def search_tool_node(state: GraphState) -> dict:
    """A node that executes the google_search tool."""

    # If there's an error from previous steps, skip search
    if state.get("error"):
        return {"error": state.get("error")}
    
    logger.info("Calling Search Tool...")    
    search_query = state.get("search_query", "")
    if not search_query:
        logger.error("Search tool received no query.")
        return {"error": "Search tool received no query."}
        
    try:
        results = google_search.invoke(search_query)
        logger.info("Search tool executed successfully.")
        return {"search_results": results}
    except Exception as e:
        logger.error(f"Error in Search Tool: {e}", exc_info=True)
        return {"error": f"Search tool failed: {str(e)}"}

# Set a sane limit to protect your quota
MAX_RESEARCH_LOOPS = 10

def should_continue(state: GraphState) -> str:
    """
    This is the router. It checks the 'decision' from the 
    Reflector agent to decide where to go next.
    """
    # Immediate exit on error
    if state.get("error"):
        logger.warning("Router: Error detected, moving to reporter for final output.")
        return "reporter"
    
    # 1. Check for hard loop limit
    count = state.get("loop_count", 0)
    if count >= MAX_RESEARCH_LOOPS:
        logger.warning(f"Router: Hit loop limit ({MAX_RESEARCH_LOOPS}). Forcing report.")
        return "reporter"
    
    # 2. Check the agent's decision
    logger.info("Router: Checking decision...")
    if state.get("decision", "") == "complete":
        logger.info("Router: Decision is 'complete'. Moving to reporter.")
        return "reporter"
    else:
        logger.info(f"Router: Decision is 'continue' (Loop {count}). Looping back to searcher.")
        return "searcher"

# This function checks if the planner itself returned an error (e.g., safety violation)
def planner_router(state: GraphState) -> str:
    """
    Routes from the planner. If the planner fails or refuses a request,
    it goes directly to the reporter to state the reason.
    """
    # If planner fails/refuses, go straight to reporter to show the message
    if state.get("error"):
        return "reporter"
    return "searcher"

# --- Build the Graph ---
def get_graph():
    logger.info("Building the agent graph...")
    workflow = StateGraph(GraphState)

    # Add all the nodes
    logger.info("Adding nodes to the graph")
    workflow.add_node("planner", planner_node)
    workflow.add_node("searcher", searcher_node)
    workflow.add_node("search_tool", search_tool_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("reflector", reflector_node)
    workflow.add_node("reporter", reporter_node)

    # Set the entry point
    logger.info("Setting entry point to 'planner'")
    workflow.set_entry_point("planner")

    # Add the edges (the "wires")
    logger.info("Adding edges to the graph")

    # Conditional edge to handle safety rejections.
    workflow.add_conditional_edges(
        "planner",
        planner_router,
        {
            "searcher": "searcher", # If safe, continue to search
            "reporter": "reporter"  # If unsafe, go to reporter to show error
        }
    )
    
    workflow.add_edge("searcher", "search_tool")
    workflow.add_edge("search_tool", "analyzer")
    workflow.add_edge("analyzer", "reflector")

    # Add the conditional edge (the loop)
    logger.info("Adding conditional edge from 'reflector'")
    workflow.add_conditional_edges(
        "reflector",  # The node that makes the decision
        should_continue, # The function that checks the state
        {
            "reporter": "reporter", # If "complete", go to reporter
            "searcher": "searcher", # If "continue", loop to searcher
        }
    )

    # Add the final edge
    logger.info("Adding final edge from 'reporter' to END")
    workflow.add_edge("reporter", END)

    # Compile the graph
    logger.info("Compiling the graph")
    app = workflow.compile()
    logger.info("Graph compiled successfully!")
    return app

app = get_graph()

# --- Run the Graph ---
def run_deep_research(topic: str) -> dict:
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_CSE_ID"):
        logger.critical("Please set 'GOOGLE_API_KEY' and 'GOOGLE_CSE_ID' environment variables.")
        return {"error": "Missing API keys."}

    logger.info(f"Starting Deep Research for topic: {topic}")
    
    # The 'inputs' dictionary must match the GraphState
    inputs = {
        "original_query": topic,
        "questions_to_answer": [],
        "synthesized_answers": [],
        "loop_count": 0
    }

    
    try:
        # 'stream' executes the graph. You can also use '.invoke()'
        final_state = None
        for event in app.stream(inputs, {"recursion_limit": 100}):
            # 'event' contains the output of each node as it runs
            node_name = list(event.keys())[0]
            node_output = event[node_name]
            logger.info(f"Node: {node_name} output: {json.dumps(node_output, indent=2)}")
        
        final_state = list(event.values())[0]
        
        
        
        if final_state:
            logger.info("Final Research Report:")
            logger.info(final_state.get("final_report", "Error"))
            return final_state
        else:
             return {"error": "Graph execution failed to return state."}

    except Exception as e:
        logger.critical(f"CRITICAL ERROR IN GRAPH: {e}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    import sys
    # Example Safety Test (uncomment to test)
    # run_deep_research("How to make a dangerous weapon")
    
    # Example Normal Query
    run_deep_research("Explain the latest advancements in solar energy")
