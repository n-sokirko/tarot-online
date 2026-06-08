@echo off
REM Настраивает автопостинг 3 раза в день: 9:00, 14:00, 20:00
REM Запусти этот файл один раз от имени администратора

SET SCRIPT_PATH=%~dp0run_autopost.bat

echo Создаю задачу в планировщике Windows...

schtasks /create /tn "TarotAutoPost_Morning" /tr "%SCRIPT_PATH%" /sc daily /st 09:00 /f
schtasks /create /tn "TarotAutoPost_Afternoon" /tr "%SCRIPT_PATH%" /sc daily /st 14:00 /f
schtasks /create /tn "TarotAutoPost_Evening" /tr "%SCRIPT_PATH%" /sc daily /st 20:00 /f

echo.
echo Готово! Задачи созданы:
echo   09:00 - утренний пост
echo   14:00 - дневной пост
echo   20:00 - вечерний пост
echo.
echo Проверь в Планировщике задач Windows (taskschd.msc)
pause
