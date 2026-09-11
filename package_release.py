import os
import sys
import zipfile
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.join(BASE_DIR, "mod", "Duskers_Data")
DIST_DIR = os.path.join(BASE_DIR, "dist")
ZIP_NAME = "Duskers_RUS_v1.2.zip"

os.makedirs(DIST_DIR, exist_ok=True)
zip_path = os.path.join(DIST_DIR, ZIP_NAME)

if not os.path.exists(os.path.join(MOD_DIR, "resources.assets")) or not os.path.exists(os.path.join(MOD_DIR, "Managed", "Assembly-CSharp.dll")):
    print("[!] Папка mod/Duskers_Data не содержит собранных файлов. Сначала запустите inject_patcher.py!")
    sys.exit(1)

readme_content = """===========================================================
               РУСИФИКАТОР ДЛЯ ИГРЫ DUSKERS (v1.2)
===========================================================

ИНСТРУКЦИЯ ПО УСТАНОВКЕ:
1. Откройте папку с установленной игрой Duskers:
   - В Steam нажмите правой кнопкой на Duskers -> "Управление" -> "Просмотреть локальные файлы".
2. Скопируйте папку "Duskers_Data" из этого архива в папку с игрой с ЗАМЕНОЙ файлов.
3. Запустите игру и наслаждайтесь погружением!

ЧТО ПЕРЕВЕДЕНО:
- Полный перевод всего интерфейса и терминала.
- Полный перевод встроенной справки и мануала (команды help, navigate, destruct и др.).
- 100% перевод всех бортовых журналов, интро-диалогов и лоров экипажа.
- Аутентичный пиксельный шрифт Fixedsys Excelsior с полной поддержкой кириллицы.

GitHub репозиторий проекта:
https://github.com/NuclearWork/Duskers_RUS
===========================================================
"""

temp_readme = os.path.join(MOD_DIR, "ИНСТРУКЦИЯ_ПО_УСТАНОВКЕ.txt")
with open(temp_readme, "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"📦 Упаковка релиза в {zip_path}...")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(os.path.join(BASE_DIR, "mod")):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, os.path.join(BASE_DIR, "mod"))
            zipf.write(full_path, rel_path)

if os.path.exists(temp_readme):
    os.remove(temp_readme)

print(f"✅ Готово! Архив для публикации на GitHub Releases создан:")
print(f"   {zip_path} ({os.path.getsize(zip_path) // (1024*1024)} МБ)")
