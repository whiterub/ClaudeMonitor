@echo off
echo === ClaudeMonitor Standalone Build (for MSIX packaging) ===
echo.

echo Installing dependencies...
pip install -r requirements.txt
pip install nuitka zstandard ordered-set

echo.
echo Building ClaudeMonitor with Nuitka (standalone mode)...
python -m nuitka --standalone ^
    --windows-console-mode=disable ^
    --enable-plugin=tk-inter ^
    --include-data-dir=assets=assets ^
    --output-filename=ClaudeMonitor.exe ^
    --output-dir=dist ^
    --assume-yes-for-downloads ^
    --mingw64 ^
    --windows-icon-from-ico=msix\Assets\icon.ico ^
    --company-name=ClaudeMonitor ^
    --product-name=ClaudeMonitor ^
    --file-version=1.0.3 ^
    --file-description="Claude AI Usage Monitor" ^
    --copyright="MIT License" ^
    main.py

echo.
echo Build complete!
echo Output directory: dist\main.dist\
echo Run dist\main.dist\ClaudeMonitor.exe to test
pause
