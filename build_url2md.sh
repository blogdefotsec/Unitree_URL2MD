#!/usr/bin/env bash
# build_url2md.sh — 将 url2md.py + html_to_md.py 打包为单文件可执行程序
#
# 用法:
#   ./build_url2md.sh              # 默认: 精简版 (仅 Requests, 约 30~60MB, 不支持 SPA)
#   ./build_url2md.sh full         # 完整版 (含 Selenium, 约 200~400MB, 支持 SPA 渲染, 仍需目标机有 Chrome/Chromium)
#   ./build_url2md.sh clean        # 清理构建产物
#
# 产物位置: dist/url2md (Linux ELF)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "[安装] 首次构建，正在安装 PyInstaller ..."
    pip3 install --quiet pyinstaller
fi

mode="${1:-lite}"

if [ "$mode" = "clean" ]; then
    rm -rf build dist url2md.spec __pycache__
    echo "[清理] 已删除 build/ dist/ url2md.spec __pycache__/"
    exit 0
fi

COMMON_ARGS=(
    --noconfirm
    --onefile
    --clean
    --name url2md
    --paths "$PROJECT_DIR"
    --hidden-import html_to_md
    --hidden-import markdownify
    --hidden-import bs4
    --hidden-import soupsieve
    --hidden-import requests
    --hidden-import urllib3
    --hidden-import charset_normalizer
    --hidden-import certifi
    --hidden-import idna
    # markdownify 0.x 依赖
    --hidden-import markdown_it
    --hidden-import mdurl
    --hidden-import mdurl._url
    --collect-submodules markdown_it
    --collect-submodules soupsieve
)

EXCLUDE_ARGS=()

case "$mode" in
    lite|light|minimal)
        echo "[构建] 精简版模式 —— 仅 Requests, 无 Selenium/浏览器渲染"
        EXCLUDE_ARGS=(
            --exclude-module selenium
            --exclude-module trio
            --exclude-module wsproto
            --exclude-module sniffio
            --exclude-module outcome
            --exclude-module webdriver_manager
            --exclude-module sortedcontainers
            --exclude-module attrs
            --exclude-module cffi
            --exclude-module pycparser
            --exclude-module PySocks
            --exclude-module websocket_client
        )
        ;;
    full|complete|with-browser)
        echo "[构建] 完整版模式 —— 含 Selenium (目标机器仍需 Chrome/Chromium 可用)"
        COMMON_ARGS+=(
            # Selenium 全量子模块（动态 import 的子模块必须显式收集，否则 PyInstaller 漏打）
            --collect-submodules selenium
            --collect-submodules selenium.webdriver
            --collect-submodules selenium.webdriver.chrome
            --collect-submodules selenium.webdriver.common
            --collect-submodules selenium.webdriver.remote
            --collect-submodules selenium.webdriver.support
            --collect-submodules selenium.common
            --hidden-import selenium.webdriver.chrome.options
            --hidden-import selenium.webdriver.chrome.service
            --hidden-import selenium.webdriver.chrome.webdriver
            --hidden-import selenium.webdriver.common.options
            --hidden-import selenium.webdriver.common.service
            --hidden-import selenium.webdriver.common.by
            --hidden-import selenium.webdriver.common.keys
            --hidden-import selenium.webdriver.common.desired_capabilities
            --hidden-import selenium.webdriver.common.timeouts
            --hidden-import selenium.webdriver.remote.command
            --hidden-import selenium.webdriver.remote.webdriver
            --hidden-import selenium.webdriver.remote.webelement
            --hidden-import selenium.webdriver.remote.remote_connection
            --hidden-import selenium.webdriver.support.wait
            --hidden-import selenium.webdriver.support.expected_conditions
            # webdriver_manager
            --collect-submodules webdriver_manager
            --hidden-import webdriver_manager.chrome
            --hidden-import webdriver_manager.core.os_manager
            --hidden-import webdriver_manager.core.logger
            --hidden-import webdriver_manager.core.download_manager
            # trio / websocket / Selenium 4.x 隐式依赖
            --collect-submodules trio
            --collect-submodules wsproto
            --hidden-import sniffio
            --hidden-import outcome
            --hidden-import sortedcontainers
            --hidden-import attrs
            --hidden-import cffi
            --hidden-import pycparser
            --hidden-import websocket_client
            --hidden-import PySocks
        )
        ;;
    *)
        echo "[错误] 未知模式: $mode" >&2
        echo "用法: $0 [lite|full|clean]" >&2
        exit 2
        ;;
esac

rm -rf build dist url2md.spec __pycache__

pyinstaller "${COMMON_ARGS[@]}" "${EXCLUDE_ARGS[@]}" "$PROJECT_DIR/url2md.py"

echo
echo "========================================================"
echo "  构建完成！产物位置: $PROJECT_DIR/dist/url2md"
echo "  大小: $(du -h "$PROJECT_DIR/dist/url2md" | cut -f1)"
echo "========================================================"
echo
echo "  使用示例（精简版只支持服务端渲染页面，例如 GitHub）："
echo "    ./dist/url2md https://github.com/unitreerobotics/unitree_mujoco --no-browser"
echo
echo "  完整版渲染 SPA（如帮助中心）："
echo "    ./dist/url2md https://support.unitree.com/home/zh/G1_developer/about_G1 --use-browser -o out.md"
echo
