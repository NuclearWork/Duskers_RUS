# 🛰️ Duskers — Полный Русификатор (Russian Localization)

[![Game Version](https://img.shields.io/badge/Game_Version-1.205-blue.svg)](https://store.steampowered.com/app/254320/Duskers/)
[![Translation Status](https://img.shields.io/badge/Translation-100%25-brightgreen.svg)]()
[![Release](https://img.shields.io/badge/Release-v1.2-orange.svg)](https://github.com/NuclearWork/Duskers_RUS/releases)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Полная качественная локализация текста, терминала, справки и всех сюжетных журналов для научно-фантастического симулятора выживания **Duskers** (Misfits Attic).

---

## 🎮 Особенности перевода

- **Аутентичный ретро-шрифт:** В игру внедрен кириллический шрифт **Fixedsys Excelsior**, сохраняющий строгий моноширинный терминальный стиль оригинальной игры без артефактов и обрезки строк.
- **100% Сюжета и Лора:** Полностью переведены все 145 файлов сюжетных записей, диалогов экипажа, интро-экранов после обучения, секретных архивов и отчетов исследователей корпорации MUTEKI.
- **Командный мануал и справка:** 100% перевод встроенной справочной системы (`help`, `navigate`, `destruct`, `loot`, `repair`, `shield` и всех остальных команд) с детальными пояснениями параметров.
- **Удобство управления:** Все вводимые команды консоли (`open`, `close`, `navigate`, `generator`, `gather`) намеренно сохранены на латинице — вам не придется постоянно переключать раскладку клавиатуры во время напряженных вылазок.
- **Стабильность:** Технические идентификаторы объектов, координаты процедурной генерации галактики и внутренние маркеры движка Unity сохранены в исходном виде, что исключает любые вылеты и баги генерации.

---

## 📥 Установка (Для игроков)

Самый быстрый и простой способ установить русификатор:

1. Перейдите в раздел **[Releases](https://github.com/NuclearWork/Duskers_RUS/releases)** и скачайте архив `Duskers_RUS_v1.2.zip`.
2. Откройте папку с установленной игрой в Steam:
   * Нажмите правой кнопкой мыши по **Duskers** в библиотеке Steam → **Управление** → **Просмотреть локальные файлы**.
3. Скопируйте папку **`Duskers_Data`** из скачанного архива в папку игры с **заменой всех файлов**.
4. Запустите игру. Приятного погружения!

> **Как удалить / вернуть оригинал:** В Steam нажмите правой кнопкой на Duskers → *Свойства* → *Установленные файлы* → *Проверить целостность файлов игры*.

---

## 🛠️ Сборка из исходников (Для разработчиков)

Если вы хотите внести правки в перевод или собрать мод самостоятельно:

### Требования
- **Python 3.9+** с библиотекой `UnityPy`:
  ```bash
  pip install UnityPy
  ```
- **.NET 6.0 SDK** (для сборки C# инжектора строк DLL).

### Инструкция по сборке

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/NuclearWork/Duskers_RUS.git
   cd Duskers_RUS
   ```
2. Внесите изменения в базу перевода `Translation/ru_database.json`.
3. Запустите автоматический сборщик и установщик:
   ```bash
   python inject_patcher.py
   ```
   *Скрипт автоматически найдет установленную игру Duskers в Steam, пропатчит шрифт `resources.assets`, упакует сюжетные тексты, внедрит строки в `Assembly-CSharp.dll` через Mono.Cecil и установит мод прямо в игру.*

4. Создать готовый релизный ZIP-архив:
   ```bash
   python package_release.py
   ```

---

## 📂 Структура репозитория

```text
Duskers_RUS/
├── Exported_EN/                  # Исходные английские ресурсы игры
│   ├── dll_strings_en.json       # Литералы из Assembly-CSharp.dll
│   ├── resources_text_en.json    # Текстовые ассеты и лоры (TextAssets)
│   └── streaming_assets_en.json  # Данные из StreamingAssets/
│
├── Translation/                  # База локализации
│   └── ru_database.json          # Полный словарь переводов {ключ: русский_текст}
│
├── Resources/Fonts/              # Моноширинный кириллический шрифт
│   └── Fixedsys_Excelsior.ttf
│
├── DllPatcher/                   # C# проект инжекции строк через Mono.Cecil
│   └── Program.cs
│
├── DllExtractor/                 # C# проект экспорта строк из Assembly-CSharp.dll
│   └── Program.cs
│
├── tools/                        # Вспомогательные скрипты миграции и парсинга
├── inject_patcher.py             # Главный скрипт сборки и установки мода
├── extract_assets.py             # Экстрактор ассетов из оригинальной игры
├── gemini_translator.py          # Скрипт пакетного перевода через Gemini API
├── package_release.py            # Упаковщик релизного архива
└── README.md
```

---

## 📜 Лицензия и Благодарности

- **Перевод и инструментарий:** [NuclearWork](https://github.com/NuclearWork)
- **Шрифт:** *Fixedsys Excelsior 3.01* от Dimitrios Gazetas (Kika).
- **Игра:** Создана студией [Misfits Attic](http://misfitsattic.com/). Все права на оригинальные ассеты принадлежат разработчикам.
- **Лицензия:** Инструменты и файлы локализации распространяются под лицензией [MIT](LICENSE).
