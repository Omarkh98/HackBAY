from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()
import re

client = OpenAI()

def clean_user_prompt(prompt: str) -> str:
    """
    Remove file paths (e.g., tools/.../*.py) from the user prompt to improve tool matching.
    """
    # Regex to remove relative paths with .py files, e.g. tools/library_license_checker/config/license_map.py
    cleaned = re.sub(r'\b[\w./-]*\.py\b', '', prompt)
    # Also remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def route_to_tool(user_prompt: str, metadata_dict: dict) -> str:
    """
    Uses GPT to select the most relevant tool based on user prompt and available tool descriptions.

    Returns:
        tool_name (str): The key of the selected tool.
    """
    tools = [
        {
            "name": name,
            "description": meta.get("description", ""),
            "keywords": meta.get("keywords", [])
        }
        for name, meta in metadata_dict.items()
    ]

    # Clean the user prompt to remove file paths
    cleaned_prompt = clean_user_prompt(user_prompt)

    if any(kw in cleaned_prompt for kw in ["compliance", "guideline", "coding standard", "best practice", "style violation"]):
        return "internal_guideline_compliance_checker"
    
    if any(kw in cleaned_prompt for kw in ["license", "licensing", "dependency", "third-party"]):
        return "library_license_checker"

    messages = [
        {"role": "system", "content":
            "You are an AI assistant that selects the best tool for a given developer task. "
            "Each tool is described by its purpose and associated keywords. Choose the tool whose "
            "intent best matches the user's request, based on meaning and context."},
        {"role": "user", 
            "content": f"""User request: {cleaned_prompt}

Available tools:
{json.dumps(tools, indent=2)}

Which tool should be used? Reply with only the tool's name exactly as listed."""}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or gpt-3.5-turbo
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content.strip()