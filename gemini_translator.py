"""
Duskers RU Patcher — Надёжный пакетный переводчик (Gemini API)
==============================================================
Архитектура хранения данных:
  - Исходные файлы в Exported_EN/ НЕ ИЗМЕНЯЮТСЯ НИКОГДА.
  - Переводы хранятся в отдельном файле: Translation/ru_database.json
  - Прогресс выполнения: Translation/progress.json
  - Если скрипт прервать — продолжает ровно с того места.
"""

import json
import os
import re
import tempfile
import time

import google.generativeai as genai

# ===================================================================
# API ключ загружается из .env или переменной окружения GEMINI_API_KEY
# ===================================================================
API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY and os.path.exists(os.path.join(os.path.dirname(__file__), ".env")):
    with open(os.path.join(os.path.dirname(__file__), ".env"), "r", encoding="utf-8") as env_f:
        for line in env_f:
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1].strip("\"'")
# ===================================================================

# ─── Пути ──────────────────────────────────────────────────────────
BASE_DIR        = r"C:\Users\user\Documents\GITHUB\Duskers_RUS"
EXPORTED_DIR    = os.path.join(BASE_DIR, "Exported_EN")
TRANSLATION_DIR = os.path.join(BASE_DIR, "Translation")

# Исходные файлы (ТОЛЬКО ДЛЯ ЧТЕНИЯ)
SRC_DLL        = os.path.join(EXPORTED_DIR, "dll_strings_en.json")
SRC_RESOURCES  = os.path.join(EXPORTED_DIR, "resources_text_en.json")
SRC_STREAMING  = os.path.join(EXPORTED_DIR, "streaming_assets_en.json")

# Наши файлы (создаём сами)
RU_DATABASE    = os.path.join(TRANSLATION_DIR, "ru_database.json")   # {source_key: ru_text}
PROGRESS_FILE  = os.path.join(TRANSLATION_DIR, "progress.json")      # {batch_id: "done"}

# ─── Настройки API ─────────────────────────────────────────────────
MODEL_NAME  = "gemini-3.5-flash-lite"
BATCH_SIZE  = 25                        # Уменьшили для пробития зависших строк
DELAY       = 3.0                        # Секунд между запросами (макс. 24 rpm)

# ─── Фильтры технических строк ──────────────────────────────────────
SKIP_PATTERNS = [
    re.compile(r"^[A-Z][a-zA-Z0-9_]{2,}$"),  # CamelCase: MyMethod, GameObject
    re.compile(r"^_[a-zA-Z0-9_]+$"),           # Unity шейдеры: _LightDir
    re.compile(r"^[a-z]+\.[a-z]"),             # пути: game.ui, audio.sfx
    re.compile(r"^Assets/"),                    # Unity ресурсы
    re.compile(r"^UI/"),
    re.compile(r"^\s*$"),                       # пустые
    re.compile(r"^\d+(\.\d+)?$"),               # числа
    re.compile(r"^\{[0-9]+\}$"),                # только {0}
    re.compile(r"^https?://"),                  # URL
    re.compile(r"^[a-zA-Z0-9_]+\(\)$"),        # вызовы функций: Start()
    re.compile(r"^[a-zA-Z0-9_/\\:.]+\.(png|wav|mp3|prefab|mat|asset|unity|shader|dll)$"),
]

SYSTEM_PROMPT = """Ты профессиональный переводчик видеоигр с английского на русский.
Я отправляю тебе JSON объект {"0": "english text", "1": "english text", ...}.
Переведи ЗНАЧЕНИЯ на русский язык и верни JSON в том же формате.

ПРАВИЛА (строгие):
1. Верни ТОЛЬКО валидный JSON. Никаких пояснений, никаких ```json блоков.
2. НЕ ПЕРЕВОДИ игровые команды: navigate, scan, generator, pry, tow, motion, open, close, lure, tag, tether.
3. Сохраняй форматирование в точности: {0}, {1}, \\n, <color=white>, <b>, [room], %s, %d.
4. Не меняй регистр и содержимое технических тегов.
5. Стиль: мрачная, атмосферная космическая выживалка — переводи живо, по-русски.

ГЛОССАРИЙ (обязателен):
- Drone → Дрон          | Scrap → Лом           | Air Lock → Шлюз
- Upgrade → Модуль      | Salvage → Добыча       | Infestation → Заражение
- Generator → Генератор | Motion Sensor → Датчик | Tow → Буксир
- Hive → Улей           | Scout → Разведчик      | Hull → Корпус
"""


# ═══════════════════════════════════════════════════════════════════
#  УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════

def should_skip(text: str) -> bool:
    if not text or len(text.strip()) < 3:
        return True
    for pat in SKIP_PATTERNS:
        if pat.search(text):
            return True
    if not re.search(r"[a-zA-Z]", text):  # нет ни одной буквы
        return True
    return False


def atomic_save(path: str, data):
    """Атомарная запись: сначала во временный файл, потом rename — файл не будет повреждён."""
    dir_name = os.path.dirname(path)
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)  # атомарная замена
    except Exception:
        os.unlink(tmp_path)
        raise


