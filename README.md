# Duskers RUS — Русификатор

## Структура проекта

```
Duskers_RUS/
├── Exported_EN/              # ⚠️ Исходники — НЕ ИЗМЕНЯТЬ
│   ├── dll_strings_en.json   # 9033 строки из Assembly-CSharp.dll
│   ├── resources_text_en.json# 166 TextAssets (лоры, сюжет)
│   └── streaming_assets_en.json # 4 файла из StreamingAssets/
│
├── Translation/              # Создаётся автоматически
│   ├── ru_database.json      # База переводов {ключ: русский_текст}
│   └── progress.json         # Прогресс переводчика {batch_N: "done"}
│
├── DllExtractor/             # C# инструмент (Mono.Cecil)
│   └── Program.cs
│
├── extract_assets.py         # Экстрактор (UnityPy)
├── gemini_translator.py      # Переводчик (Gemini API)
└── README.md
```

## Быстрый старт

### 1. Извлечение строк (уже сделано)
```bash
python extract_assets.py
cd DllExtractor && dotnet run
```

### 2. Перевод
Вставь API ключ в `gemini_translator.py` (строка 20), затем:
```bash
python gemini_translator.py
```
Скрипт продолжит с места остановки при любом прерывании.

### 3. Следующий шаг: Патчер
TODO: inject_patcher.py — записывает переводы обратно в игру.

## Лимиты Gemini API (бесплатный план)
| Модель | RPM | Запросов/день |
|--------|-----|--------------|
| gemini-2.0-flash-lite | 30 | 1500 |

При батче в 100 строк нам нужно **~90 запросов** на весь проект (~6% дневного лимита).
