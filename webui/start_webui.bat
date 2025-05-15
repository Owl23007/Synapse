@echo off
title Synapse WebUI

:: 设置工作目录为脚本所在目录
cd /d "%~dp0"

:: 检查依赖项
python --version > nul 2>&1
if errorlevel 1 (
    echo 未找到 Python，请安装 Python 3.8+
    pause
    exit /b 1
)

:: Start the web application
echo Starting Synapse WebUI...
python app.py

pause