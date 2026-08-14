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

echo Starting Beacon API on http://localhost:8000 ...
cd /d "%CD%\apps\api"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
endlocal
