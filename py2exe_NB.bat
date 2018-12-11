@echo off
pip install pyinstaller -U > nul
pyinstaller -F NB.py -i ico/NB.ico
pause
