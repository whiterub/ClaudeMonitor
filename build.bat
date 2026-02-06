@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building ClaudeMonitor...
pyinstaller --onefile --windowed --icon=assets\icon.ico ^
    --add-data "assets;assets" ^
    --name ClaudeMonitor ^
    main.py

echo.
echo Build complete!
echo Output: dist\ClaudeMonitor.exe
pause
