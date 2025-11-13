#!/usr/bin/env python3
"""
Скрипт сборки для Windows
Создает исполняемый файл .exe из main.py
"""
import os
import subprocess
import sys

def build_windows():
    print("🔨 Сборка для Windows...")
    
    # Проверяем наличие PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller найден")
    except ImportError:
        print("❌ PyInstaller не установлен. Устанавливаю...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Проверяем наличие зависимостей
    print("📦 Проверка зависимостей...")
    try:
        import requests
        print("✓ requests найден")
    except ImportError:
        print("❌ requests не установлен. Устанавливаю...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Параметры сборки
    app_name = "Apps installer"
    main_script = "main.py"
    icon_file = None  # Можно добавить .ico файл если есть
    
    # Команда PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",  # Один исполняемый файл
        "--windowed",  # Без консоли
        "--name", app_name,
        "--clean",  # Очистить перед сборкой
        main_script
    ]
    
    # Добавляем конфигурационный файл
    cmd.extend(["--add-data", "config.json;."])
    
    # Добавляем иконку если есть
    if icon_file and os.path.exists(icon_file):
        cmd.extend(["--icon", icon_file])
    
    print(f"🚀 Запуск PyInstaller...")
    print(f"Команда: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print(f"\n✅ Сборка завершена!")
        print(f"📁 Исполняемый файл: dist\\{app_name}.exe")
        print(f"📁 Временные файлы: build\\")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка сборки: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_windows()

