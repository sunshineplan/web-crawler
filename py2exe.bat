@echo off
pip install pyinstaller -U > nul
pyinstaller -F Main.py -i ico/Main.ico
pause
