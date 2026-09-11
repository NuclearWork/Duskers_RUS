# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import subprocess
import argparse

try:
    import UnityPy
except ImportError:
    print("[!] Библиотека UnityPy не найдена. Установите её: pip install UnityPy")
    sys.exit(1)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATION_DB = os.path.join(BASE_DIR, "Translation", "ru_database.json")
FONT_FILE = os.path.join(BASE_DIR, "Resources", "Fonts", "Fixedsys_Excelsior.ttf")
OUTPUT_DIR = os.path.join(BASE_DIR, "mod", "Duskers_Data")

# Список возможных путей установки Duskers в Steam
DEFAULT_GAME_PATHS = [
    r"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"C:\Program Files (x86)\Steam\steamapps\common\Duskers\Duskers_Data",
    r"C:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"D:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"E:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"F:\SteamLibrary\steamapps\common\Duskers\Duskers_Data"
]

def find_game_dir(custom_path=None):
    if custom_path and os.path.isdir(custom_path):
        if os.path.exists(os.path.join(custom_path, "resources.assets")):
            return custom_path
        if os.path.isdir(os.path.join(custom_path, "Duskers_Data")):
            return os.path.join(custom_path, "Duskers_Data")

    env_path = os.environ.get("DUSKERS_DIR")
    if env_path and os.path.isdir(env_path):
        if os.path.exists(os.path.join(env_path, "resources.assets")):
            return env_path

    for path in DEFAULT_GAME_PATHS:
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "resources.assets")):
            return path

    return None

def load_db():
    if not os.path.exists(TRANSLATION_DB):
        print(f"[!] Файл базы перевода не найден: {TRANSLATION_DB}")
        sys.exit(1)
    with open(TRANSLATION_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def patch_assets(game_dir, db):
    print("📦 Патчинг resources.assets и шрифтов...")
    
    if not os.path.exists(FONT_FILE):
        print(f"[!] Шрифт не найден: {FONT_FILE}")
        sys.exit(1)

    with open(FONT_FILE, "rb") as f:
        font_data = f.read()

    resources_src = os.path.join(game_dir, "resources.assets")
    if not os.path.exists(resources_src):
        print(f"[!] Файл resources.assets не найден по пути: {resources_src}")
        sys.exit(1)

    env_res = UnityPy.load(resources_src)
    text_assets_patched = 0

    for obj in env_res.objects:
        if obj.type.name == "TextAsset":
            tree = obj.read_typetree()
            name = tree.get("m_Name", "")
            key = f"res::{name}"
            
            if key in db and db[key].encode("utf-8") != tree.get("m_Script", b""):
                tree["m_Script"] = db[key]
                obj.save_typetree(tree)
                text_assets_patched += 1

        elif obj.type.name == "Font":
            tree = obj.read_typetree()
            name = tree.get("m_Name", "")
            if name in ["Fixedsys500c_Console"]:
                tree["m_FontData"] = font_data
                obj.save_typetree(tree)
                print(f"  [Вшит шрифт] {name} (resources.assets)")

    out_resources = os.path.join(OUTPUT_DIR, "resources.assets")
    with open(out_resources, "wb") as f:
        f.write(list(env_res.files.values())[0].save())
    print(f"  [+] Заменено {text_assets_patched} текстовых файлов (TextAssets).")

def patch_streaming_assets(db):
    print("📁 Патчинг StreamingAssets...")
    count = 0
    for key, text in db.items():
        if key.startswith("sa::"):
            rel_path = key[4:]
            out_path = os.path.join(OUTPUT_DIR, "StreamingAssets", rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            count += 1
    print(f"  [+] Записано {count} файлов в StreamingAssets.")

def patch_dll(game_dir):
    print("⚙️ Запуск C# инжектора для Assembly-CSharp.dll...")
    dll_patcher_dir = os.path.join(BASE_DIR, "DllPatcher")
    original_dll = os.path.join(game_dir, "Managed", "Assembly-CSharp.dll")
    patched_dll = os.path.join(BASE_DIR, "Patched_RU", "Assembly-CSharp.dll")

    if not os.path.exists(original_dll):
        print(f"[!] Assembly-CSharp.dll не найдена: {original_dll}")
        sys.exit(1)

    cmd = ["dotnet", "run", "--", TRANSLATION_DB, original_dll, patched_dll]
    result = subprocess.run(cmd, cwd=dll_patcher_dir, capture_output=True, text=True)

    if result.returncode == 0 and os.path.exists(patched_dll):
        managed_out = os.path.join(OUTPUT_DIR, "Managed")
        os.makedirs(managed_out, exist_ok=True)
        shutil.copy(patched_dll, os.path.join(managed_out, "Assembly-CSharp.dll"))
        print("  [+] Assembly-CSharp.dll успешно пропатчена и упакована.")
    else:
        print("  [!] Ошибка при патчинге Assembly-CSharp.dll:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Русификатор для игры Duskers (Duskers_RUS)")
    parser.add_argument("-g", "--game-dir", help="Путь к папке Duskers_Data или корневой папке игры")
    parser.add_argument("--no-copy", action="store_true", help="Только собрать мод в папку mod/, не копировать в игру")
    args = parser.parse_args()

    print("==================================================")
    print("   Русификатор Duskers — Сборщик и Установщик     ")
    print("==================================================")

    game_dir = find_game_dir(args.game_dir)
    if not game_dir:
        print("\n[!] Не удалось автоматически обнаружить папку с установленной игрой Duskers.")
        user_input = input("Пожалуйста, введите полный путь к папке Duskers_Data (например Z:\\SteamLibrary\\steamapps\\common\\Duskers\\Duskers_Data):\n> ").strip()
        game_dir = find_game_dir(user_input)
        if not game_dir:
            print("[X] Указанный путь неверен или не содержит resources.assets. Завершение работы.")
            sys.exit(1)

    print(f"[+] Обнаружена папка игры: {game_dir}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "Managed"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "StreamingAssets"), exist_ok=True)

    db = load_db()
    patch_assets(game_dir, db)
    patch_streaming_assets(db)
    patch_dll(game_dir)

    if not args.no_copy:
        print(f"\n🚀 Копирование мода напрямую в игру...")
        print(f"   Цель: {game_dir}")
        try:
            shutil.copytree(OUTPUT_DIR, game_dir, dirs_exist_ok=True)
            print("✅ Мод успешно установлен в игру!")
        except Exception as e:
            print(f"❌ Ошибка при копировании файлов в игру: {e}")

    print(f"\n🎉 ВСЕ ГОТОВО! Файлы для распространения лежат в: {os.path.abspath(os.path.join(BASE_DIR, 'mod'))}")

if __name__ == "__main__":
    main()
