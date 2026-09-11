import os
import json
import time
import re
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
    res = json.load(f)

with open('Translation/ru_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

SKIP_FILES = {
    'DefaultGameBoard', 'ships_log_directory', 'DroneNames', 'GalaxyNames', 
    'OutpostNames', 'SystemNames', 'DronePresets', 'DVPDefinitions', 
    'DungeonDefinitions', 'CommandDefinitions'
}

cyr_re = re.compile(r'[а-яА-ЯёЁ]')

to_translate = []
for k, v in res.items():
    if k in SKIP_FILES or not isinstance(v, str) or len(v.strip()) < 5:
        continue
    db_key = f'res::{k}'
    if db_key not in db:
        to_translate.append((k, v))
    else:
        val = db[db_key]
        if not cyr_re.search(val) and len(v.strip()) > 10:
            to_translate.append((k, v))

print(f"Total files to translate: {len(to_translate)}", flush=True)

def translate_batch(batch_items):
    # batch_items is list of (filename, text)
    prompt = """Ты — профессиональный переводчик научно-фантастической игры Duskers.
Переведи бортовые журналы, сообщения экипажа, диалоги ИИ и системные отчеты на русский язык.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Сохраняй в точности все технические теги и команды: <color=...>, </color>, [YN#...], [begin], [end of file], {/ и }.
2. Не переводи ссылки внутри [YN#Y=file1:N=file2] — имена файлов должны остаться английскими!
3. Сохраняй переносы строк и отступы (табуляции).
4. Передавай мрачную, сухую атмосферу брошенных космических кораблей.

Входные данные — JSON-объект {имя_файла: текст}.
Верни ТОЛЬКО валидный JSON-объект {имя_файла: переведенный_текст} без маркдауна и лишних слов:
"""
    input_dict = {k: v for k, v in batch_items}
    prompt += json.dumps(input_dict, ensure_ascii=False)

    for attempt in range(3):
        try:
            resp = model.generate_content(prompt)
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:-3]
            elif txt.startswith("```"):
                txt = txt[3:-3]
            result = json.loads(txt.strip())
            if isinstance(result, dict) and len(result) == len(batch_items):
                return result
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}", flush=True)
            time.sleep(5)
    return None

BATCH_SIZE = 4
total_batches = (len(to_translate) + BATCH_SIZE - 1) // BATCH_SIZE

for b_idx in range(total_batches):
    batch = to_translate[b_idx * BATCH_SIZE : (b_idx + 1) * BATCH_SIZE]
    print(f"[{b_idx+1}/{total_batches}] Translating: {[x[0] for x in batch]}...", flush=True)
    
    translated_dict = translate_batch(batch)
    if translated_dict:
        for k, ru_text in translated_dict.items():
            db[f"res::{k}"] = ru_text
        # Save to DB
        with open('Translation/ru_database.json', 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print(f"  [+] Saved batch {b_idx+1}", flush=True)
    else:
        print(f"  [-] Failed batch {b_idx+1}, skipping", flush=True)
        
    time.sleep(4.5)  # 13-14 RPM to respect 15 RPM limit

print("All story/lore TextAssets translated successfully!", flush=True)
