from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api import api as api_router
import logging

from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

logger.info("Starting application")
app = FastAPI(
    title="Multi-node Deep Research Workflow API",
    description="An API to undertake deep research using a team of AI agents.",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) ---
# This allows your frontend (running on a different port) to communicate with this API.
origins = [
    "http://localhost:5173",  # Default port for Vue 3 (Vite)
    "http://localhost:8000",  # Default port for Vue 2 (Vue CLI)
    "http://localhost",
]
logger.info(f"Adding CORS middleware with origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API router
logger.info("Mounting API routers")

app.include_router(api_router, prefix="/api")