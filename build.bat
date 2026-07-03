@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul

echo.
echo === Сборка TelegraphParser.exe ===
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ОШИБКА] Python не найден в PATH.
  echo Установи Python 3 и включи "Add Python to PATH".
  pause
  exit /b 1
)

echo Ставлю зависимости...
python -m pip install --upgrade pip
python -m pip install pyinstaller requests beautifulsoup4
if errorlevel 1 (
  echo [ОШИБКА] Не удалось установить зависимости.
  pause
  exit /b 1
)

echo.
echo Собираю exe...
python -m PyInstaller --onefile --console --name TelegraphParser telegraph_parser.py
if errorlevel 1 (
  echo [ОШИБКА] Сборка не удалась.
  pause
  exit /b 1
)

echo.
echo === Готово ===
echo Файл: "%~dp0dist\TelegraphParser.exe"
echo Скопируй его куда удобно и запускай двойным кликом.
echo (конфиги keywords.txt/patterns.txt и база создадутся рядом с exe сами)
echo.
pause
