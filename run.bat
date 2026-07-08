@echo off
setlocal EnableDelayedExpansion

title Suduku-Arena - Local Server

rem Move to the folder this .bat file lives in (project root)
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo ============================================
echo   Suduku-Arena - Starting Local Server
echo ============================================
echo Project folder: %ROOT%
echo.

rem ---- 1. Find Python ----
where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PY=py -3"
    ) else (
        echo [ERROR] Python was not found on your PATH.
        echo Install Python 3.10+ from https://www.python.org/downloads/
        echo ^(tick "Add python.exe to PATH" during install^)
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Using: %PY%

rem ---- 2. Install dependencies if missing ----
%PY% -c "import bcrypt, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages from requirements.txt ...
    %PY% -m pip install -r "%ROOT%\requirements.txt" --quiet
    if errorlevel 1 (
        echo [ERROR] pip install failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependencies already installed.
)

rem ---- 3. Read PORT from .env (default 8888) ----
set "PORT=8888"
if exist "%ROOT%\.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("%ROOT%\.env") do (
        if /i "%%a"=="PORT" set "PORT=%%b"
    )
)
set "URL=http://127.0.0.1:%PORT%/"

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

rem ---- 4. Open the browser a couple seconds after the server should be up ----
rem     (runs in a tiny background helper so it doesn't block the server below)
start "" cmd /c "timeout /t 2 /nobreak >nul & start "" "%URL%""

echo.
echo ============================================
echo   Suduku-Arena is running at %URL%
echo   Press CTRL+C to stop the server.
echo   ^(If asked "Terminate batch job (Y/N)?", press Y^)
echo ============================================
echo.

rem ---- 5. Run the server IN THIS WINDOW (foreground) ----
rem     This is what makes Ctrl+C actually stop it, same as a normal dev server.
%PY% "%ROOT%\backend\server.py"

echo.
echo Server stopped.
pause
exit /b 0
