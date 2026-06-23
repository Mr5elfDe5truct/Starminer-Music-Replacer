@echo off
setlocal
echo Starting Starminer Music Replacer GUI...
python "%~dp0gui.py"
if %errorlevel% neq 0 (
    echo Error: Failed to start the GUI. Make sure Python 3 is installed.
    pause
)
