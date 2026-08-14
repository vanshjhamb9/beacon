@echo off
setlocal
REM Start Redis 7+/8+ with Streams from the no-space runtime copy.
set REDIS_HOME=C:\temp\redis74
if not exist "%REDIS_HOME%\redis-server.exe" (
  echo Redis runtime missing at %REDIS_HOME%.
  echo Install redis-windows-fork 8.x and extract/copy runtime to C:\temp\redis74 including DLLs.
  exit /b 1
)

netstat -ano | findstr ":6379" >nul
if not errorlevel 1 (
  echo Redis already listening on :6379
  set REDIS_LINE=
  for /f "delims=" %%l in ('"%REDIS_HOME%\redis-cli.exe" INFO server ^| findstr redis_version') do set REDIS_LINE=%%l
  set REDIS_VERSION=%REDIS_LINE:redis_version:=%
  set REDIS_VERSION=%REDIS_VERSION: =%
  if not "%REDIS_VERSION%"=="" (
    echo redis_version:%REDIS_VERSION%
  )
  if "%REDIS_VERSION%"=="3.0.504" (
    echo Legacy Redis detected on :6379. Restarting with Redis 8 runtime...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":6379"') do (
      taskkill /PID %%p /F >nul 2>&1
    )
    timeout /t 1 >nul
  ) else (
    exit /b 0
  )
)

echo Starting Redis 8 runtime on :6379 ...
REM msys Redis needs cwd = REDIS_HOME so DLLs resolve
start "beacon-redis7" /MIN /D "%REDIS_HOME%" redis-server.exe redis.conf
timeout /t 2 >nul
"%REDIS_HOME%\redis-cli.exe" ping
"%REDIS_HOME%\redis-cli.exe" INFO server | findstr redis_version
endlocal
