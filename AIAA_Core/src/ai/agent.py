import ollama
import json
import re
from src.config import Config

# System prompt optimized for DeepSeek to force JSON
SYSTEM_PROMPT = """
You are an API Router. You MUST return ONLY a JSON object. 
Do not output any reasoning, markdown formatting, or explanations.
Just the raw JSON.

User Intent Schema:
{
  "intent": "check_stock" | "check_debtor_info" | "check_top_debtors" | "check_sales" | "unknown",
  "args": { ... }
}

Examples:
User: "Check stock for iPhone"
JSON: {"intent": "check_stock", "args": {"item_code": "iPhone"}}

User: "Top 5 debtors"
JSON: {"intent": "check_top_debtors", "args": {"limit": 5}}

User: "Sales for today"
JSON: {"intent": "check_sales", "args": {"date_text": "today"}}
"""

def clean_deepseek_response(text):
    """Removes <think> tags and finds the first valid JSON object"""
    # 1. Remove <think>...</think> sections if present
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # 2. Try to find JSON inside code blocks ```json ... ```
    json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_block:
        return json_block.group(1)
        
    # 3. If no blocks, try to find the first { ... } structure
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
        
    return text

def interpret_intent(user_text):
    try:
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_text},
            ]
        )
        
        raw_content = response['message']['content']
        cleaned_content = clean_deepseek_response(raw_content)
        
        # Parse JSON
        return json.loads(cleaned_content)
        
    except json.JSONDecodeError:
        print(f"❌ JSON Parse Error. Raw AI Output: {raw_content}")
        return {"intent": "unknown", "args": {}}
    except Exception as e:
        print(f"🧠 AI Critical Error: {e}")
        return {"intent": "unknown", "args": {}}