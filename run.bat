@echo off

REM AI Tuber Test が実行中かどうかを確認
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq mamin.py" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo AI Tuber Test は既に実行中です。
) else (
    echo AI Tuber Test を起動します。
    venv\scripts\activate
    python main.py
)
pause