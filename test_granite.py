import json
import urllib.request
import urllib.error

def translate_text(text):
    url = "http://localhost:11434/api/generate"
    system_prompt = """You are a professional video game translator. Translate the following text into Russian.
RULES:
1. Output ONLY the translated text, without any quotes, explanations, or introductory words.
2. Do NOT translate game commands such as: navigate, scan, generator, pry, tow, motion, open, close.
3. Preserve all formatting, exactly as in the original: {0}, {1}, \n, <color=white>.
GLOSSARY:
- Scrap -> Лом
- Drone -> Дрон
- Air Lock -> Шлюз
- Upgrade -> Модуль / Улучшение
- Salvage -> Сбор / Утилизация
"""
    data = {
        "model": "granite4.2:3b",
        "prompt": text,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get("response", "").strip()
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    test_strings = [
        "Welcome to Drone Operator Training",
        "Type 'navigate 1 r3' to send Drone 1 to Room 3",
        "Upgrade used - will suffer wear and tear at end of mission: {0}",
        "Warning: ship upgrade detected that can be salvaged.",
        "You might need power to continue, consider piloting drone 2 into Room 2 and typing 'generator'"
    ]

    print("Testing granite4.2:3b via Ollama...\n")
    for s in test_strings:
        print(f"EN: {s}")
        print(f"RU: {translate_text(s)}\n{'-'*50}")
