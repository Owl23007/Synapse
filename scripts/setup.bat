@echo off
setlocal enabledelayedexpansion

chcp 65001 > nul

echo ===================================
echo         Synapse 环境安装向导
echo ===================================

echo [1/4] 检查 Python 环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo [X] Python未安装！
    echo [!] 请从 https://python.org 下载并安装 Python 3.8+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [√] 检测到%%i

echo [2/4] 配置虚拟环境...
if not exist "venv" (
    echo [*] 正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [X] 创建失败！
        echo [!] 请检查 Python 权限设置
        pause
        exit /b 1
    )
    echo [√] 创建完成
) else (
    echo [√] 虚拟环境已就绪
)

echo [3/4] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [X] 激活失败！
    echo [!] 请尝试以管理员身份运行
    pause
    exit /b 1
)
echo [√] 环境已激活

echo [4/4] 安装依赖包...
if exist "requirements.txt" (
    echo [*] 正在安装依赖（预计需要 3-5 分钟）...
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo [X] 安装失败！
        echo [!] 请检查网络连接或更换 pip 源
        pause
        exit /b 1
    )
    echo [√] 安装完成
) else (
    echo [!] 未找到 requirements.txt
    echo [i] 跳过依赖安装
)

echo.
echo ===================================
echo         环境配置成功完成
echo ===================================
pause