@echo off
cd /d "%~dp0"
python autopost.py >> autopost.log 2>&1
