"""
Simple response processing utilities for LLM responses

This module contains utilities for cleaning and extracting content from
LLM responses, extracted from gemini.py for better separation of concerns.
"""

import json
from typing import Dict, Any


class ResponseProcessor:
    """Simple utilities for processing LLM responses"""
    
    @staticmethod
    def extract_json(response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response text
        
        This handles cases where the LLM includes extra text around the JSON
        """
        # Find the first { ... } block
        start = response_text.find("{")
        end = response_text.rfind("}")
        
        if start != -1 and end != -1 and end > start:
            raw_json = response_text[start:end+1]
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError:
                pass
        
        # Fallback: return empty dict
        return {}
    
    @staticmethod
    def extract_mermaid_code(response_text: str) -> str:
        """
        Extract Mermaid diagram code from LLM response text
        
        This handles cases where the LLM includes markdown formatting or extra text
        """
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
    
    @staticmethod
    def clean_markdown_response(response_text: str) -> str:
        """
        Clean markdown response by removing any wrapper formatting
        
        Some LLMs wrap responses in code blocks, this removes them
        """
        text = response_text.strip()
        
        # Remove markdown code fences if present
        if text.startswith('```') and text.endswith('```'):
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines).strip()
        
        return text 