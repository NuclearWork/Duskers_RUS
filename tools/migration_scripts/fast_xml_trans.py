import os
import json
import time
import xml.etree.ElementTree as ET
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1].strip("\"'")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(model_name="gemini-3.5-flash-lite")

with open('Exported_EN/resources_text_en.json', 'r', encoding='utf-8') as f:
    text_assets = json.load(f)
with open('Translation/ru_database.json', 'r', encoding='utf-8') as f:
    ru_db = json.load(f)

def translate_batch(strings):
    sys_prompt = "Ты профессиональный переводчик видеоигр. Переведи текст на русский язык. Сохраняй все спецсимволы, табы (&#x9;) и переносы (\\n).\n"
    prompt = sys_prompt + "Верни ТОЛЬКО валидный JSON массив строк (без маркдауна и без комментариев):\n" + json.dumps(strings, ensure_ascii=False)
    for _ in range(3):
        try:
            resp = model.generate_content(prompt)
            txt = resp.text.strip()
            if txt.startswith("```json"): txt = txt[7:-3]
            elif txt.startswith("```"): txt = txt[3:-3]
            res = json.loads(txt.strip())
            if len(res) == len(strings): return res
        except Exception as e:
            print(f"Error: {e}", flush=True)
            time.sleep(2)
    return strings

xml_str = text_assets.get("CommandDefinitions")
wrapped_xml = f"<root>{xml_str}</root>"
root = ET.fromstring(wrapped_xml)

nodes_to_translate = []
strings_to_translate = []

for elem in root.iter():
    for attr in ['description', 'message']:
        val = elem.get(attr)
        if val and len(val.strip()) > 1:
            nodes_to_translate.append((elem, attr))
            strings_to_translate.append(val)

print(f"Translating {len(strings_to_translate)} strings from CommandDefinitions...", flush=True)

translated_strings = []
batch_size = 40
for i in range(0, len(strings_to_translate), batch_size):
    batch = strings_to_translate[i:i+batch_size]
    print(f"  Batch {i//batch_size + 1}/{(len(strings_to_translate)+batch_size-1)//batch_size}...", flush=True)
    translated_strings.extend(translate_batch(batch))
    time.sleep(1)

for i, (elem, attr) in enumerate(nodes_to_translate):
    if i < len(translated_strings):
        elem.set(attr, translated_strings[i])

new_xml = ET.tostring(root, encoding='unicode', method='xml')
new_xml = new_xml.replace('<root>', '').replace('</root>', '').strip()
ru_db["res::CommandDefinitions"] = new_xml

with open('Translation/ru_database.json', 'w', encoding='utf-8') as f:
    json.dump(ru_db, f, ensure_ascii=False, indent=2)

print("CommandDefinitions translated successfully!", flush=True)
