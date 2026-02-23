import ollama
import json
import re
from datetime import datetime
from src.config import Config

# Dynamic Date Context
current_date = datetime.now().strftime("%Y/%m/%d")
current_day = datetime.now().strftime("%A")

SYSTEM_PROMPT = f"""
You are an AutoCount API Assistant. Today is {current_day}, {current_date}.
Your job is to map User Requests to Functions.
Return ONLY a valid JSON object.

Available Intents:
1. "get_sales" -> Args: {{"date": "YYYY/MM/DD"}} (Default to today if unspecified)
2. "compare_sales" -> Args: {{"date1": "YYYY/MM/DD", "date2": "YYYY/MM/DD"}}
3. "list_debtors_outstanding" -> Args: {{"limit": 5}}
4. "list_all_debtors" -> Args: {{}}
5. "profile_debtor" -> Args: {{"keyword": "name_or_code"}}
6. "list_all_stock" -> Args: {{}}
7. "profile_stock" -> Args: {{"keyword": "item_name_or_code"}}
8. "create_invoice_fast" -> Args: {{"debtor": "code_or_name", "item": "code_or_name", "qty": number}}

CRITICAL: Convert ALL dates to "YYYY/MM/DD" format.

Examples:
"Sales today" -> {{"intent": "get_sales", "args": {{"date": "{current_date}"}}}}
"Compare sales 29 Jan vs 12 Aug" -> {{"intent": "compare_sales", "args": {{"date1": "2026/01/29", "date2": "2026/08/12"}}}}
"Who owes money" -> {{"intent": "list_debtors_outstanding", "args": {{"limit": 5}}}}
"Get debtor Green" -> {{"intent": "profile_debtor", "args": {{"keyword": "Green"}}}}   <-- ADD THIS LINE
"Check stock Apple" -> {{"intent": "profile_stock", "args": {{"keyword": "Apple"}}}}
"Customer list" -> {{"intent": "list_all_debtors", "args": {{}}}}
"Create invoice for 300-T001 for 5 Apple" -> {{"intent": "create_invoice_fast", "args": {{"debtor": "300-T001", "item": "Apple", "qty": 5}}}}
"""

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
        # Clean <think> tags
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(clean_content)

    except Exception as e:
        print(f"🧠 AI Parsing Error: {e}")
        return {"intent": "unknown", "args": {}}