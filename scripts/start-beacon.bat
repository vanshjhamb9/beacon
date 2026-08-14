@echo off
setlocal
cd /d "%~dp0.."

set POSTGRES_HOST=127.0.0.1
set REDIS_HOST=127.0.0.1
set POSTGRES_DB=beacon
set POSTGRES_USER=beacon
set POSTGRES_PASSWORD=beacon_password
set PYTHONPATH=%CD%\apps\api;%CD%\apps\worker;%CD%\packages;%CD%

call "%~dp0start-redis.bat"
if errorlevel 1 exit /b 1

echo Applying Alembic migrations to head...
cd /d "%CD%\apps\api"
python -m alembic -c alembic.ini upgrade head
if errorlevel 1 (
  echo Migration failed — refusing to start.
  exit /b 1
)

echo Starting API...
start "beacon-api" cmd /c "cd /d %CD% && set PYTHONPATH=%PYTHONPATH% && set POSTGRES_HOST=127.0.0.1 && set REDIS_HOST=127.0.0.1 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 >nul
echo Starting worker+beat in this window...
cd /d "%~dp0"
call start-worker.bat
endlocal
