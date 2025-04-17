@echo off
setlocal enabledelayedexpansion

chcp 65001 > nul

:: 检查运行标记文件
set FLAG_FILE=venv\.deps_installed
if exist %FLAG_FILE% (
    echo 依赖已安装，跳过检查...
) else (
    :: 检查 Python 环境
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python未安装，请先安装Python 3.8+
        exit /b 1
    )

    :: 检查虚拟环境
    if not exist "venv" (
        echo 创建虚拟环境...
        python -m venv venv
    )

    :: 激活虚拟环境并安装依赖
    call venv\Scripts\activate
    echo 首次运行，安装依赖...
    pip install -r requirements.txt
    pip install -e .

    :: 创建标记文件
    echo Dependencies installed at: %date% %time% > %FLAG_FILE%
)

:: 激活虚拟环境
call venv\Scripts\activate

:: 设置 PYTHONPATH
set PYTHONPATH=%CD%

:: 启动应用
echo 启动 Synapse AI Agent...
python -m src.app

:: 如果程序异常退出，等待用户确认
if errorlevel 1 (
    echo 程序异常退出，请查看日志了解详细信息
    pause
)

endlocal

