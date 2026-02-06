@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building ClaudeView...
pyinstaller --onefile --windowed --icon=assets\icon.ico ^
    --add-data "assets;assets" ^
    --name ClaudeView ^
    main.py

echo.
echo Build complete!
echo Output: dist\ClaudeView.exe
pause
