@echo off
cd client
start python dashboard.py
if %ERRORLEVEL% NEQ 0 pause
cd ..