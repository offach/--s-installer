#!/bin/bash
# Скрипт сборки для macOS (альтернативный вариант)

echo "🔨 Сборка для macOS..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    exit 1
fi

# Устанавливаем зависимости если нужно
if [ ! -f "venv/bin/activate" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Установка зависимостей..."
pip install -r requirements.txt
pip install pyinstaller

# Запускаем Python скрипт сборки
python3 build_macos.py

# Создаем DMG если нужно (опционально)
if [ -f "dist/Apps installer" ]; then
    echo "📦 Создание DMG файла..."
    hdiutil create -volname "Apps installer" -srcfolder "dist/Apps installer" -ov -format UDZO "dist/Apps installer.dmg" 2>/dev/null || echo "⚠️  Не удалось создать DMG (возможно не критично)"
fi

echo "✅ Готово!"

