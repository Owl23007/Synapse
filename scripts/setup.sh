#!/bin/bash

echo "=================================== "
echo "         Synapse 环境安装向导      "
echo "=================================== "

echo "[1/4] 检查 Python 环境..."
python --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[X] Python未安装！"
    echo "[!] 请从 https://python.org 下载并安装 Python 3.8+"
    exit 1
fi
echo "[√] 检测到 Python 版本: $(python --version)"

echo "[2/4] 配置虚拟环境..."
if [ ! -d "venv" ]; then
    echo "[*] 正在创建虚拟环境..."
    python -m venv venv
    if [ $? -ne 0 ]; then
        echo "[X] 创建失败！"
        echo "[!] 请检查 Python 权限设置"
        exit 1
    fi
    echo "[√] 创建完成"
else
    echo "[√] 虚拟环境已就绪"
fi

echo "[3/4] 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[X] 激活失败！"
    echo "[!] 请尝试以管理员身份运行"
    exit 1
fi
echo "[√] 环境已激活"

echo "[4/4] 安装依赖包..."
if [ -f "requirements.txt" ]; then
    echo "[*] 正在安装依赖（预计需要 3-5 分钟）..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[X] 安装失败！"
        echo "[!] 请检查网络连接或更换 pip 源"
        exit 1
    fi
    echo "[√] 安装完成"
else
    echo "[!] 未找到 requirements.txt"
    echo "[i] 跳过依赖安装"
fi

echo
echo "=================================== "
echo "         环境配置成功完成          "
echo "=================================== "
pause