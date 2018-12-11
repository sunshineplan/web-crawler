@echo off
pip install pyinstaller -U > nul
pyinstaller -F NB.py
pause
