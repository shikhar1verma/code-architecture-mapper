"""
Clean Gemini LLM interface

This module provides the main interface for LLM operations with clean separation of concerns.
All retry logic has been moved to retry_handler.py and response processing to response_utils.py.
"""

from typing import Type, Any
from pydantic import BaseModel, ValidationError

from backend.llm.retry_handler import _retry_handler, GeminiQuotaExhaustedError, GeminiAPIError
from backend.llm.response_utils import ResponseProcessor
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def generate_markdown(system_prompt: str, user_prompt: str) -> str:
    """
    Generate markdown content using Gemini with fallback models
    
    Args:
        system_prompt: System instructions for the LLM
        user_prompt: User's actual prompt
        
    Returns:
        Generated markdown content as string
    """
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = _retry_handler.call_with_fallback(combined_prompt)
        return ResponseProcessor.clean_markdown_response(response)
        
    except GeminiQuotaExhaustedError:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in generate_markdown: {e}")
        raise GeminiAPIError(f"Unexpected API error: {str(e)}")


def generate_json(system_prompt: str, user_prompt: str, schema: Type[BaseModel]) -> Any:
    """
    Generate JSON content using Gemini with fallback models and validation
    
    Args:
        system_prompt: System instructions for the LLM
        user_prompt: User's actual prompt  
        schema: Pydantic model for validation
        
    Returns:
        Validated object matching the schema
    """
    # First try with regular prompt
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = _retry_handler.call_with_fallback(combined_prompt)
        data = ResponseProcessor.extract_json(response_text)
        return schema.model_validate(data)
        
    except ValidationError:
        # Second try: ask to fix format
        logger.warning("🔄 JSON validation failed, trying with format correction prompt...")
        fix_prompt = f"{system_prompt} Return ONLY valid JSON matching schema.\n\nThe previous output was invalid. Fix it.\n\n{user_prompt}"
        
        try:
            fix_response_text = _retry_handler.call_with_fallback(fix_prompt)
            data2 = ResponseProcessor.extract_json(fix_response_text)
            return schema.model_validate(data2)
            
        except ValidationError as ve:
            logger.error(f"❌ JSON validation failed after format correction: {ve}")
            raise GeminiAPIError(f"Failed to generate valid JSON after retry: {str(ve)}")
            
    except GeminiQuotaExhaustedError:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in generate_json: {e}")
        raise GeminiAPIError(f"Unexpected API error: {str(e)}")


def generate_mermaid_correction(system_prompt: str, user_prompt: str) -> str:
    """
    Generate corrected Mermaid diagram code using Gemini with fallback models
    
    Args:
        system_prompt: System instructions for the LLM
        user_prompt: User's actual prompt containing the broken diagram
        
    Returns:
        Corrected Mermaid diagram code
    """
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = _retry_handler.call_with_fallback(combined_prompt)
        
        # Clean the response - extract only the Mermaid code
        corrected_code = ResponseProcessor.extract_mermaid_code(response_text)
        
        if not corrected_code:
            logger.warning("⚠️ No valid Mermaid code found in response, returning original response")
            return response_text.strip()
            
        return corrected_code
        
    except GeminiQuotaExhaustedError:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in generate_mermaid_correction: {e}")
        raise GeminiAPIError(f"Unexpected API error: {str(e)}")


# Re-export exceptions for backward compatibility
__all__ = [
    'generate_markdown',
    'generate_json', 
    'generate_mermaid_correction',
    'GeminiQuotaExhaustedError',
    'GeminiAPIError'
] 