@echo off
setlocal
chcp 65001 >nul
title Painel de Pendencias SRAG - mantenha esta janela aberta
cd /d "%~dp0"
set "PYC="
if exist "..\.venv\Scripts\python.exe" set "PYC=..\.venv\Scripts\python.exe"
if not defined PYC (where py >nul 2>nul && set "PYC=py -3")
if not defined PYC (where python >nul 2>nul && set "PYC=python")
if not defined PYC (
  echo ERRO: Python 3 nao foi encontrado. Use o .venv do projeto ou instale o Python 3.
  pause
  exit /b 1
)
echo Iniciando o painel (se houver uma versao antiga aberta, ela sera encerrada e substituida)...
echo Esta janela deve ficar aberta enquanto voce usa o painel.
echo Para encerrar: botao "Encerrar" no painel, ou feche esta janela.
echo.
%PYC% "%~dp0server.py" start
if errorlevel 1 (
  echo.
  echo O painel foi encerrado com erro. Detalhes em .srag-status-local\logs\painel.log
  pause
)
endlocal
