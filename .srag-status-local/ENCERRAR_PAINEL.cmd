@echo off
cd /d "%~dp0"
set "PYC="
if exist "..\.venv\Scripts\python.exe" set "PYC=..\.venv\Scripts\python.exe"
if not defined PYC (where py >nul 2>nul && set "PYC=py -3")
if not defined PYC (where python >nul 2>nul && set "PYC=python")
if not defined PYC exit /b 1
%PYC% "%~dp0server.py" stop
timeout /t 3 >nul
