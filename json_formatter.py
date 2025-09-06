"""
JSON formatting utilities for ensuring Claude responses are valid JSON
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that might contain markdown, code blocks, or explanations.
    
    Args:
        text: Raw text that might contain JSON
        
    Returns:
        Valid JSON string
    """
    # First, try to parse the entire text as JSON
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    # Look for ```json blocks first, then generic ``` blocks
    patterns = [
        r'```json\s*\n?([\s\S]*?)\n?```',
        r'```\s*\n?([\s\S]*?)\n?```',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for match in matches:
            try:
                # Validate it's proper JSON
                json.loads(match.strip())
                return match.strip()
            except json.JSONDecodeError:
                continue
    
    # Try to find raw JSON objects or arrays
    # Look for content between outermost { } or [ ]
    json_object_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\})*)*\}'
    json_array_pattern = r'\[(?:[^\[\]]|(?:\[(?:[^\[\]]|(?:\[[^\[\]]*\])*)*\])*)*\]'
    
    for pattern in [json_object_pattern, json_array_pattern]:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # Validate it's proper JSON
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
    
    # If we still can't find valid JSON, create a JSON object from the text
    logger.warning(f"Could not extract valid JSON from response, wrapping in object")
    return json.dumps({
        "response": text,
        "_note": "Original response was not valid JSON"
    }, ensure_ascii=False)


def ensure_json_response(text: str, schema: dict = None) -> str:
    """
    Ensure the response is valid JSON that conforms to expected format.
    
    Args:
        text: Raw response text
        schema: Optional schema hint for structuring the response
        
    Returns:
        Valid JSON string
    """
    json_str = extract_json_from_text(text)
    
    # If we have a schema hint and the response doesn't match,
    # try to restructure it
    if schema and "_graphiti_schema" in str(schema):
        try:
            data = json.loads(json_str)
            # Check if response is wrapped in our fallback format
            if "_note" in data and "response" in data:
                # Try to extract structured data from the response text
                response_text = data["response"]
                # This is where we could apply schema-specific extraction
                # For now, we'll just return the JSON as is
        except Exception:
            pass
    
    return json_str


def create_json_instruction(schema: dict = None) -> str:
    """
    Create instruction text to append to prompts for JSON formatting.
    
    Args:
        schema: Optional schema to include in instructions
        
    Returns:
        Instruction text
    """
    base_instruction = """
You must respond with valid JSON only. Do not include any explanations, markdown formatting, or text outside the JSON.
Your entire response must be parseable by JSON.parse().
"""
    
    if schema:
        base_instruction += f"\nThe JSON should conform to this structure: {json.dumps(schema, indent=2)}"
    
    return base_instruction