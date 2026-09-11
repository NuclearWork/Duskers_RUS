import os
import json
import shutil
import subprocess
import UnityPy

BASE_DIR = r"C:\Users\user\Documents\GITHUB\Duskers_RUS"
GAME_DIR = r"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data"
TRANSLATION_DB = os.path.join(BASE_DIR, "Translation", "ru_database.json")
FONT_FILE = os.path.join(BASE_DIR, "Resources", "Fonts", "Fixedsys_Excelsior.ttf")

OUTPUT_DIR = os.path.join(BASE_DIR, "mod", "Duskers_Data")

# Создаем папку для готового патча
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "Managed"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "StreamingAssets", "DataStore", "Objectives"), exist_ok=True)

def load_db():
    with open(TRANSLATION_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def patch_assets(db):
    print("📦 Патчинг resources.assets и шрифтов...")
    
    # Загружаем кириллический шрифт
    with open(FONT_FILE, "rb") as f:
        font_data = f.read()

    # Патчим resources.assets
    env_res = UnityPy.load(os.path.join(GAME_DIR, "resources.assets"))
    
    text_assets_patched = 0

    for obj in env_res.objects:
        if obj.type.name == "TextAsset":
            tree = obj.read_typetree()
            name = tree.get("m_Name", "")
            key = f"res::{name}"
            
            if key in db and db[key].encode("utf-8") != tree.get("m_Script", b""):
                # UnityPy сам закодирует строку, передаем str
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

    # Сохраняем resources.assets
    with open(os.path.join(OUTPUT_DIR, "resources.assets"), "wb") as f:
        f.write(list(env_res.files.values())[0].save())
    print(f"  [+] Заменено {text_assets_patched} лоров (TextAssets).")

def patch_streaming_assets(db):
    print("📁 Патчинг StreamingAssets...")
    count = 0
    for key, text in db.items():
        if key.startswith("sa::"):
            rel_path = key[4:]  # убираем "sa::"
            out_path = os.path.join(OUTPUT_DIR, "StreamingAssets", rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            count += 1
    print(f"  [+] Записано {count} файлов в StreamingAssets.")

def patch_dll():
    print("⚙️ Запуск C# инжектора для Assembly-CSharp.dll...")
    dll_patcher_dir = os.path.join(BASE_DIR, "DllPatcher")
    
    # Копируем пропатченную DLL в папку патча
    patched_dll = os.path.join(BASE_DIR, "Patched_RU", "Assembly-CSharp.dll")
    
    # Запускаем C# проект
    result = subprocess.run(["dotnet", "run"], cwd=dll_patcher_dir, capture_output=True, text=True)
    
    if os.path.exists(patched_dll):
        shutil.copy(patched_dll, os.path.join(OUTPUT_DIR, "Managed", "Assembly-CSharp.dll"))
        print("  [+] Assembly-CSharp.dll успешно упакована в патч.")
    else:
        print("  [!] Ошибка: Патченная DLL не была создана!")
        print(result.stdout)

def main():
    db = load_db()
    patch_assets(db)
    patch_streaming_assets(db)
    patch_dll()
    
    print(f"\n🚀 Копирование мода напрямую в игру...")
    print(f"   Цель: {GAME_DIR}")
    
    try:
        shutil.copytree(OUTPUT_DIR, GAME_DIR, dirs_exist_ok=True)
        print("✅ Мод успешно установлен в игру!")
    except Exception as e:
        print(f"❌ Ошибка при копировании файлов в игру: {e}")
        
    print(f"\n🎉 ВСЕ ГОТОВО! Файлы для распространения лежат в папке: {os.path.abspath(os.path.join(BASE_DIR, 'mod'))}")

if __name__ == "__main__":
    main()
