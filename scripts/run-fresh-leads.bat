@echo off
setlocal
cd /d "%~dp0.."

set POSTGRES_HOST=127.0.0.1
set REDIS_HOST=127.0.0.1
set POSTGRES_DB=beacon
set POSTGRES_USER=beacon
set POSTGRES_PASSWORD=beacon_password
set PYTHONPATH=%CD%\apps\api;%CD%\apps\worker;%CD%\packages;%CD%

echo [%date% %time%] Fresh Leads Run Starting...
python "%~dp0fresh_leads_scheduler.py"
echo [%date% %time%] Fresh Leads Run Complete
endlocal
