@echo off
title Synapse WebUI

:: Change to script directory
cd /d "%~dp0"

:: 检查依赖项

:: Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Start the web application
echo Starting Synapse WebUI...
python app.py

pause