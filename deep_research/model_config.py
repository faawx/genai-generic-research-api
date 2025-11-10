import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from a .env file
load_dotenv()

# --- Model Configuration ---
# Default model parameters
GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.8
DEFAULT_TOP_P = 1
DEFAULT_TOP_K = 32
DEFAULT_MAX_OUTPUT_TOKENS = 2048

# Safety settings (adjust as needed)
# For more details, see: https://ai.google.dev/docs/safety_guidelines
DEFAULT_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

def configure_gemini_model(
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    top_k: int = DEFAULT_TOP_K,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    safety_settings: list = DEFAULT_SAFETY_SETTINGS
):
    """
    Configures and returns a Gemini GenerativeModel instance with specified parameters.
    """
    try:
        logger.info("Configuring Gemini model with centralized settings")
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_output_tokens,
            },
            safety_settings=safety_settings
        )
        logger.info("Gemini model configured successfully with centralized settings")
        return model
    except KeyError:
        logger.error("GOOGLE_API_KEY environment variable not set. Please set it in your .env file.")
        return None
    except Exception as e:
        logger.error(f"Failed to configure Gemini model: {e}", exc_info=True)
        return None

# Initialize the model when this module is imported
model = configure_gemini_model()