def load_json(path: str, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


# ═══════════════════════════════════════════════════════════════════
#  API
# ═══════════════════════════════════════════════════════════════════

def translate_batch(model, batch: dict) -> dict:
    """Переводит батч {id: текст}. Возвращает {id: перевод}."""
    prompt = SYSTEM_PROMPT + "\n\nJSON TO TRANSLATE:\n" + json.dumps(batch, ensure_ascii=False)
    retries = 4
    backoff = 10
    while retries > 0:
        try:
            response = model.generate_content(prompt)
            res_text = response.text.strip()
            # убрать возможный markdown
            res_text = re.sub(r"^```[a-z]*\n?", "", res_text)
            res_text = re.sub(r"```$", "", res_text).strip()
            return json.loads(res_text)
        except json.JSONDecodeError:
            print(f"\n    [!] Некорректный JSON в ответе. Повтор через {backoff}с...")
            time.sleep(backoff)
            retries -= 1
            backoff *= 2
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "resource" in err.lower():
                wait = 65
                print(f"\n    [!] Лимит API. Ждём {wait}с...")
                time.sleep(wait)
                # не уменьшаем retries при 429
            else:
                print(f"\n    [!] Ошибка: {e}. Повтор через {backoff}с...")
                time.sleep(backoff)
                retries -= 1
                backoff *= 2
    return {}


# ═══════════════════════════════════════════════════════════════════
#  СБОР СТРОК ИЗ ИСХОДНИКОВ
# ═══════════════════════════════════════════════════════════════════

def collect_all_strings() -> dict:
    """
    Собирает все переводимые строки из всех источников.
    Возвращает словарь: {unique_key: original_text}
    unique_key = "dll::{type}::{method}::{offset}" или "res::{name}" или "sa::{path}"
    """
    all_strings = {}

    # 1. DLL строки
    dll_data = load_json(SRC_DLL, [])
    for entry in dll_data:
        original = entry.get("original", "")
        if not should_skip(original):
            key = f"dll::{entry.get('type','')}::{entry.get('method','')}::{entry.get('offset','')}"
            all_strings[key] = original

    # 2. TextAssets из resources.assets
    res_data = load_json(SRC_RESOURCES, {})
    for name, text in res_data.items():
        if text and not should_skip(text[:50]):  # проверяем только начало
            key = f"res::{name}"
            all_strings[key] = text

    # 3. StreamingAssets
    sa_data = load_json(SRC_STREAMING, {})
    for path, text in sa_data.items():
        if text:
            key = f"sa::{path}"
            all_strings[key] = text

    return all_strings


# ═══════════════════════════════════════════════════════════════════
#  ОСНОВНАЯ ЛОГИКА
# ═══════════════════════════════════════════════════════════════════

def main():
    if API_KEY == "ТВОЙ_API_КЛЮЧ":
        print("❌ Вставь свой API ключ в переменную API_KEY в начале файла.")
        return

    os.makedirs(TRANSLATION_DIR, exist_ok=True)

    # Загружаем текущее состояние
    ru_db    = load_json(RU_DATABASE, {})   # уже переведённые строки
    progress = load_json(PROGRESS_FILE, {}) # выполненные батчи

    # Собираем все строки из исходников
    print("🔍 Сбор строк из исходных файлов...")
    all_strings = collect_all_strings()

    # Оставляем только ещё не переведённые
    pending = [(k, v) for k, v in all_strings.items() if k not in ru_db]

    total_all    = len(all_strings)
    total_done   = len(ru_db)
    total_left   = len(pending)
    total_batches = (total_left + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"📊 Всего строк:        {total_all}")
    print(f"   Уже переведено:     {total_done}")
    print(f"   Осталось:           {total_left}")
    print(f"   Примерно запросов:  ~{total_batches} (по {BATCH_SIZE} строк)")
    print(f"   Расход дневной кв.: ~{total_batches}/1500\n")

    if total_left == 0:
        print("✅ Всё уже переведено!")
        return

    # Настраиваем Gemini
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config=genai.types.GenerationConfig(temperature=0.1),
    )
    print(f"✅ Модель: {MODEL_NAME}\n")

    # Переводим батчами
    for batch_num, batch_start in enumerate(range(0, total_left, BATCH_SIZE)):
        chunk = pending[batch_start:batch_start + BATCH_SIZE]
        batch_dict = {str(i): text for i, (_, text) in enumerate(chunk)}

        pct = (total_done + batch_start) / total_all * 100
        print(f"[{pct:5.1f}%] Батч {batch_num+1}/{total_batches} "
              f"({batch_start+1}–{batch_start+len(chunk)} из {total_left})... ", end="", flush=True)

        translated = translate_batch(model, batch_dict)

        if translated:
            # Сохраняем переводы в базу
            for local_i, (key, _) in enumerate(chunk):
                ru_text = translated.get(str(local_i), "")
                if ru_text:
                    ru_db[key] = ru_text

            # Атомарно сохраняем базу переводов
            atomic_save(RU_DATABASE, ru_db)

            print(f"✓ {len(translated)} переведено")
        else:
            print(f"✗ Не удалось перевести — пропуск.")

        time.sleep(DELAY)

    print(f"\n🎉 Готово! Переводов в базе: {len(ru_db)} из {total_all}")
    print(f"   База сохранена: {RU_DATABASE}")


if __name__ == "__main__":
    main()
