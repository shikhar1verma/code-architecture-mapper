"""
Simple retry and fallback handler for Gemini API calls

This module handles the retry logic and model fallback mechanism,
extracted from gemini.py for better separation of concerns.
"""

import random
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
from typing import Callable, Any, Optional, List

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_FALLBACK_ORDER,
    RETRY_MIN_DELAY_SECONDS,
    RETRY_MAX_DELAY_SECONDS,
    MAX_RETRIES_PER_MODEL
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiQuotaExhaustedError(Exception):
    """Raised when all Gemini models have exhausted their quotas"""
    def __init__(self, attempted_models: List[str] = None):
        self.attempted_models = attempted_models or []
        message = "All Gemini API models have exhausted their quotas. This is a demo system using free tier quotas."
        if attempted_models:
            message += f" Attempted models: {', '.join(attempted_models)}"
        super().__init__(message)


class GeminiAPIError(Exception):
    """Raised when Gemini API encounters other errors"""
    pass


class RetryHandler:
    """Simple handler for API retries and model fallbacks"""
    
    def __init__(self):
        # Configure API
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Cache for model instances to avoid recreating them
        self._model_cache = {}
    
    def get_model(self, model_name: str):
        """Get or create a model instance"""
        if model_name not in self._model_cache:
            self._model_cache[model_name] = genai.GenerativeModel(model_name)
        return self._model_cache[model_name]
    
    def random_delay(self):
        """Generate random delay between retries"""
        delay = random.uniform(RETRY_MIN_DELAY_SECONDS, RETRY_MAX_DELAY_SECONDS)
        logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
        time.sleep(delay)
    
    def call_with_fallback(self, prompt: str, response_handler: Optional[Callable] = None) -> Any:
        """
        Call Gemini API with fallback models and retry mechanism
        
        Args:
            prompt: The prompt to send to the model
            response_handler: Optional function to process the response
            
        Returns:
            Response from successful model call
        """
        attempted_models = []
        
        for model_name in GEMINI_MODEL_FALLBACK_ORDER:
            attempted_models.append(model_name)
            logger.info(f"🤖 Trying model: {model_name}")
            
            model = self.get_model(model_name)
            
            for attempt in range(MAX_RETRIES_PER_MODEL):
                try:
                    if attempt > 0:
                        logger.info(f"🔄 Retry {attempt + 1}/{MAX_RETRIES_PER_MODEL} for {model_name}")
                        self.random_delay()
                    
                    logger.debug(f"🤖 Sending prompt to {model_name}: {prompt[:100]}...")
                    response = model.generate_content(prompt)
                    
                    if response_handler:
                        return response_handler(response)
                    else:
                        return response.text or ""
                    
                except ResourceExhausted as e:
                    logger.warning(f"🚫 Model {model_name} quota exhausted (attempt {attempt + 1})")
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        self.random_delay()
                    break  # Move to next model instead of retrying
                    
                except (InternalServerError, ServiceUnavailable) as e:
                    logger.warning(f"🔧 Model {model_name} temporarily unavailable (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        self.random_delay()
                    else:
                        logger.error(f"❌ Model {model_name} failed after {MAX_RETRIES_PER_MODEL} attempts")
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Unexpected error with model {model_name} (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        self.random_delay()
                    else:
                        logger.error(f"❌ Model {model_name} failed after {MAX_RETRIES_PER_MODEL} attempts")
                        break
        
        # If we get here, all models failed
        logger.error(f"💥 All models exhausted. Attempted: {attempted_models}")
        raise GeminiQuotaExhaustedError(attempted_models)


# Global instance for backward compatibility
_retry_handler = RetryHandler() 