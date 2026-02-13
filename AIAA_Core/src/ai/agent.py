import ollama
import json
import re
from src.config import Config

SYSTEM_PROMPT = """
You are an AutoCount API Assistant.
Your job is to map user queries to specific TOOLS.
Return ONLY a valid JSON object. NO conversational text. NO <think> tags.

Available Tools:
1. "check_stock" -> Args: {"item_code": "extracted_item_name_or_code"}
2. "check_debtor_info" -> Args: {"name": "extracted_customer_name"}
3. "list_top_debtors" -> Args: {"limit": 5} (Default to 5 if not specified)
4. "check_sales" -> Args: {"date_text": "today" or "yesterday" or "YYYY-MM-DD"}
5. "list_customers" -> Args: {"limit": 10}
6. "list_stock" -> Args: {"limit": 20}

Examples:
User: "Check stock for iPhone 15" -> JSON: {"intent": "check_stock", "args": {"item_code": "iPhone 15"}}
User: "Who owes us money?" -> JSON: {"intent": "list_top_debtors", "args": {"limit": 5}}
User: "Sales for today" -> JSON: {"intent": "check_sales", "args": {"date_text": "today"}}
User: "Info on debtor Green" -> JSON: {"intent": "check_debtor_info", "args": {"name": "Green"}}
User: "Show me customer list" -> JSON: {"intent": "list_customers", "args": {"limit": 10}}
"""

def interpret_intent(user_text):
    """Parses user natural language into structured JSON intent."""
    try:
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_text},
            ]
        )
        
        raw_content = response['message']['content']
        
        # 1. Clean DeepSeek <think> tags
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        
        # 2. Extract JSON block if wrapped in markdown
        json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            # Try parsing the whole string
            return json.loads(clean_content)

    except Exception as e:
        print(f"🧠 AI Parsing Error: {e}")
        return {"intent": "unknown", "args": {}}