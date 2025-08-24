import json
import random
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
from typing import Type, Any
from pydantic import BaseModel, ValidationError
from backend.config import (
    GEMINI_API_KEY, 
    GEMINI_MODEL,
    GEMINI_MODEL_FALLBACK_ORDER,
    RETRY_MIN_DELAY_SECONDS,
    RETRY_MAX_DELAY_SECONDS,
    MAX_RETRIES_PER_MODEL
)

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)

# Cache for model instances to avoid recreating them
_model_cache = {}

def _get_model(model_name: str):
    """Get or create a model instance"""
    if model_name not in _model_cache:
        _model_cache[model_name] = genai.GenerativeModel(model_name)
    return _model_cache[model_name]


class GeminiQuotaExhaustedError(Exception):
    """Raised when all Gemini models have exhausted their quotas"""
    def __init__(self, attempted_models: list = None):
        self.attempted_models = attempted_models or []
        message = "All Gemini API models have exhausted their quotas. This is a demo system using free tier quotas."
        if attempted_models:
            message += f" Attempted models: {', '.join(attempted_models)}"
        super().__init__(message)


class GeminiAPIError(Exception):
    """Raised when Gemini API encounters other errors"""
    pass


def _random_delay():
    """Generate random delay between retries"""
    delay = random.uniform(RETRY_MIN_DELAY_SECONDS, RETRY_MAX_DELAY_SECONDS)
    print(f"⏳ Waiting {delay:.1f}s before retry...")
    time.sleep(delay)


def _call_with_fallback(prompt: str, response_handler=None):
    """
    Call Gemini API with fallback models and retry mechanism
    
    Args:
        prompt: The prompt to send to the model
        response_handler: Optional function to process the response (for JSON parsing, etc.)
    
    Returns:
        Response from successful model call
    """
    attempted_models = []
    
    for model_name in GEMINI_MODEL_FALLBACK_ORDER:
        attempted_models.append(model_name)
        print(f"🤖 Trying model: {model_name}")
        
        model = _get_model(model_name)
        
        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                if attempt > 0:
                    print(f"🔄 Retry {attempt + 1}/{MAX_RETRIES_PER_MODEL} for {model_name}")
                    _random_delay()
                print('\n🤖 Prompt: ', prompt, '\n')
                response = model.generate_content(prompt)
                
                if response_handler:
                    return response_handler(response)
                else:
                    return response.text or ""
                
            except ResourceExhausted as e:
                print(f"🚫 Model {model_name} quota exhausted (attempt {attempt + 1})")
                if attempt < MAX_RETRIES_PER_MODEL - 1:
                    _random_delay()
                break  # Move to next model instead of retrying
                
            except (InternalServerError, ServiceUnavailable) as e:
                print(f"🔧 Model {model_name} temporarily unavailable (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES_PER_MODEL - 1:
                    _random_delay()
                else:
                    print(f"❌ Model {model_name} failed after {MAX_RETRIES_PER_MODEL} attempts")
                    break
                    
            except Exception as e:
                print(f"❌ Unexpected error with model {model_name} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES_PER_MODEL - 1:
                    _random_delay()
                else:
                    print(f"❌ Model {model_name} failed after {MAX_RETRIES_PER_MODEL} attempts")
                    break
    
    # If we get here, all models failed
    print(f"💥 All models exhausted. Attempted: {attempted_models}")
    raise GeminiQuotaExhaustedError(attempted_models)


def generate_markdown(system_prompt: str, user_prompt: str) -> str:
    """Generate markdown content using Gemini with fallback models"""
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        return _call_with_fallback(combined_prompt)
    except GeminiQuotaExhaustedError:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in generate_markdown: {e}")
        raise GeminiAPIError(f"Unexpected API error: {str(e)}")


def generate_json(system_prompt: str, user_prompt: str, schema: Type[BaseModel]) -> Any:
    """Generate JSON content using Gemini with fallback models"""
    
    # First try with regular prompt
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = _call_with_fallback(combined_prompt)
        data = _extract_json(response_text)
        return schema.model_validate(data)
    except ValidationError:
        # Second try: ask to fix format
        print("🔄 JSON validation failed, trying with format correction prompt...")
        fix_prompt = f"{system_prompt} Return ONLY valid JSON matching schema.\n\nThe previous output was invalid. Fix it.\n\n{user_prompt}"
        try:
            fix_response_text = _call_with_fallback(fix_prompt)
            data2 = _extract_json(fix_response_text)
            return schema.model_validate(data2)
        except ValidationError as ve:
            print(f"❌ JSON validation failed after format correction: {ve}")
            raise GeminiAPIError(f"Failed to generate valid JSON after retry: {str(ve)}")
    except GeminiQuotaExhaustedError:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in generate_json: {e}")
        raise GeminiAPIError(f"Unexpected API error: {str(e)}")


def generate_mermaid_correction(system_prompt: str, user_prompt: str) -> str:
    """Generate corrected Mermaid diagram code using Gemini with fallback models"""
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = _call_with_fallback(combined_prompt)
        
        # Clean the response - extract only the Mermaid code
        corrected_code = _extract_mermaid_code(response_text)
        
        if not corrected_code:
            print("⚠️ No valid Mermaid code found in response, returning original response")
            return response_text.strip()
            
        return corrected_code
        
    except GeminiQuotaExhaustedError:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in generate_mermaid_correction: {e}")
        raise GeminiAPIError(f"Unexpected API error: {str(e)}")


def _extract_mermaid_code(response_text: str) -> str:
    """Extract Mermaid code from the response text"""
    lines = response_text.strip().split('\n')
    
    # Look for flowchart start
    for i, line in enumerate(lines):
        if line.strip().startswith('flowchart'):
            # Found the start, take everything from here
            mermaid_lines = lines[i:]
            
            # Clean up any markdown formatting or extra text
            cleaned_lines = []
            for line in mermaid_lines:
                # Skip markdown code block markers
                if line.strip() in ['```', '```mermaid']:
                    continue
                cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines).strip()
    
    # Fallback: return the whole response if no flowchart found
    return response_text.strip()


def _extract_json(s: str):
    # naive: find the first { ... } block
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = s[start:end+1]
        try:
            return json.loads(raw)
        except Exception:
            pass
    # fallback empty
    return {} 