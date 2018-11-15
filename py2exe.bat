@echo off
pip install pyinstaller -U > nul
pyinstaller -F Main.py -i Main.ico
pause
