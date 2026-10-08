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
