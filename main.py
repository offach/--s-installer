import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import requests
import os
import threading
import time
import subprocess
import platform
import json

class DownloadManager:
    def __init__(self, master):
        self.master = master
        self.current_index = 0
        self.selected_options = []
        self.save_path = ""
        self.downloaded_files = []
        self.system = platform.system()  # Windows, Darwin (macOS), Linux
        self.config_error = None
        self.config = self.load_config()
        self.urls = self.build_urls_for_platform()

    def load_config(self):
        """Загрузка конфигурации из JSON файла"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ОШИБКА: Файл конфигурации config.json не найден!\nОжидался путь: {config_path}")
            self.config_error = f"Файл конфигурации config.json не найден!\nОжидался путь: {config_path}"
            return {"downloads": {}, "categories": {}}
        except json.JSONDecodeError as e:
            print(f"ОШИБКА: Ошибка чтения config.json: {e}")
            self.config_error = f"Ошибка чтения config.json: {e}"
            return {"downloads": {}, "categories": {}}

    def build_urls_for_platform(self):
        """Построение словаря URL для текущей платформы"""
        urls = {}
        downloads = self.config.get("downloads", {})
        
        for name, platforms in downloads.items():
            platform_key = "Windows" if self.system == "Windows" else "Darwin" if self.system == "Darwin" else None
            if platform_key and platform_key in platforms:
                platform_info = platforms[platform_key]
                if "url" in platform_info and "filename" in platform_info:
                    urls[name] = (platform_info["url"], platform_info["filename"])
        
        return urls

    def resolve_redirect(self, url):
        """Разрешение редиректов для получения финального URL"""
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.url
        except Exception:
            # Если HEAD не работает, пробуем GET
            try:
                response = requests.get(url, stream=True, timeout=10, allow_redirects=True)
                return response.url
            except Exception:
                return url  # Возвращаем оригинальный URL если не удалось разрешить

    def start_download(self):
        self.selected_options = [var.get() for var in all_vars if var.get()]
        if not self.selected_options:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите хотя бы один элемент для загрузки.")
            return

        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            return  # Если папка не выбрана, выйти из функции

        self.save_path = os.path.join(folder_selected, "offach installer Загрузки")
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        for widget in download_listbox.winfo_children():
            widget.destroy()
        for option in self.selected_options:
            add_to_download_list(option)

        self.current_index = 0
        self.downloaded_files = []
        self.download_next_file()

    def download_next_file(self):
        if self.current_index >= len(self.selected_options):
            messagebox.showinfo("Загрузка завершена",
                                f"Все файлы были успешно загружены:\n" + "\n".join(self.downloaded_files))
            # Кроссплатформенное открытие папки
            system = platform.system()
            if system == 'Windows':
                os.startfile(self.save_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', self.save_path])
            else:  # Linux и другие
                subprocess.run(['xdg-open', self.save_path])
            return

        option = self.selected_options[self.current_index]
        if option in self.urls:
            url, filename = self.urls[option]
            # Разрешаем редиректы для получения актуального URL
            final_url = self.resolve_redirect(url)
            threading.Thread(target=self.download_browser, args=(final_url, filename, option)).start()
        else:
            # Если программа недоступна для данной платформы
            self.master.after(0, lambda: messagebox.showwarning(
                "Предупреждение", 
                f"{option} недоступен для операционной системы {self.system}"))
            self.current_index += 1
            self.master.after(0, self.download_next_file)

    def update_progress(self, downloaded_size, total_size, filename):
        """Безопасное обновление прогресс-бара из главного потока"""
        if total_size > 0:
            progress = (downloaded_size / total_size) * 100
            progress_var.set(progress)
        else:
            progress_var.set(0)
        current_status_var.set(
            f"Загружается: {filename} ({self.current_index + 1}/{len(self.selected_options)})")

    def download_browser(self, url, filename, option):
        file_path = os.path.join(self.save_path, filename)
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                start_time = time.time()

                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            # Безопасное обновление GUI из главного потока
                            self.master.after(0, self.update_progress, downloaded_size, total_size, filename)

                            elapsed_time = time.time() - start_time
                            # Проверка таймаута только если известен размер файла
                            if total_size > 0 and elapsed_time > 60 and downloaded_size < total_size * 0.05:
                                raise Exception("Превышено время ожидания для загрузки")

                self.downloaded_files.append(filename)
        except Exception as e:
            # Безопасный вызов messagebox из главного потока
            error_msg = f"Произошла ошибка при загрузке {filename}: {e}"
            self.master.after(0, lambda: messagebox.showerror("Ошибка", error_msg))

        self.current_index += 1
        self.master.after(0, self.download_next_file)


def add_to_download_list(item):
    frame = tk.Frame(download_listbox, bg="white")
    frame.pack(fill=tk.X)
    label = tk.Label(frame, text=item, anchor="w", bg="white")
    label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    button = tk.Button(frame, text="Удалить", command=lambda: remove_from_download_list(frame, item))
    button.pack(side=tk.RIGHT)


def remove_from_download_list(frame, item):
    frame.destroy()
    software_vars[item].set("")


def show_info():
    info_window = tk.Toplevel(root)
    info_window.title("Справка")

    info_label = tk.Label(info_window, text="Создатель: offach\nКонтакт: me@offach.ru\n\nСписок ссылок:")
    info_label.pack(padx=10, pady=10)

    links_text = "\n".join([f"{name}: {url[0]}" for name, url in download_manager.urls.items() if name in download_manager.urls])
    links_label = tk.Label(info_window, text=links_text, justify=tk.LEFT, anchor="w")
    links_label.pack(padx=10, pady=10)

    info_window.transient(root)
    info_window.grab_set()
    root.wait_window(info_window)


def create_gui():
    global root, progress_var, current_status_var, all_vars, download_listbox, search_entry, software_vars, all_checkbuttons, download_manager

    root = tk.Tk()
    root.title("offach's installer")
    root.geometry("550x650")  # Задаем фиксированный размер окна
    root.configure(bg="white")
    
    # Создаем download_manager сначала для работы с конфигом
    download_manager = DownloadManager(root)
    
    # Показываем ошибку конфигурации если есть
    if hasattr(download_manager, 'config_error') and download_manager.config_error:
        root.after(100, lambda: messagebox.showerror("Ошибка конфигурации", download_manager.config_error))

    def on_start():
        messagebox.showinfo("Внимание", "Ответственности создатель не несет, используйте на свой риск.")

    root.after(200, on_start)

    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(main_frame, bg="white")
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Прокрутка колесиком мыши
    def on_mouse_wheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    # Creating a search bar
    search_frame = tk.Frame(scrollable_frame, padx=20, pady=10, bg="white")
    search_frame.pack(fill=tk.X)
    search_label = tk.Label(search_frame, text="Поиск", bg="white")
    search_label.pack(side=tk.LEFT)
    search_entry = tk.Entry(search_frame)
    search_entry.pack(fill=tk.X, expand=True)
    search_entry.bind("<KeyRelease>", search_program)

    # Info button
    info_button = tk.Button(scrollable_frame, text="Информация", command=show_info)
    info_button.pack(anchor="ne", padx=10, pady=5)

    # Загрузка категорий из конфига или дефолтные
    categories = download_manager.config.get("categories", {
        "Браузеры": ["Google Chrome", "Mozilla Firefox", "Yandex", "Opera"],
        "СоцСети": ["Discord", "Skype", "Telegram Desktop", "Zoom", "WhatsApp Desktop"],
        "Лаунчеры игр и т.д.": ["Steam", "Epic Games Launcher"],
        "Софт для разработки": ["Visual Studio Code", "JetBrains IntelliJ IDEA", "PyCharm", "Sublime Text"],
        "Полезные утилиты": ["OBS Studio", "7-Zip"],
        "Приложения для гаджетов": ["Logitech G Hub"]
    })
    
    # Фильтруем программы - показываем только доступные для текущей ОС
    available_apps = set(download_manager.urls.keys())
    filtered_categories = {}
    for category, apps in categories.items():
        available = [app for app in apps if app in available_apps]
        if available:  # Показываем категорию только если есть доступные программы
            filtered_categories[category] = available
    categories = filtered_categories

    all_vars = []
    all_checkbuttons = []
    software_vars = {}

    cat_frame = tk.Frame(scrollable_frame, padx=10, pady=10, bg="white")
    cat_frame.pack(fill=tk.BOTH, expand=True)

    row = 0
    col = 0
    for category, items in categories.items():
        if col >= 3:
            col = 0
            row += 1
        frame = tk.LabelFrame(cat_frame, text=category, padx=10, pady=10, bg="white")
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        for item in items:
            var = tk.StringVar(value="")
            chk = tk.Checkbutton(frame, text=item, variable=var, onvalue=item, offvalue="",
                                 command=update_download_list, bg="white")
            chk.pack(anchor=tk.W)
            all_vars.append(var)
            all_checkbuttons.append(chk)
            software_vars[item] = var

        col += 1

    # Listbox to show selected programs for download
    download_listbox_frame = tk.LabelFrame(scrollable_frame, text="Список загрузок", padx=10, pady=10, bg="white")
    download_listbox_frame.pack(fill=tk.X, pady=5)
    download_listbox = tk.Frame(download_listbox_frame, bg="white")
    download_listbox.pack(fill=tk.X, pady=5)

    current_status_var = tk.StringVar()
    current_status_label = tk.Label(scrollable_frame, textvariable=current_status_var, bg="white")
    current_status_label.pack(pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(scrollable_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, pady=10)

    # Показываем информацию о текущей ОС
    system_info = tk.Label(scrollable_frame, 
                          text=f"Платформа: {platform.system()} ({platform.platform()})", 
                          bg="white", fg="gray")
    system_info.pack(pady=5)

    download_button = tk.Button(scrollable_frame, text="Загрузить", command=download_manager.start_download)
    download_button.pack(pady=10)

    root.mainloop()


def update_download_list():
    # Clear the download list frame
    for widget in download_listbox.winfo_children():
        widget.destroy()

    for var in all_vars:
        if var.get():
            add_to_download_list(var.get())


def search_program(event):
    search_text = search_entry.get().lower()
    for chk in all_checkbuttons:
        if search_text in chk.cget("text").lower():
            chk.config(fg="red")
        else:
            chk.config(fg="black")

    if search_text == "":
        for chk in all_checkbuttons:
            chk.config(fg="black")


if __name__ == "__main__":
    create_gui()
