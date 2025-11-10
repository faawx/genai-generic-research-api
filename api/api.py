from fastapi import APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from deep_research.graph import run_deep_research

import logging

from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
logger.info("Initializing FastAPI app")
api = APIRouter()



# Define the request model for the API endpoint
class ResearchRequest(BaseModel):
    topic: str

# Define the root endpoint for a simple health check
@api.get("/", tags=["Health Check"])
def read_root():
    """Provides a simple status check."""
    logger.info("Health check endpoint called")
    return {"status": "API is running"}

@api.post("/do-research", tags=["Deep Research"], response_model=dict)
def do_research(request: ResearchRequest):
    """
    Takes a travel topic and returns a complete, generated itinerary.
    """
    logger.info(f"Starting deep research for topic: {request.topic}")
    
    try:
        result = run_deep_research(request.topic)
        if result.get("error"):
            logger.error(f"Deep research failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        logger.info(f"Deep research completed for topic: {request.topic}")
        return result
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# To run this API, save the files and run in your terminal:
# uvicorn main:app --reload