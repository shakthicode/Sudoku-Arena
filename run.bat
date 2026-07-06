@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Sudoko-Arena Launcher

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo.
echo ====================================================
echo             Sudoko-Arena Local Launcher            
echo ====================================================
echo Directory: %ROOT%
echo.

rem ---- Find Python ----
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
    ) else (
        echo [ERROR] Python was not found on your PATH.
        echo Please install Python 3 and check "Add python.exe to PATH".
        echo.
        pause
        exit /b 1
    )
)

rem ---- Load Port from .env or default to 8888 ----
set "PORT=8888"
if exist "%ROOT%\.env" (
    for /f "tokens=1,2 delims==" %%i in (%ROOT%\.env) do (
        set "key=%%i"
        set "val=%%j"
        rem Trim spaces
        for /f "tokens=*" %%a in ("!key!") do set "key=%%a"
        for /f "tokens=*" %%a in ("!val!") do set "val=%%a"
        if "!key!"=="PORT" set "PORT=!val!"
    )
)

set "URL=http://localhost:%PORT%/"

rem ---- Check/Install dependencies ----
echo [INFO] Verifying Python dependencies...
%PYTHON_CMD% -c "import bcrypt, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required libraries from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [WARN] Failed to install dependencies. Running anyway...
    )
) else (
    echo [INFO] All dependencies verified.
)

rem ---- Start Python Server ----
echo [INFO] Starting Sudoko-Arena server on port %PORT%...
start "Sudoko-Arena Server" cmd /c "%PYTHON_CMD% backend/server.py"

rem ---- Wait for server to respond ----
echo [INFO] Waiting for server to launch...
powershell -NoProfile -Command "$ok=$false; for ($i=0; $i -lt 15; $i++) { try { $r = Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Milliseconds 500 }; if (-not $ok) { exit 1 }"
if errorlevel 1 (
    echo [ERROR] Server failed to respond within 7.5 seconds.
    echo Please make sure no other process is using port %PORT%.
    echo.
    pause
    exit /b 1
)

rem ---- Open default browser ----
echo [INFO] Opening %URL% in your browser...
start "" "%URL%"

echo.
echo ====================================================
echo   Sudoko-Arena is now running at %URL%
echo ====================================================
echo Keep this window or the "Sudoko-Arena Server" window
echo open to keep the application running.
echo.
pause
exit /b 0
