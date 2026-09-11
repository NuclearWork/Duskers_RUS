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

XML_KEYS = [
    "CommandDefinitions", "DungeonDefinitions", "Tutorial", 
    "DroneUpgradeLibrary", "DVPDefinitions", "ShipNames"
]

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
            print(f"Error: {e}")
            time.sleep(5)
    return strings # Fallback to original if failed

for key_name in XML_KEYS:
    db_key = f"res::{key_name}"
    if db_key in ru_db:
        continue
        
    xml_str = text_assets.get(key_name)
    if not xml_str: continue
    
    print(f"Processing {key_name}...")
    
    try:
        wrapped_xml = f"<root>{xml_str}</root>"
        root = ET.fromstring(wrapped_xml)
        
        # Collect nodes to translate
        nodes_to_translate = []
        strings_to_translate = []
        
        # Attributes to check
        attrs = ['description', 'message', 'text', 'name']
        
        for elem in root.iter():
            for attr in attrs:
                val = elem.get(attr)
                if val and len(val.strip()) > 2 and not val.startswith("&#x9;") and "{" not in val:
                    # Actually, message often starts with &#x9; (tab). We should translate it!
                    pass
                
                # Let's just collect all 'description' and 'message'
                if attr in ['description', 'message', 'text'] and val and len(val.strip()) > 1:
                    nodes_to_translate.append((elem, attr))
                    strings_to_translate.append(val)
                    
        print(f"Found {len(strings_to_translate)} strings.")
        
        # Translate in batches of 20
        translated_strings = []
        batch_size = 20
        for i in range(0, len(strings_to_translate), batch_size):
            batch = strings_to_translate[i:i+batch_size]
            print(f"  Batch {i//batch_size + 1}/{(len(strings_to_translate)+batch_size-1)//batch_size}...")
            trans_batch = translate_batch(batch)
            translated_strings.extend(trans_batch)
            time.sleep(2)
            
        # Inject back
        for i, (elem, attr) in enumerate(nodes_to_translate):
            if i < len(translated_strings):
                elem.set(attr, translated_strings[i])
                
        # Generate new XML string
        new_xml = ET.tostring(root, encoding='unicode', method='xml')
        # Remove <root> and </root>
        new_xml = new_xml.replace('<root>', '').replace('</root>', '').strip()
        
        ru_db[db_key] = new_xml
        print(f"Saved {key_name} to DB!")
        
        with open('Translation/ru_database.json', 'w', encoding='utf-8') as f:
            json.dump(ru_db, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Failed to process {key_name}: {e}")

print("Done!")
