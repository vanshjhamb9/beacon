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

echo Starting Celery Beat (separate process — required on Windows)...
start "beacon-celery-beat" /MIN cmd /c "cd /d %CD%\apps\worker && set PYTHONPATH=%PYTHONPATH% && set POSTGRES_HOST=127.0.0.1 && set REDIS_HOST=127.0.0.1 && python -m celery -A worker.celery_app.celery_app beat --loglevel=INFO"

timeout /t 2 >nul
echo Starting Celery Worker...
cd /d "%CD%\apps\worker"
python -m celery -A worker.celery_app.celery_app worker --loglevel=INFO --pool=solo -Q celery
endlocal
