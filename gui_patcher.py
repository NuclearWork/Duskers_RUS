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

def is_game_running():
    """Проверяет, запущена ли сейчас игра Duskers"""
    try:
        import psutil
        for p in psutil.process_iter(['name']):
            name = p.info.get('name')
            if name and 'duskers' in name.lower():
                return True
    except Exception:
        try:
            out = subprocess.check_output("tasklist", shell=True, text=True, errors="ignore")
            return "duskers.exe" in out.lower()
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

        self.title("Duskers — Менеджер Русификатора [v1.2]")
        self.geometry("700x590")
        self.minsize(640, 520)
        self.configure(bg="#0c1017")

        self.game_path_var = tk.StringVar(value=find_game_dir())

        self.setup_ui()
        self.check_status()

    def setup_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")

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
        path_frame.pack(fill="x", padx=16, pady=6)

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
        self.info_frame.pack(fill="x", padx=16, pady=4)

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

        # Панель основных действий (Установить / Восстановить)
        actions_frame = tk.Frame(self, bg="#0c1017")
        actions_frame.pack(fill="x", padx=16, pady=6)

        self.install_btn = tk.Button(
            actions_frame, 
            text="✔ УСТАНОВИТЬ РУСИФИКАТОР", 
            font=("Consolas", 11, "bold"), 
            bg="#008844", 
            fg="#ffffff", 
            activebackground="#00aa55", 
            activeforeground="#ffffff", 
            bd=0, 
            pady=9,
            cursor="hand2",
            command=self.start_install
        )
        self.install_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.restore_btn = tk.Button(
            actions_frame, 
            text="↺ ВОССТАНОВИТЬ ОРИГИНАЛ (EN)", 
            font=("Consolas", 11, "bold"), 
            bg="#3a2222", 
            fg="#ff8888", 
            activebackground="#552c2c", 
            activeforeground="#ffffff", 
            bd=0, 
            pady=9,
            cursor="hand2",
            command=self.start_restore
        )
        self.restore_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Вспомогательная панель быстрых действий (Запуск игры / Открыть папку)
        sub_actions_frame = tk.Frame(self, bg="#0c1017")
        sub_actions_frame.pack(fill="x", padx=16, pady=(0, 6))

        self.launch_btn = tk.Button(
            sub_actions_frame, 
            text="▶ ЗАПУСТИТЬ ИГРУ (STEAM)", 
            font=("Consolas", 9, "bold"), 
            bg="#1b2a3f", 
            fg="#38ef7d", 
            activebackground="#263d5c", 
            activeforeground="#00ff66", 
            bd=0, 
            pady=5,
            cursor="hand2",
            command=self.launch_game
        )
        self.launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.open_dir_btn = tk.Button(
            sub_actions_frame, 
            text="📁 ОТКРЫТЬ ПАПКУ ИГРЫ", 
            font=("Consolas", 9, "bold"), 
            bg="#1b2a3f", 
            fg="#a0b8d0", 
            activebackground="#263d5c", 
            activeforeground="#ffffff", 
            bd=0, 
            pady=5,
            cursor="hand2",
            command=self.open_game_folder
        )
        self.open_dir_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

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
        log_frame.pack(fill="both", expand=True, padx=16, pady=(2, 14))

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
        """Потокобезопасный вывод сообщения в консоль GUI"""
        self.after(0, self._do_log, message)

    def _do_log(self, message):
        self.log_text.insert("end", f"> {message}\n")
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
            self.status_lbl.config(text="[X] Папка Duskers_Data не найдена по указанному пути", fg="#ff4444")
            self.lang_status_lbl.config(text="ТЕКУЩИЙ ЯЗЫК: Недоступно (укажите папку)", fg="#ff4444")
            self.backup_status_lbl.config(text="РЕЗЕРВНАЯ КОПИЯ: Недоступно", fg="#7a92a5")
            self.install_btn.config(state="disabled", bg="#223328")
            self.restore_btn.config(state="disabled", bg="#281e1e")
            self.launch_btn.config(state="disabled")
            self.open_dir_btn.config(state="disabled")
            return

        self.status_lbl.config(text=f"[✓] Игра обнаружена: {game_path}", fg="#00ff66")
        self.install_btn.config(state="normal", bg="#008844")
        self.launch_btn.config(state="normal")
        self.open_dir_btn.config(state="normal")

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
        self.after(0, self._do_set_busy, is_busy)

    def _do_set_busy(self, is_busy):
        state = "disabled" if is_busy else "normal"
        self.install_btn.config(state=state)
        self.restore_btn.config(state=state)
        self.path_entry.config(state=state)
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
            messagebox.showwarning(
                "Игра запущена", 
                "Игра Duskers сейчас запущена!\n\nПожалуйста, закройте игру перед установкой русификатора, чтобы файлы не были заблокированы Windows."
            )
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

                self.log(f"[✓] Бэкап сохранен в: {backup_dir}")
            except Exception as e:
                self.log(f"[!] Ошибка при создании бэкапа: {e}")
                self.after(0, lambda err=e: messagebox.showerror("Ошибка", f"Не удалось создать бэкап: {err}"))
                self.set_busy(False)
                return
        else:
            self.log("Резервная копия оригинальных файлов уже сохранена.")

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

            # Записываем маркер установки
            with open(os.path.join(game_path, "duskers_rus.installed"), "w", encoding="utf-8") as f:
                f.write("Duskers Russian Localization v1.2")

            self.log("✅ РУСИФИКАТОР УСПЕШНО УСТАНОВЛЕН!")
            self.after(0, self.check_status)
            self.after(0, lambda: messagebox.showinfo("Успех", "Русификатор Duskers успешно установлен!\nПриятной игры!"))
        except Exception as e:
            self.log(f"[!] Ошибка при установке файлов: {e}")
            self.after(0, lambda err=e: messagebox.showerror("Ошибка", f"Не удалось скопировать файлы: {err}"))

        self.set_busy(False)

    def start_restore(self):
        if is_game_running():
            messagebox.showwarning(
                "Игра запущена", 
                "Игра Duskers сейчас запущена!\n\nПожалуйста, закройте игру перед восстановлением файлов, чтобы они не были заблокированы Windows."
            )
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

def main():
    app = DuskersPatcherGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
