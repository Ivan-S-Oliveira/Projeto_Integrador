@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYC="
if exist "..\.venv\Scripts\python.exe" set "PYC=..\.venv\Scripts\python.exe"
if not defined PYC (where py >nul 2>nul && set "PYC=py -3")
if not defined PYC (where python >nul 2>nul && set "PYC=python")
if not defined PYC (echo Python 3 nao encontrado. & pause & exit /b 1)
echo === Diagnostico do Painel de Pendencias ===
%PYC% "%~dp0server.py" diagnostico
echo.
echo === Validacao do PROJECT_STATUS_TEXT.md ===
%PYC% "%~dp0server.py" validar
echo.
echo === Ultimas linhas do log ===
if exist "logs\painel.log" powershell -NoProfile -Command "Get-Content -Tail 30 -Encoding UTF8 'logs\painel.log'"
echo.
pause
