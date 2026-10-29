# -*- coding: utf-8 -*-
"""
Duskers Russian Localization Manager (GUI)
Установщик и менеджер русификатора для игры Duskers.
Позволяет в один клик устанавливать русский перевод и возвращать оригинальный английский язык.
"""

import os
import sys
import shutil
import json
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Определение базовой папки (поддержка запуска как скриптом, так и через PyInstaller .exe)
if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = APP_DIR

# Папка с модифицированными файлами (внутри exe или рядом со скриптом)
MOD_DATA_DIR = os.path.join(APP_DIR, "mod", "Duskers_Data")
if not os.path.exists(MOD_DATA_DIR):
    MOD_DATA_DIR = os.path.join(EXE_DIR, "mod", "Duskers_Data")

# Папка с ресурсами и иконками
ICONS_DIR = os.path.join(APP_DIR, "Resources", "Icons")
if not os.path.exists(ICONS_DIR):
    ICONS_DIR = os.path.join(EXE_DIR, "Resources", "Icons")

DEFAULT_STEAM_PATHS = [
    r"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"C:\Program Files (x86)\Steam\steamapps\common\Duskers\Duskers_Data",
    r"C:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"D:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"E:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"F:\SteamLibrary\steamapps\common\Duskers\Duskers_Data"
]

def load_ui_image(filename, size=None):
    """Безопасная загрузка изображения через PIL / PhotoImage"""
    filepath = os.path.join(ICONS_DIR, filename)
    if not os.path.exists(filepath):
        return None
    if HAS_PIL:
        try:
            im = Image.open(filepath)
            if size:
                im = im.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception:
            pass
    try:
        return tk.PhotoImage(file=filepath)
    except Exception:
        return None

def is_game_running():
    """Проверяет, запущена ли сейчас игра Duskers (исключая процесс самого патчера/установщика)"""
    current_pid = os.getpid()
    target_names = {"duskers.exe", "duskers.x86_64", "duskers.x86", "duskers"}

    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if p.info.get('pid') == current_pid:
                    continue
                name = p.info.get('name')
                if name and name.lower() in target_names:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        try:
            out = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq duskers.exe" /FO CSV /NH',
                shell=True,
                text=True,
                errors="ignore"
            )
            for line in out.strip().splitlines():
                parts = line.strip().split('","')
                if parts and len(parts) >= 2:
                    proc_name = parts[0].strip('"').lower()
                    proc_pid = parts[1].strip('"')
                    if proc_name == "duskers.exe" and proc_pid.isdigit() and int(proc_pid) != current_pid:
                        return True
        except Exception:
            pass
    return False

def find_game_dir():
    """Ищет папку Duskers_Data в переменных окружения и стандартных библиотеках Steam"""
    env_path = os.environ.get("DUSKERS_DIR")
    if env_path and os.path.isdir(env_path):
        if os.path.exists(os.path.join(env_path, "resources.assets")):
            return env_path
        if os.path.isdir(os.path.join(env_path, "Duskers_Data")):
            return os.path.join(env_path, "Duskers_Data")

    for p in DEFAULT_STEAM_PATHS:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "resources.assets")):
            return p
    return ""

class DuskersPatcherGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Duskers — Менеджер Русификатора [v1.3]")
        self.geometry("710x620")
        self.minsize(660, 560)
        self.configure(bg="#080c13")

        # Назначение иконки окна
        self._apply_window_icon()

        # Загрузка визуальных ассетов
        self._load_assets()

        self.game_path_var = tk.StringVar(value=find_game_dir())

        self.setup_ui()
        self.check_status()

    def _apply_window_icon(self):
        """Устанавливает иконку приложения в заголовок и панель задач Windows"""
        ico_file = os.path.join(ICONS_DIR, "app_icon.ico")
        png_file = os.path.join(ICONS_DIR, "app_icon.png")

        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        if os.path.exists(png_file):
            try:
                self._app_icon_photo = load_ui_image("app_icon.png")
                if self._app_icon_photo:
                    self.iconphoto(True, self._app_icon_photo)
            except Exception:
                pass

    def _load_assets(self):
        """Кэширует графические иконки и баннер"""
        self.img_banner = load_ui_image("header_banner.png", (676, 76))
        self.img_install = load_ui_image("icon_install.png", (22, 22))
        self.img_restore = load_ui_image("icon_restore.png", (22, 22))
        self.img_steam = load_ui_image("icon_steam.png", (18, 18))
        self.img_folder = load_ui_image("icon_folder.png", (18, 18))
        self.img_browse = load_ui_image("icon_browse.png", (16, 16))
        
        self.img_led_green = load_ui_image("led_green.png", (14, 14))
        self.img_led_yellow = load_ui_image("led_yellow.png", (14, 14))
        self.img_led_red = load_ui_image("led_red.png", (14, 14))

    def setup_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        self.font_term = ("Consolas", 10)
        self.font_term_bold = ("Consolas", 10, "bold")
        self.font_header = ("Consolas", 13, "bold")
        self.font_title = ("Consolas", 15, "bold")

        # 1. Верхний баннер в стиле ретро-терминала CRT
        if self.img_banner:
            banner_frame = tk.Frame(self, bg="#080c13")
            banner_frame.pack(fill="x", padx=16, pady=(12, 6))
            self.banner_lbl = tk.Label(banner_frame, image=self.img_banner, bg="#080c13", bd=0)
            self.banner_lbl.pack(anchor="center")
        else:
            # Fallback текстовый заголовок
            header_frame = tk.Frame(self, bg="#111722", bd=1, relief="solid", highlightbackground="#1b2a3f", highlightthickness=1)
            header_frame.pack(fill="x", padx=16, pady=(12, 6))
            title_lbl = tk.Label(
                header_frame, 
                text="🛰️ DUSKERS RUSSIAN LOCALIZATION MANAGER", 
                fg="#00ff66", 
                bg="#111722", 
                font=self.font_title
            )
            title_lbl.pack(pady=(10, 2))
            sub_lbl = tk.Label(
                header_frame, 
                text="Полный перевод интерфейса, мануала, бортовых журналов и терминала", 
                fg="#7a92a5", 
                bg="#111722", 
                font=self.font_term
            )
            sub_lbl.pack(pady=(0, 10))

        # 2. Секция выбора папки с игрой
        path_frame = tk.LabelFrame(
            self, 
            text=" [ ПАПКА С ИГРОЙ ] ", 
            fg="#38ef7d", 
            bg="#0c121a", 
            font=self.font_term_bold, 
            bd=1, 
            relief="groove"
        )
        path_frame.pack(fill="x", padx=16, pady=5)

        path_inner = tk.Frame(path_frame, bg="#0c121a")
        path_inner.pack(fill="x", padx=10, pady=7)

        self.path_entry = tk.Entry(
            path_inner, 
            textvariable=self.game_path_var, 
            font=self.font_term, 
            bg="#131c28", 
            fg="#e0e8f0", 
            insertbackground="#00ff66",
            bd=1,
            relief="solid",
            highlightcolor="#00ff66",
            highlightthickness=1
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)
        self.path_entry.bind("<KeyRelease>", lambda e: self.check_status())

        # Кнопка обзора с иконкой
        browse_kwargs = {
            "text": " Обзор...",
            "font": self.font_term_bold,
            "bg": "#1e2a38",
            "fg": "#ffffff",
            "activebackground": "#29394d",
            "activeforeground": "#00ff66",
            "bd": 1,
            "relief": "solid",
            "padx": 10,
            "pady": 3,
            "cursor": "hand2",
            "command": self.browse_folder
        }
        if self.img_browse:
            browse_kwargs["image"] = self.img_browse
            browse_kwargs["compound"] = "left"

        self.browse_btn = tk.Button(path_inner, **browse_kwargs)
        self.browse_btn.pack(side="right")
        self._add_hover_effect(self.browse_btn, "#1e2a38", "#2a3b4e")

        # Строка статуса пути со светодиодом
        status_line = tk.Frame(path_frame, bg="#0c121a")
        status_line.pack(fill="x", padx=10, pady=(0, 6))

        self.path_led_lbl = tk.Label(status_line, image=self.img_led_yellow, bg="#0c121a")
        self.path_led_lbl.pack(side="left", padx=(0, 6))

        self.status_lbl = tk.Label(
            status_line, 
            text="Поиск игры...", 
            font=self.font_term, 
            bg="#0c121a", 
            fg="#ffbb33", 
            anchor="w"
        )
        self.status_lbl.pack(side="left", fill="x", expand=True)

        # 3. Информационная панель телеметрии (Язык + Бэкап)
        info_frame = tk.LabelFrame(
            self,
            text=" [ СТАТУС ТЕЛЕМЕТРИИ ] ",
            fg="#38ef7d",
            bg="#0c121a",
            font=self.font_term_bold,
            bd=1,
            relief="groove"
        )
        info_frame.pack(fill="x", padx=16, pady=4)

        # Строка 1: Текущий язык
        row_lang = tk.Frame(info_frame, bg="#0c121a")
        row_lang.pack(fill="x", padx=10, pady=(6, 3))

        self.lang_led = tk.Label(row_lang, image=self.img_led_yellow, bg="#0c121a")
        self.lang_led.pack(side="left", padx=(0, 6))

        self.lang_status_lbl = tk.Label(
            row_lang, 
            text="ТЕКУЩИЙ ЯЗЫК: Не определен", 
            font=self.font_term_bold, 
            bg="#0c121a", 
            fg="#ffffff",
            anchor="w"
        )
        self.lang_status_lbl.pack(side="left", fill="x", expand=True)

        # Строка 2: Резервная копия
        row_backup = tk.Frame(info_frame, bg="#0c121a")
        row_backup.pack(fill="x", padx=10, pady=(0, 6))

        self.backup_led = tk.Label(row_backup, image=self.img_led_yellow, bg="#0c121a")
        self.backup_led.pack(side="left", padx=(0, 6))

        self.backup_status_lbl = tk.Label(
            row_backup, 
            text="РЕЗЕРВНАЯ КОПИЯ (BACKUP): Не найдена", 
            font=self.font_term, 
            bg="#0c121a", 
            fg="#7a92a5",
            anchor="w"
        )
        self.backup_status_lbl.pack(side="left", fill="x", expand=True)

        # 4. Основные командные кнопки (Установить / Восстановить)
        actions_frame = tk.Frame(self, bg="#080c13")
        actions_frame.pack(fill="x", padx=16, pady=6)

        # Кнопка «УСТАНОВИТЬ РУСИФИКАТОР»
        install_kwargs = {
            "text": "  УСТАНОВИТЬ РУСИФИКАТОР",
            "font": ("Consolas", 11, "bold"),
            "bg": "#006b37",
            "fg": "#ffffff",
            "activebackground": "#00994f",
            "activeforeground": "#ffffff",
            "bd": 1,
            "relief": "solid",
            "pady": 8,
            "cursor": "hand2",
            "command": self.start_install
        }
        if self.img_install:
            install_kwargs["image"] = self.img_install
            install_kwargs["compound"] = "left"

        self.install_btn = tk.Button(actions_frame, **install_kwargs)
        self.install_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._add_hover_effect(self.install_btn, "#006b37", "#008f49")

        # Кнопка «ВОССТАНОВИТЬ ОРИГИНАЛ»
        restore_kwargs = {
            "text": "  ВОССТАНОВИТЬ ОРИГИНАЛ (EN)",
            "font": ("Consolas", 11, "bold"),
            "bg": "#3d1b1b",
            "fg": "#ff9999",
            "activebackground": "#5c2626",
            "activeforeground": "#ffffff",
            "bd": 1,
            "relief": "solid",
            "pady": 8,
            "cursor": "hand2",
            "command": self.start_restore
        }
        if self.img_restore:
            restore_kwargs["image"] = self.img_restore
            restore_kwargs["compound"] = "left"

        self.restore_btn = tk.Button(actions_frame, **restore_kwargs)
        self.restore_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self._add_hover_effect(self.restore_btn, "#3d1b1b", "#542424")

        # 5. Вспомогательная панель (Запуск игры / Открыть папку)
        sub_actions_frame = tk.Frame(self, bg="#080c13")
        sub_actions_frame.pack(fill="x", padx=16, pady=(0, 6))

        launch_kwargs = {
            "text": "  ЗАПУСТИТЬ ИГРУ (STEAM)",
            "font": ("Consolas", 9, "bold"),
            "bg": "#141e2b",
            "fg": "#38ef7d",
            "activebackground": "#1e2d40",
            "activeforeground": "#00ff66",
            "bd": 1,
            "relief": "solid",
            "pady": 5,
            "cursor": "hand2",
            "command": self.launch_game
        }
        if self.img_steam:
            launch_kwargs["image"] = self.img_steam
            launch_kwargs["compound"] = "left"

        self.launch_btn = tk.Button(sub_actions_frame, **launch_kwargs)
        self.launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._add_hover_effect(self.launch_btn, "#141e2b", "#1c2b3d")

        open_dir_kwargs = {
            "text": "  ОТКРЫТЬ ПАПКУ ИГРЫ",
            "font": ("Consolas", 9, "bold"),
            "bg": "#141e2b",
            "fg": "#a0b8d0",
            "activebackground": "#1e2d40",
            "activeforeground": "#ffffff",
            "bd": 1,
            "relief": "solid",
            "pady": 5,
            "cursor": "hand2",
            "command": self.open_game_folder
        }
        if self.img_folder:
            open_dir_kwargs["image"] = self.img_folder
            open_dir_kwargs["compound"] = "left"

        self.open_dir_btn = tk.Button(sub_actions_frame, **open_dir_kwargs)
        self.open_dir_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self._add_hover_effect(self.open_dir_btn, "#141e2b", "#1c2b3d")

        # 6. Консольный лог действий
        log_frame = tk.LabelFrame(
            self, 
            text=" [ СИСТЕМНЫЙ ТЕРМИНАЛ MUTEKI ] ", 
            fg="#38ef7d", 
            bg="#080c13", 
            font=self.font_term_bold, 
            bd=1, 
            relief="groove"
        )
        log_frame.pack(fill="both", expand=True, padx=16, pady=(2, 14))

        self.log_text = tk.Text(
            log_frame, 
            font=("Consolas", 9), 
            bg="#05080d", 
            fg="#00ff66", 
            insertbackground="#00ff66", 
            bd=0,
            wrap="word",
            padx=10,
            pady=8
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        # Цветовые теги для лога
        self.log_text.tag_config("ok", foreground="#00ff66")
        self.log_text.tag_config("info", foreground="#55d4ff")
        self.log_text.tag_config("warn", foreground="#ffbb33")
        self.log_text.tag_config("err", foreground="#ff4444")
        self.log_text.tag_config("dim", foreground="#5a758c")

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview, bg="#0e1622")
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log("Система инициализирована. Версия русификатора: v1.3")
        self.log("Графический модуль MUTEKI OS загружен.")

    def _add_hover_effect(self, widget, normal_bg, hover_bg):
        """Добавляет интерактивную подсветку кнопок при наведении мыши"""
        def on_enter(e):
            if str(widget["state"]) != "disabled":
                widget.config(bg=hover_bg)
        def on_leave(e):
            if str(widget["state"]) != "disabled":
                widget.config(bg=normal_bg)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def log(self, message):
        """Потокобезопасный вывод сообщения в консоль GUI"""
        self.after(0, self._do_log, message)

    def _do_log(self, message):
        tag = "normal"
        if message.startswith("[✓]") or message.startswith("✅") or "УСПЕШНО" in message:
            tag = "ok"
        elif message.startswith("[!]") or message.startswith("⚠️") or "Внимание" in message:
            tag = "warn"
        elif message.startswith("[X]") or message.startswith("❌") or "Ошибка" in message:
            tag = "err"
        elif message.startswith("---") or message.startswith(">"):
            tag = "dim"
        elif message.startswith("📁") or message.startswith("📦") or message.startswith("⚙️"):
            tag = "info"

        self.log_text.insert("end", f"> {message}\n", tag)
        self.log_text.see("end")

    def browse_folder(self):
        selected = filedialog.askdirectory(title="Выберите папку с игрой Duskers или папку Duskers_Data")
        if selected:
            if os.path.exists(os.path.join(selected, "resources.assets")):
                self.game_path_var.set(selected)
            elif os.path.isdir(os.path.join(selected, "Duskers_Data")) and os.path.exists(os.path.join(selected, "Duskers_Data", "resources.assets")):
                self.game_path_var.set(os.path.join(selected, "Duskers_Data"))
            else:
                self.game_path_var.set(selected)
            self.check_status()

    def get_game_path(self):
        p = self.game_path_var.get().strip()
        if os.path.isdir(p):
            if os.path.exists(os.path.join(p, "resources.assets")):
                return p
            sub = os.path.join(p, "Duskers_Data")
            if os.path.isdir(sub) and os.path.exists(os.path.join(sub, "resources.assets")):
                return sub
        return None

    def check_status(self):
        game_path = self.get_game_path()
        if not game_path:
            if self.img_led_red:
                self.path_led_lbl.config(image=self.img_led_red)
                self.lang_led.config(image=self.img_led_red)
                self.backup_led.config(image=self.img_led_red)
            self.status_lbl.config(text="Папка Duskers_Data не найдена по указанному пути", fg="#ff4444")
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Недоступно (укажите папку)", fg="#ff4444")
            self.backup_status_lbl.config(text="РЕЗЕРВНАЯ КОПИЯ: Недоступно", fg="#7a92a5")
            self.install_btn.config(state="disabled", bg="#16221c")
            self.restore_btn.config(state="disabled", bg="#201616")
            self.launch_btn.config(state="disabled", bg="#101720")
            self.open_dir_btn.config(state="disabled", bg="#101720")
            return

        if self.img_led_green:
            self.path_led_lbl.config(image=self.img_led_green)
        self.status_lbl.config(text=f"Игра обнаружена: {game_path}", fg="#00ff66")
        self.install_btn.config(state="normal", bg="#006b37")
        self.launch_btn.config(state="normal", bg="#141e2b")
        self.open_dir_btn.config(state="normal", bg="#141e2b")

        # Проверка наличия бэкапа
        backup_dir = os.path.join(game_path, "backup_en")
        backup_res = os.path.join(backup_dir, "resources.assets")
        backup_dll = os.path.join(backup_dir, "Managed", "Assembly-CSharp.dll")

        has_backup = os.path.exists(backup_res) and os.path.exists(backup_dll)
        if has_backup:
            if self.img_led_green:
                self.backup_led.config(image=self.img_led_green)
            self.backup_status_lbl.config(
                text=f"РЕЗЕРВНАЯ КОПИЯ: Сохранена ({backup_dir})", 
                fg="#00ff66"
            )
            self.restore_btn.config(state="normal", bg="#3d1b1b")
        else:
            if self.img_led_yellow:
                self.backup_led.config(image=self.img_led_yellow)
            self.backup_status_lbl.config(
                text="РЕЗЕРВНАЯ КОПИЯ: Отсутствует (будет создана при первой установке)", 
                fg="#ffbb33"
            )
            self.restore_btn.config(state="disabled", bg="#201616")

        # Проверка маркера перевода
        marker_file = os.path.join(game_path, "duskers_rus.installed")
        if os.path.exists(marker_file):
            if self.img_led_green:
                self.lang_led.config(image=self.img_led_green)
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Русский [РУСИФИКАТОР АКТИВЕН]", fg="#00ff66")
        else:
            if self.img_led_yellow:
                self.lang_led.config(image=self.img_led_yellow)
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Английский (Оригинал Steam)", fg="#e0e8f0")

    def set_busy(self, is_busy):
        self.after(0, self._do_set_busy, is_busy)

    def _do_set_busy(self, is_busy):
        state = "disabled" if is_busy else "normal"
        self.install_btn.config(state=state)
        self.restore_btn.config(state=state)
        self.path_entry.config(state=state)
        self.browse_btn.config(state=state)
        self.launch_btn.config(state=state)
        self.open_dir_btn.config(state=state)

    def launch_game(self):
        """Запуск Duskers через Steam протокол или прямой exe"""
        self.log("Запуск Duskers...")
        try:
            os.startfile("steam://rungameid/254320")
            self.log("[✓] Команда запуска отправлена в Steam.")
        except Exception as e:
            game_path = self.get_game_path()
            if game_path:
                root_dir = os.path.dirname(game_path) if os.path.basename(game_path) == "Duskers_Data" else game_path
                exe_file = os.path.join(root_dir, "Duskers.exe")
                if os.path.exists(exe_file):
                    os.startfile(exe_file)
                    self.log(f"[✓] Игра запущена напрямую: {exe_file}")
                    return
            messagebox.showwarning("Внимание", f"Не удалось автоматически запустить игру: {e}\nЗапустите Duskers через Steam.")

    def open_game_folder(self):
        """Открытие папки с игрой в проводнике"""
        game_path = self.get_game_path()
        if game_path:
            root_dir = os.path.dirname(game_path) if os.path.basename(game_path) == "Duskers_Data" else game_path
            if os.path.exists(root_dir):
                os.startfile(root_dir)
                self.log(f"Открыта папка игры: {root_dir}")
                return
        messagebox.showwarning("Внимание", "Папка с игрой не найдена.")

    def start_install(self):
        if is_game_running():
            proceed = messagebox.askyesno(
                "Игра запущена", 
                "Обнаружен запущенный процесс игры Duskers (duskers.exe)!\n\n"
                "Рекомендуется закрыть игру перед установкой русификатора, "
                "чтобы избежать ошибок блокировки файлов Windows.\n\n"
                "Вы уверены, что хотите продолжить установку?"
            )
            if not proceed:
                return
        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self):
        self.set_busy(True)
        game_path = self.get_game_path()
        if not game_path:
            self.after(0, lambda: messagebox.showerror("Ошибка", "Папка с игрой не найдена!"))
            self.set_busy(False)
            return

        self.log("--- НАЧАЛО УСТАНОВКИ РУСИФИКАТОРА ---")

        # 1. Проверяем источник файлов мода
        src_res = os.path.join(MOD_DATA_DIR, "resources.assets")
        src_dll = os.path.join(MOD_DATA_DIR, "Managed", "Assembly-CSharp.dll")

        if not os.path.exists(src_res) or not os.path.exists(src_dll):
            self.log("[!] Ошибка: Вшитые файлы мода не найдены!")
            self.after(0, lambda: messagebox.showerror("Ошибка", f"Файлы мода отсутствуют в:\n{MOD_DATA_DIR}"))
            self.set_busy(False)
            return

        # 2. Создаем бэкап, если его еще нет
        backup_dir = os.path.join(game_path, "backup_en")
        backup_res = os.path.join(backup_dir, "resources.assets")
        backup_dll = os.path.join(backup_dir, "Managed", "Assembly-CSharp.dll")

        if not (os.path.exists(backup_res) and os.path.exists(backup_dll)):
            self.log("Создание резервной копии оригинальных файлов (English)...")
            os.makedirs(os.path.join(backup_dir, "Managed"), exist_ok=True)
            
            orig_res = os.path.join(game_path, "resources.assets")
            orig_dll = os.path.join(game_path, "Managed", "Assembly-CSharp.dll")

            try:
                shutil.copy2(orig_res, backup_res)
                shutil.copy2(orig_dll, backup_dll)

                # Бэкап StreamingAssets
                orig_sa = os.path.join(game_path, "StreamingAssets")
                backup_sa = os.path.join(backup_dir, "StreamingAssets")
                if os.path.exists(orig_sa) and not os.path.exists(backup_sa):
                    shutil.copytree(orig_sa, backup_sa, dirs_exist_ok=True)

                self.log("[✓] Резервная копия оригинала успешно сохранена в backup_en/.")
            except Exception as e:
                self.log(f"[!] Ошибка при создании бэкапа: {e}")
                self.after(0, lambda err=e: messagebox.showerror("Ошибка", f"Не удалось создать резервную копию: {err}"))
                self.set_busy(False)
                return
        else:
            self.log("[i] Резервная копия оригинальных файлов уже сохранена.")

        # 3. Устанавливаем файлы мода
        self.log("Копирование русифицированных ресурсов (resources.assets)...")
        try:
            shutil.copy2(src_res, os.path.join(game_path, "resources.assets"))

            self.log("Копирование переведенной сборки (Assembly-CSharp.dll)...")
            shutil.copy2(src_dll, os.path.join(game_path, "Managed", "Assembly-CSharp.dll"))

            # Копируем StreamingAssets
            src_sa = os.path.join(MOD_DATA_DIR, "StreamingAssets")
            if os.path.exists(src_sa):
                dst_sa = os.path.join(game_path, "StreamingAssets")
                shutil.copytree(src_sa, dst_sa, dirs_exist_ok=True)

            # Создаем маркер установки
            marker_file = os.path.join(game_path, "duskers_rus.installed")
            with open(marker_file, "w", encoding="utf-8") as f:
                f.write("Duskers Russian Localization v1.3")

            self.log("✅ РУСИФИКАТОР УСПЕШНО УСТАНОВЛЕН!")
            self.after(0, self.check_status)
            self.after(0, lambda: messagebox.showinfo("Успех", "Русификатор Duskers успешно установлен!\nПриятной игры!"))
        except Exception as e:
            self.log(f"[!] Ошибка при установке файлов: {e}")
            self.after(0, lambda err=e: messagebox.showerror("Ошибка", f"Не удалось скопировать файлы: {err}"))

        self.set_busy(False)

    def start_restore(self):
        if is_game_running():
            proceed = messagebox.askyesno(
                "Игра запущена", 
                "Обнаружен запущенный процесс игры Duskers (duskers.exe)!\n\n"
                "Рекомендуется закрыть игру перед восстановлением файлов, "
                "чтобы избежать ошибок блокировки файлов Windows.\n\n"
                "Вы уверены, что хотите продолжить восстановление?"
            )
            if not proceed:
                return

        confirm = messagebox.askyesno(
            "Подтверждение", 
            "Вы действительно хотите восстановить оригинальную английскую версию игры?"
        )
        if confirm:
            threading.Thread(target=self._restore_thread, daemon=True).start()

    def _restore_thread(self):
        self.set_busy(True)
        game_path = self.get_game_path()
        if not game_path:
            self.set_busy(False)
            return

        self.log("--- ВОССТАНОВЛЕНИЕ ОРИГИНАЛЬНОГО ЯЗЫКА (ENGLISH) ---")
        backup_dir = os.path.join(game_path, "backup_en")
        backup_res = os.path.join(backup_dir, "resources.assets")
        backup_dll = os.path.join(backup_dir, "Managed", "Assembly-CSharp.dll")

        if not os.path.exists(backup_res) or not os.path.exists(backup_dll):
            self.log("[!] Ошибка: Резервная копия не найдена!")
            self.after(0, lambda: messagebox.showerror(
                "Ошибка", 
                "Резервная копия не найдена!\n\nВы можете восстановить оригинальные файлы через Steam:\nПравый клик по игре -> Свойства -> Установленные файлы -> Проверить целостность файлов."
            ))
            self.set_busy(False)
            return

        try:
            self.log("Восстановление оригинального resources.assets...")
            shutil.copy2(backup_res, os.path.join(game_path, "resources.assets"))

            self.log("Восстановление оригинального Assembly-CSharp.dll...")
            shutil.copy2(backup_dll, os.path.join(game_path, "Managed", "Assembly-CSharp.dll"))

            backup_sa = os.path.join(backup_dir, "StreamingAssets")
            if os.path.exists(backup_sa):
                self.log("Восстановление оригинального StreamingAssets...")
                dst_sa = os.path.join(game_path, "StreamingAssets")
                shutil.copytree(backup_sa, dst_sa, dirs_exist_ok=True)

            marker_file = os.path.join(game_path, "duskers_rus.installed")
            if os.path.exists(marker_file):
                os.remove(marker_file)

            self.log("✅ ОРИГИНАЛЬНАЯ АНГЛИЙСКАЯ ВЕРСИЯ ВОССТАНОВЛЕНА!")
            self.after(0, self.check_status)
            self.after(0, lambda: messagebox.showinfo("Готово", "Оригинальная английская версия игры успешно восстановлена!"))
        except Exception as e:
            self.log(f"[!] Ошибка при восстановлении: {e}")
            self.after(0, lambda err=e: messagebox.showerror("Ошибка", f"Не удалось восстановить файлы: {err}"))

        self.set_busy(False)

if __name__ == "__main__":
    app = DuskersPatcherGUI()
    app.mainloop()
