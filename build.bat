@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install nuitka zstandard ordered-set

echo Building ClaudeMonitor with Nuitka...
python -m nuitka --standalone --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=tk-inter ^
    --include-data-dir=assets=assets ^
    --output-filename=ClaudeMonitor.exe ^
    --output-dir=dist ^
    --assume-yes-for-downloads ^
    --msvc=latest ^
    --company-name=ClaudeMonitor ^
    --product-name=ClaudeMonitor ^
    --file-version=1.0.1 ^
    --file-description="Claude AI Usage Monitor" ^
    --copyright="MIT License" ^
    main.py

echo.
echo Build complete!
echo Output: dist\ClaudeMonitor.exe
pause
