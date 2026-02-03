# llm.py

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL =  os.getenv("MODEL")

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "core", "prompt.txt")


def load_system_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ prompt.txt cannot installed: {e}")
        return "You are Jarvis, a helpful AI assistant."


SYSTEM_PROMPT = load_system_prompt()


def safe_json_parse(text: str) -> dict | None:
    if not text:
        return None

    text = text.strip()

    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        except:
            pass
    elif "```" in text:
        try:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()
        except:
            pass

    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"The error text: {text[:200]}")
        return None


def get_llm_output(user_text: str, memory_block: dict = None) -> dict:

    if not user_text or not user_text.strip():
        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": "Sir, I didn't catch that.",
            "memory_update": None
        }

    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY couldn't found!")
        return {
            "intent": "chat",
            "parameters": {},
            "text": "API key is missing, Sir.",
            "needs_clarification": False,
            "memory_update": None
        }

    # Memory'yi string'e çevir
    memory_str = ""
    if memory_block:
        memory_str = "\n".join(f"{k}: {v}" for k, v in memory_block.items())

    user_prompt = f"""User message: "{user_text}"

Known user memory:
{memory_str if memory_str else "No memory available"}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 500
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Jarvis-Assistant"
    }

    try:
        
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            print(f"❌ API Hatası: {response.text}")
            return {
                "intent": "chat",
                "parameters": {},
                "text": f"Sir, API error: {response.status_code}",
                "needs_clarification": False,
                "memory_update": None
            }

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # JSON parse et
        parsed = safe_json_parse(content)

        if parsed:
            return {
                "intent": parsed.get("intent", "chat"),
                "parameters": parsed.get("parameters", {}),
                "needs_clarification": parsed.get("needs_clarification", False),
                "text": parsed.get("text"),
                "memory_update": parsed.get("memory_update")
            }

        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": content,
            "memory_update": None
        }

    except requests.exceptions.Timeout:
        print("❌ API timeout!")
        return {
            "intent": "chat",
            "text": "Sir, the connection timed out.",
            "parameters": {},
            "needs_clarification": False,
            "memory_update": None
        }
    
    except Exception as e:
        print(f"❌ LLM ERROR: {e}")
        return {
            "intent": "chat",
            "text": "Sir, I encountered a system error.",
            "parameters": {},
            "needs_clarification": False,
            "memory_update": None
        }