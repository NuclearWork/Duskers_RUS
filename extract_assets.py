import os
import json
import UnityPy

game_dir = r"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data"
export_dir = r"C:\Users\user\Documents\GITHUB\Duskers_RUS\Exported_EN"

# 1. Extract StreamingAssets
streaming_dir = os.path.join(game_dir, "StreamingAssets")
streaming_strings = {}

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

with open(os.path.join(export_dir, "streaming_assets_en.json"), "w", encoding="utf-8") as out:
    json.dump(streaming_strings, out, indent=4, ensure_ascii=False)
print(f"Extracted {len(streaming_strings)} StreamingAssets files.")


# 2. Extract TextAssets from resources.assets
assets_strings = {}
resources_path = os.path.join(game_dir, "resources.assets")

try:
    env = UnityPy.load(resources_path)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            tree = obj.read_typetree()
            name = tree.get('m_Name', 'Unknown')
            script_bytes = tree.get('m_Script', b'')
            
            # decode script bytes
            text = ""
            if isinstance(script_bytes, bytes):
                try:
                    text = script_bytes.decode('utf-8-sig') # handling BOM if any
                except:
                    text = script_bytes.decode('cp1252', errors='replace')
            elif isinstance(script_bytes, str):
                text = script_bytes
            else:
                text = str(script_bytes)
            
            assets_strings[name] = text

    with open(os.path.join(export_dir, "resources_text_en.json"), "w", encoding="utf-8") as out:
        json.dump(assets_strings, out, indent=4, ensure_ascii=False)
    print(f"Extracted {len(assets_strings)} TextAssets from resources.assets.")

except Exception as e:
    print(f"Error extracting resources.assets: {e}")
