# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET

with open('Translation/ru_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

xml_str = db.get("res::CommandDefinitions", "")
wrapped = f"<root>{xml_str}</root>"
root = ET.fromstring(wrapped)

REPLACEMENTS = {
    "auto-navigates drone(s) to a room": "автоматически направляет дрона(-ов) в комнату",
    "\t\t'navigate 1 2 r14' Navigate drones 1 and 2 to r14": "\t\t'navigate 1 2 r14' Направить дронов 1 и 2 в r14",
    "\t\t'navigate 1 d8'    Navigates drone 1 through d8": "\t\t'navigate 1 d8'    Направить дрона 1 через шлюз d8",
    "\t\t'navigate 1 3'     Navigates drone 1 to drone 3": "\t\t'navigate 1 3'     Направить дрона 1 к дрону 3",
    "\t\t'navigate 3'       (from drone view) Navigates drone 3 to current drone": "\t\t'navigate 3'       (из вида дрона) Направить дрона 3 к текущему дрону",
    "self destructs the drone with an optional delay": "самоуничтожение дрона с возможностью задержки",
    "\t\tWill damage everything in the current room.": "\t\tНаносит урон всему живому и объектам в текущей комнате.",
    "\t\tThis command requires confirmation before executing": "\t\tКоманда требует подтверждения перед выполнением",
    "\t\tTo cancel: type 'destruct' (quickly!) again": "\t\tДля отмены: введите 'destruct' повторно (быстро!)",
    "\t\t'destruct t10' issues destruct after 10 seconds": "\t\t'destruct t10' запускает взрыв через 10 секунд",
    "\t\t'destruct' (w/o time) is equal to 'destruct t3'": "\t\t'destruct' (без времени) эквивалентно 'destruct t3'",
    "toggles specified door(s)": "переключает состояние указанной(-ых) двери(-ей)",
    "\t\tOpens or closes one or more specified doors, so long as they are powered.": "\t\tОткрывает или закрывает указанные двери при наличии питания.",
    "toggles specified airlock(s)": "переключает состояние указанного(-ых) шлюза(-ов)",
    "\t\tOpens or closes one or more specified airlocks, so long as they are powered.": "\t\tОткрывает или закрывает указанные внешние шлюзы при наличии питания.",
    "loot or swap upgrade with dead drone": "забрать или обменять модуль с уничтоженного дрона",
    "\t\tLOOT examples (requires empty slot):": "\t\tПримеры СБОРА (требуется пустой слот):",
    "\t\t\tloot [target item] ([target drone]).": "\t\t\tloot [целевой модуль] ([целевой дрон]).",
    "repair nearby broken items": "починить поврежденные объекты рядом",
    "\t\tRepairs upgrades on drones that have errors, as well as broken items within a room.": "\t\tЧинит сломанные модули дронов и поврежденные объекты в комнате.",
    "\t\tYou must be near the item to repair it.": "\t\tДрон должен находиться рядом с объектом для ремонта.",
    "\t\tIf there is only one thing to repair, no parameters need to be specified": "\t\tЕсли ремонтировать нужно только один объект, параметры указывать не нужно",
    "\t\tIf more than one items need repairing, entering the command with no paramters will list the items": "\t\tЕсли повреждено несколько объектов, команда без параметров выведет их список",
    "\t\tIf you have enough repair resources to repair all items, enter repair all": "\t\tПри наличии достаточного запаса ресурсов введите 'repair all'",
    "\t\tYou can also fix specific items by specifying their name": "\t\tТакже можно чинить конкретные объекты, указав их название",
    "\t\tWoe is you if your repair upgrade breaks...": "\t\tГоре вам, если сломается сам ремонтный модуль...",
    "scans the current room for undetected items": "сканирует текущую комнату на скрытые предметы",
    "\t\tScans the drone's room for items of interest.": "\t\tСканирует комнату на наличие полезных объектов.",
    "\t\tScans may reveal items undetected by first-pass inspection": "\t\tСканирование может обнаружить скрытые при первичном осмотре предметы",
    "drops a sensor which continually scans a room for threats": "сбрасывает датчик, непрерывно сканирующий комнату на угрозы",
    "\t\tA sensor cannot be retrieved once dropped": "\t\tУстановленный датчик невозможно забрать обратно",
    "magnetically clamps item in room to prevent being pulled outside of ship": "магнитно фиксирует объект в комнате для защиты от разгерметизации",
    "activates/deactivates shield": "включает/выключает силовой щит",
    "\t\tForcefield that protects the drone from damage.": "\t\tСиловое поле, защищающее дрона от любых повреждений.",
    "shield recharges but has lower health": "щит перезаряжается, но имеет меньший запас прочности",
    "radiation-proof shield": "радиационно-стойкий щит",
    "Acts as if shield broken by attack": "Имитирует пробитие щита в результате атаки",
    "drops proximity stun mine": "сбрасывает оглушающую бесконтактную мину",
    "\t\tsolders door shut": "\t\tнаглухо заваривает дверь",
    "\t\t'info' list items in the specified drone's room": "\t\t'info' выводит список предметов в комнате указанного дрона"
}

modified_count = 0
for elem in root.iter():
    for attr in ['description', 'message']:
        val = elem.get(attr)
        if val in REPLACEMENTS:
            elem.set(attr, REPLACEMENTS[val])
            modified_count += 1
        elif val:
            # Strip comparison
            v_strip = val.strip()
            for r_k, r_v in REPLACEMENTS.items():
                if v_strip == r_k.strip():
                    elem.set(attr, r_v)
                    modified_count += 1
                    break

print(f"Patched {modified_count} attributes in CommandDefinitions!")

new_xml = ET.tostring(root, encoding='unicode', method='xml')
new_xml = new_xml.replace('<root>', '').replace('</root>', '').strip()
db["res::CommandDefinitions"] = new_xml

with open('Translation/ru_database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("Saved updated CommandDefinitions to ru_database.json!")
