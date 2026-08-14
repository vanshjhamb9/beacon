@echo off
set PYTHONPATH=C:\Inowix intelligence system\New folder;C:\Inowix intelligence system\New folder\apps\api;C:\Inowix intelligence system\New folder\packages
cd /d "C:\Inowix intelligence system\New folder\apps\api"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
