import json
import google.generativeai as genai
from typing import Type, Any
from pydantic import BaseModel, ValidationError
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)


def generate_markdown(system_prompt: str, user_prompt: str) -> str:
    # Combine system and user prompts into a single message for Gemini
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    resp = _model.generate_content(combined_prompt)
    return resp.text or ""


def generate_json(system_prompt: str, user_prompt: str, schema: Type[BaseModel]) -> Any:
    # Try to coerce the first fenced JSON if present
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    resp = _model.generate_content(combined_prompt)
    txt = resp.text or "{}"
    data = _extract_json(txt)
    try:
        obj = schema.model_validate(data)
        return obj
    except ValidationError:
        # second try: ask to fix format
        fix_prompt = f"{system_prompt} Return ONLY valid JSON matching schema.\n\nThe previous output was invalid. Fix it.\n\n{user_prompt}"
        fix = _model.generate_content(fix_prompt)
        data2 = _extract_json(fix.text or "{}")
        return schema.model_validate(data2)


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