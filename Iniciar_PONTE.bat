@echo off
setlocal EnableExtensions
title PONTE - Iniciar aplicativo
cd /d "%~dp0"
if errorlevel 1 goto ERRO_PASTA

echo ===========================================
echo       PONTE - TRADUTOR DE LIBRAS
echo ===========================================
echo.

if not exist "interface.py" goto ERRO_ARQUIVOS
if not exist "requirements.txt" goto ERRO_ARQUIVOS

set "PYTHON_VENV=%CD%\.venv\Scripts\python.exe"
if exist "%PYTHON_VENV%" goto CHECAR_DEPENDENCIAS

echo [1/3] Criando ambiente virtual...
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv ".venv"
) else (
    where python >nul 2>&1
    if errorlevel 1 goto ERRO_PYTHON
    python -m venv ".venv"
)
if errorlevel 1 goto ERRO_VENV
if not exist "%PYTHON_VENV%" goto ERRO_VENV

:CHECAR_DEPENDENCIAS
echo [2/3] Conferindo bibliotecas...
"%PYTHON_VENV%" -c "import cv2; from PySide6 import QtWidgets; import dotenv; import google.generativeai; import pyttsx3" >nul 2>&1
if not errorlevel 1 goto INICIAR

echo Instalando as dependencias do PONTE...
echo Na primeira instalacao, e necessario acesso a internet.
"%PYTHON_VENV%" -m pip install -r "requirements.txt"
if errorlevel 1 goto ERRO_DEPENDENCIAS

"%PYTHON_VENV%" -c "import cv2; from PySide6 import QtWidgets; import dotenv; import google.generativeai; import pyttsx3" >nul 2>&1
if errorlevel 1 goto ERRO_DEPENDENCIAS

:INICIAR
echo [3/3] Abrindo o aplicativo...
echo Feche o aplicativo PONTE para finalizar este terminal.
"%PYTHON_VENV%" "interface.py"
if errorlevel 1 goto ERRO_APLICATIVO
exit /b 0

:ERRO_PASTA
echo ERRO: Nao foi possivel acessar a pasta do projeto.
goto FALHA

:ERRO_ARQUIVOS
echo ERRO: Arquivos interface.py ou requirements.txt nao encontrados.
echo Mantenha este .bat na pasta principal do repositorio PONTE.
goto FALHA

:ERRO_PYTHON
echo ERRO: Python nao foi encontrado neste computador.
echo Instale Python 3.10 ou superior e marque a opcao Add Python to PATH.
goto FALHA

:ERRO_VENV
echo ERRO: Nao foi possivel criar o ambiente virtual .venv.
goto FALHA

:ERRO_DEPENDENCIAS
echo ERRO: Nao foi possivel instalar ou carregar as dependencias.
echo Confira sua conexao com a internet e a versao do Python.
goto FALHA

:ERRO_APLICATIVO
echo ERRO: A interface do PONTE foi encerrada com falha.
goto FALHA

:FALHA
echo.
pause
exit /b 1
