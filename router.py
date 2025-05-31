# core/router.py

from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()
import os

client = OpenAI()

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
        }
        for name, meta in metadata_dict.items()
    ]

    messages = [
        {"role": "system", "content": "You are an AI assistant that selects the best tool for a given developer task."},
        {"role": "user", "content": f"""User request: {user_prompt}

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