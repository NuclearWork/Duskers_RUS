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
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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

DEFAULT_STEAM_PATHS = [
    r"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"C:\Program Files (x86)\Steam\steamapps\common\Duskers\Duskers_Data",
    r"C:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"D:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"E:\SteamLibrary\steamapps\common\Duskers\Duskers_Data",
    r"F:\SteamLibrary\steamapps\common\Duskers\Duskers_Data"
]

def find_game_dir():
    # Проверяем переменные окружения
    env_path = os.environ.get("DUSKERS_DIR")
    if env_path and os.path.isdir(env_path):
        if os.path.exists(os.path.join(env_path, "resources.assets")):
            return env_path
        if os.path.isdir(os.path.join(env_path, "Duskers_Data")):
            return os.path.join(env_path, "Duskers_Data")

    # Проверяем стандартные пути
    for p in DEFAULT_STEAM_PATHS:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "resources.assets")):
            return p
    return ""

class DuskersPatcherGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Duskers — Менеджер Русификатора [v1.2]")
        self.geometry("680x560")
        self.minsize(620, 500)
        self.configure(bg="#0c1017")

        self.game_path_var = tk.StringVar(value=find_game_dir())

        self.setup_ui()
        self.check_status()

    def setup_ui(self):
        # Стилизация ttk
        style = ttk.Style(self)
        style.theme_use("clam")

        # Шрифт
        self.font_term = ("Consolas", 10)
        self.font_term_bold = ("Consolas", 10, "bold")
        self.font_header = ("Consolas", 14, "bold")
        self.font_title = ("Consolas", 16, "bold")

        # Верхняя панель (Заголовок в терминальном стиле)
        header_frame = tk.Frame(self, bg="#111722", bd=1, relief="solid", highlightbackground="#1b2a3f", highlightthickness=1)
        header_frame.pack(fill="x", padx=16, pady=(16, 10))

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

        # Секция выбора папки с игрой
        path_frame = tk.LabelFrame(
            self, 
            text=" [ ПАПКА С ИГРОЙ ] ", 
            fg="#38ef7d", 
            bg="#0c1017", 
            font=self.font_term_bold, 
            bd=1, 
            relief="groove"
        )
        path_frame.pack(fill="x", padx=16, pady=8)

        path_inner = tk.Frame(path_frame, bg="#0c1017")
        path_inner.pack(fill="x", padx=10, pady=8)

        self.path_entry = tk.Entry(
            path_inner, 
            textvariable=self.game_path_var, 
            font=self.font_term, 
            bg="#161e2b", 
            fg="#e0e8f0", 
            insertbackground="#00ff66",
            bd=1,
            relief="solid"
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)
        self.path_entry.bind("<KeyRelease>", lambda e: self.check_status())

        browse_btn = tk.Button(
            path_inner, 
            text="Обзор...", 
            font=self.font_term_bold, 
            bg="#202d3f", 
            fg="#ffffff", 
            activebackground="#2c3e55", 
            activeforeground="#00ff66",
            bd=0, 
            padx=14, 
            pady=4,
            cursor="hand2",
            command=self.browse_folder
        )
        browse_btn.pack(side="right")

        # Статус
        self.status_lbl = tk.Label(
            path_frame, 
            text="Поиск игры...", 
            font=self.font_term, 
            bg="#0c1017", 
            fg="#ffbb33", 
            anchor="w"
        )
        self.status_lbl.pack(fill="x", padx=10, pady=(0, 6))

        # Информационная карточка состояния
        self.info_frame = tk.Frame(self, bg="#111722", bd=1, relief="solid", highlightbackground="#1b2a3f", highlightthickness=1)
        self.info_frame.pack(fill="x", padx=16, pady=6)

        self.lang_status_lbl = tk.Label(
            self.info_frame, 
            text="ТЕКУЩИЙ ЯЗЫК: Не определен", 
            font=self.font_term_bold, 
            bg="#111722", 
            fg="#ffffff"
        )
        self.lang_status_lbl.pack(anchor="w", padx=12, pady=(6, 2))

        self.backup_status_lbl = tk.Label(
            self.info_frame, 
            text="РЕЗЕРВНАЯ КОПИЯ (BACKUP): Не найдена", 
            font=self.font_term, 
            bg="#111722", 
            fg="#7a92a5"
        )
        self.backup_status_lbl.pack(anchor="w", padx=12, pady=(0, 6))

        # Панель кнопок действий
        actions_frame = tk.Frame(self, bg="#0c1017")
        actions_frame.pack(fill="x", padx=16, pady=10)

        self.install_btn = tk.Button(
            actions_frame, 
            text="✔ УСТАНОВИТЬ РУСИФИКАТОР", 
            font=("Consolas", 11, "bold"), 
            bg="#008844", 
            fg="#ffffff", 
            activebackground="#00aa55", 
            activeforeground="#ffffff",
            bd=0, 
            pady=10,
            cursor="hand2",
            command=self.start_install
        )
        self.install_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.restore_btn = tk.Button(
            actions_frame, 
            text="↺ ВОССТАНОВИТЬ ОРИГИНАЛ (EN)", 
            font=("Consolas", 11, "bold"), 
            bg="#3a2222", 
            fg="#ff8888", 
            activebackground="#552c2c", 
            activeforeground="#ffffff",
            bd=0, 
            pady=10,
            cursor="hand2",
            command=self.start_restore
        )
        self.restore_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Консольный лог действий
        log_frame = tk.LabelFrame(
            self, 
            text=" [ СИСТЕМНЫЙ ЖУРНАЛ ] ", 
            fg="#38ef7d", 
            bg="#0c1017", 
            font=self.font_term_bold, 
            bd=1, 
            relief="groove"
        )
        log_frame.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self.log_text = tk.Text(
            log_frame, 
            font=("Consolas", 9), 
            bg="#070a0f", 
            fg="#00ff66", 
            insertbackground="#00ff66", 
            bd=0,
            wrap="word",
            padx=8,
            pady=8
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview, bg="#111722")
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log("Система инициализирована. Версия русификатора: v1.2")

    def log(self, message):
        self.log_text.insert("end", f"> {message}\n")
        self.log_text.see("end")

    def browse_folder(self):
        selected = filedialog.askdirectory(title="Выберите папку с игрой Duskers или папку Duskers_Data")
        if selected:
            # Проверяем, выбрал ли пользователь корень Duskers или саму Duskers_Data
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
            self.status_lbl.config(text="[X] Папка Duskers_Data не найдена по указанному пути", fg="#ff4444")
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Недоступно (укажите папку)", fg="#ff4444")
            self.backup_status_lbl.config(text="РЕЗЕРВНАЯ КОПИЯ: Недоступно", fg="#7a92a5")
            self.install_btn.config(state="disabled", bg="#223328")
            self.restore_btn.config(state="disabled", bg="#281e1e")
            return

        self.status_lbl.config(text=f"[✓] Игра обнаружена: {game_path}", fg="#00ff66")
        self.install_btn.config(state="normal", bg="#008844")

        # Проверка наличия бэкапа
        backup_dir = os.path.join(game_path, "backup_en")
        backup_res = os.path.join(backup_dir, "resources.assets")
        backup_dll = os.path.join(backup_dir, "Managed", "Assembly-CSharp.dll")

        has_backup = os.path.exists(backup_res) and os.path.exists(backup_dll)
        if has_backup:
            self.backup_status_lbl.config(
                text=f"РЕЗЕРВНАЯ КОПИЯ: Сохранена ({backup_dir})", 
                fg="#00ff66"
            )
            self.restore_btn.config(state="normal", bg="#552222")
        else:
            self.backup_status_lbl.config(
                text="РЕЗЕРВНАЯ КОПИЯ: Отсутствует (будет создана при первой установке)", 
                fg="#ffbb33"
            )
            self.restore_btn.config(state="disabled", bg="#281e1e")

        # Проверка маркера перевода
        marker_file = os.path.join(game_path, "duskers_rus.installed")
        if os.path.exists(marker_file):
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Русский [РУСИФИКАТОР АКТИВЕН]", fg="#00ff66")
        else:
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Английский (Оригинал)", fg="#e0e8f0")

    def set_busy(self, is_busy):
        state = "disabled" if is_busy else "normal"
        self.install_btn.config(state=state)
        self.restore_btn.config(state=state)
        self.path_entry.config(state=state)

    def start_install(self):
        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self):
        self.set_busy(True)
        game_path = self.get_game_path()
        if not game_path:
            messagebox.showerror("Ошибка", "Папка с игрой не найдена!")
            self.set_busy(False)
            return

        self.log("--- НАЧАЛО УСТАНОВКИ РУСИФИКАТОРА ---")

        # 1. Проверяем источник файлов мода
        src_res = os.path.join(MOD_DATA_DIR, "resources.assets")
        src_dll = os.path.join(MOD_DATA_DIR, "Managed", "Assembly-CSharp.dll")

        if not os.path.exists(src_res) or not os.path.exists(src_dll):
            self.log("[!] Ошибка: Вшитые файлы мода не найдены!")
            messagebox.showerror("Ошибка", f"Файлы мода отсутствуют в: {MOD_DATA_DIR}")
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
                self.log(f"[✓] Бэкап сохранен в папку: {backup_dir}")
            except Exception as e:
                self.log(f"[!] Ошибка при создании бэкапа: {e}")
                messagebox.showerror("Ошибка", f"Не удалось создать бэкап: {e}")
                self.set_busy(False)
                return
        else:
            self.log("Резервная копия оригинальных файлов уже существует.")

        # 3. Устанавливаем файлы мода
        self.log("Копирование русифицированных ресурсов (resources.assets)...")
        try:
            shutil.copy2(src_res, os.path.join(game_path, "resources.assets"))
            self.log("Копирование переведенной сборки (Assembly-CSharp.dll)...")
            shutil.copy2(src_dll, os.path.join(game_path, "Managed", "Assembly-CSharp.dll"))

            # Копируем StreamingAssets, если есть
            src_sa = os.path.join(MOD_DATA_DIR, "StreamingAssets")
            if os.path.exists(src_sa):
                dst_sa = os.path.join(game_path, "StreamingAssets")
                shutil.copytree(src_sa, dst_sa, dirs_exist_ok=True)

            # Записываем маркер установки
            with open(os.path.join(game_path, "duskers_rus.installed"), "w", encoding="utf-8") as f:
                f.write("Duskers Russian Localization v1.2")

            self.log("✅ РУСИФИКАТОР УСПЕШНО УСТАНОВЛЕН!")
            self.check_status()
            messagebox.showinfo("Успех", "Русификатор Duskers успешно установлен!\nПриятной игры!")
        except Exception as e:
            self.log(f"[!] Ошибка при установке файлов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось скопировать файлы: {e}")

        self.set_busy(False)

    def start_restore(self):
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
            messagebox.showerror(
                "Ошибка", 
                "Резервная копия не найдена!\n\nВы можете восстановить оригинальные файлы через Steam:\nПравый клик по игре -> Свойства -> Установленные файлы -> Проверить целостность файлов."
            )
            self.set_busy(False)
            return

        try:
            self.log("Восстановление оригинального resources.assets...")
            shutil.copy2(backup_res, os.path.join(game_path, "resources.assets"))

            self.log("Восстановление оригинального Assembly-CSharp.dll...")
            shutil.copy2(backup_dll, os.path.join(game_path, "Managed", "Assembly-CSharp.dll"))

            marker_file = os.path.join(game_path, "duskers_rus.installed")
            if os.path.exists(marker_file):
                os.remove(marker_file)

            self.log("✅ ОРИГИНАЛЬНАЯ АНГЛИЙСКАЯ ВЕРСИЯ ВОССТАНОВЛЕНА!")
            self.check_status()
            messagebox.showinfo("Готово", "Оригинальная английская версия игры успешно восстановлена!")
        except Exception as e:
            self.log(f"[!] Ошибка при восстановлении: {e}")
            messagebox.showerror("Ошибка", f"Не удалось восстановить файлы: {e}")

        self.set_busy(False)

def main():
    app = DuskersPatcherGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
