from datetime import datetime
import json
from typing import Dict, Any

# Initialize token usage tracking
token_usage = {
    "records": [],
    "total_usage": {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "calls": 0
    }
}

def record_token_usage(content: str, instruction: str, model: str, response) -> None:
    """
    Record token usage, input, output, and model information.
    
    Args:
        content: The input content
        instruction: The system instruction
        model: The model used
        response: The model's response object
    """
    global token_usage
    
    # Extract response text
    response_text = ""
    if hasattr(response, 'text'):
        response_text = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        response_text = response.candidates[0].content.parts[0].text
    
    # Extract token usage if available
    usage_data = {}
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        usage_data = {
            "prompt_tokens": usage.prompt_token_count if hasattr(usage, 'prompt_token_count') else 0,
            "completion_tokens": usage.candidates_token_count if hasattr(usage, 'candidates_token_count') else 0,
            "total_tokens": usage.total_token_count if hasattr(usage, 'total_token_count') else 0
        }
    
    # Create record
    record = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "content_length": len(content),
        "instruction_length": len(instruction),
        "response_length": len(response_text),
        "usage": usage_data
    }
    
    # Add record to token_usage
    token_usage["records"].append(record)
    
    # Update total counts
    token_usage["total_usage"]["calls"] += 1
    if "prompt_tokens" in usage_data:
        token_usage["total_usage"]["prompt_tokens"] += usage_data["prompt_tokens"]
    if "completion_tokens" in usage_data:
        token_usage["total_usage"]["completion_tokens"] += usage_data["completion_tokens"]
    if "total_tokens" in usage_data:
        token_usage["total_usage"]["total_tokens"] += usage_data["total_tokens"]

def save_token_usage(filepath="token_usage_log.json"):
    """
    Save token usage data to a JSON file.
    
    Args:
        filepath: Path to save the JSON file
    """
    with open(filepath, 'w') as f:
        json.dump(token_usage, f, indent=4)
    print(f"Token usage saved to {filepath}")
    
def display_token_usage_summary():
    """
    Display a summary of token usage.
    """
    print(f"Total API calls: {token_usage['total_usage']['calls']}")
    print(f"Total tokens used: {token_usage['total_usage']['total_tokens']}")
    print(f"Total prompt tokens: {token_usage['total_usage']['prompt_tokens']}")
    print(f"Total completion tokens: {token_usage['total_usage']['completion_tokens']}") 