# -*- coding: utf-8 -*-
import os
import sys
import json
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
EXPORT_DIR = os.path.join(BASE_DIR, "Exported_EN")
os.makedirs(EXPORT_DIR, exist_ok=True)

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

def main():
    parser = argparse.ArgumentParser(description="Экстрактор исходных английских текстов из игры Duskers")
    parser.add_argument("-g", "--game-dir", help="Путь к папке Duskers_Data")
    args = parser.parse_args()

    game_dir = find_game_dir(args.game_dir)
    if not game_dir:
        print("[!] Не удалось автоматически обнаружить папку Duskers_Data.")
        user_input = input("Введите путь к Duskers_Data:\n> ").strip()
        game_dir = find_game_dir(user_input)
        if not game_dir:
            print("[X] Ошибка: Неверный путь.")
            sys.exit(1)

    print(f"[+] Папка игры: {game_dir}")

    # 1. Extract StreamingAssets
    streaming_dir = os.path.join(game_dir, "StreamingAssets")
    streaming_strings = {}
    if os.path.isdir(streaming_dir):
        for root, dirs, files in os.walk(streaming_dir):
            for f in files:
                if f.endswith(".txt"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, streaming_dir).replace('\\', '/')
                    try:
                        with open(full_path, "r", encoding="utf-8") as file:
                            streaming_strings[rel_path] = file.read()
                    except Exception:
                        try:
                            with open(full_path, "r", encoding="cp1252") as file:
                                streaming_strings[rel_path] = file.read()
                        except Exception as e2:
                            print(f"Failed to read {rel_path}: {e2}")

        with open(os.path.join(EXPORT_DIR, "streaming_assets_en.json"), "w", encoding="utf-8") as out:
            json.dump(streaming_strings, out, indent=4, ensure_ascii=False)
        print(f"[+] Извлечено {len(streaming_strings)} файлов из StreamingAssets.")

    # 2. Extract TextAssets from resources.assets
    assets_strings = {}
    resources_path = os.path.join(game_dir, "resources.assets")
    if os.path.exists(resources_path):
        try:
            env = UnityPy.load(resources_path)
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    tree = obj.read_typetree()
                    name = tree.get('m_Name', 'Unknown')
                    script_bytes = tree.get('m_Script', b'')
                    
                    text = ""
                    if isinstance(script_bytes, bytes):
                        try:
                            text = script_bytes.decode('utf-8-sig')
                        except:
                            text = script_bytes.decode('cp1252', errors='replace')
                    elif isinstance(script_bytes, str):
                        text = script_bytes
                    else:
                        text = str(script_bytes)
                    
                    assets_strings[name] = text

            with open(os.path.join(EXPORT_DIR, "resources_text_en.json"), "w", encoding="utf-8") as out:
                json.dump(assets_strings, out, indent=4, ensure_ascii=False)
            print(f"[+] Извлечено {len(assets_strings)} TextAssets из resources.assets.")

        except Exception as e:
            print(f"[!] Ошибка при распаковке resources.assets: {e}")

    print(f"\n[✓] Все исходники сохранены в: {EXPORT_DIR}")

if __name__ == "__main__":
    main()
