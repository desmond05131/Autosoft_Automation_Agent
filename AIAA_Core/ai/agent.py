import ollama
import json
from src.config import Config

# Prompt engineering to ensure AI returns strictly JSON
SYSTEM_PROMPT = """
You are an AutoCount Assistant Router. 
Identify the user's intent and extract parameters.
Return ONLY valid JSON. No markdown.

Available Tools:
1. check_stock (args: item_code)
2. check_debtor_info (args: debtor_name_or_code)
3. check_top_debtors (args: limit)
4. check_sales (args: date_text (e.g. "today", "2026-01-29"))

Example Output:
{"intent": "check_stock", "args": {"item_code": "IPHONE"}}
"""

def interpret_intent(user_text):
    """Sends prompt to Ollama and parses JSON response."""
    try:
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_text},
            ]
        )
        
        content = response['message']['content']
        # Clean potential markdown code blocks
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"🧠 AI Error: {e}")
        return {"intent": "unknown", "args": {}}
