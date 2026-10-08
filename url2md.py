#!/usr/bin/env python3
"""
url2md - 单页文档抓取 CLI 工具
功能：输入网址，输出 Markdown（支持 文档中心 / 帮助中心 / GitHub / 通用网页）

用法：
  python url2md.py <URL>                        # 直接输出到控制台
  python url2md.py <URL> -o output.md           # 保存到文件
  python url2md.py <URL> --no-browser           # 禁用浏览器渲染，强制走纯 Requests 模式
  python url2md.py <URL> --use-browser          # 强制启用浏览器渲染（应对 SPA/动态页面）
  python url2md.py <URL> --timeout 20           # 设置超时时间（秒）
"""

import os
import sys
import time
import argparse
from urllib.parse import urlparse, unquote

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

try:
    from html_to_md import html_to_md
except ImportError as e:
    sys.stderr.write(f"[错误] 导入 html_to_md 失败: {e}\n")
    sys.stderr.write(f"       脚本目录: {_SCRIPT_DIR}\n")
    sys.exit(1)

import requests

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _get_browser():
    """尝试获取无头浏览器，失败返回 None。"""
    try:
        from selenium import webdriver
    except ImportError:
        return None

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument(f"user-agent={UA}")

    try:
        return webdriver.Chrome(options=options)
    except Exception:
        try:
            os.environ['WDM_SSL_VERIFY'] = '0'
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception:
            try:
                options.binary_location = "/usr/bin/chromium-browser"
                return webdriver.Chrome(options=options)
            except Exception:
                return None


def _requests_fetch(url: str, timeout: int, token: str = "") -> str | None:
    """纯 Requests 模式抓取。"""
    try:
        headers = {"User-Agent": UA}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        is_raw_md = (
            "raw.githubusercontent.com" in url
            or url.endswith(".md")
            or url.endswith(".txt")
            or ("text/plain" in content_type and "text/html" not in content_type)
        )

        if is_raw_md:
            return resp.text

        looks_like_html = "text/html" in content_type or "<html" in resp.text[:500].lower()
        if looks_like_html:
            md = html_to_md(resp.text)
            if md and len(md.strip()) > 10:
                return md
            sys.stderr.write("[提示] 返回的 HTML 中未检测到主内容节点，目标页面可能是前端渲染 (SPA)。\n"
                             "       请尝试加 --use-browser 使用浏览器渲染模式。\n")
            return None
        return resp.text
    except Exception as e:
        sys.stderr.write(f"[Requests 模式失败] {e}\n")
        return None


def _browser_fetch(url: str, timeout: int, token: str = "") -> str | None:
    """Selenium 浏览器渲染模式。"""
    browser = _get_browser()
    if browser is None:
        return None
    try:
        if token:
            browser.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {"Authorization": f"Bearer {token}"}})
        browser.get("about:blank")
        time.sleep(0.3)
        browser.get(url)

        md_content = None
        for _ in range(timeout):
            time.sleep(1)
            temp_md = html_to_md(browser.page_source)
            if temp_md and len(temp_md.strip()) > 10:
                md_content = temp_md
                break
        return md_content
    except Exception as e:
        sys.stderr.write(f"[浏览器模式失败] {e}\n")
        return None
    finally:
        try:
            browser.quit()
        except Exception:
            pass


def fetch_url(url: str, timeout: int = 15, force_mode: str = "auto", token: str = "") -> str | None:
    """
    抓取 URL 并返回 Markdown。
    force_mode: "auto" | "browser" | "requests"
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        sys.stderr.write(f"[错误] 无效的 URL: {url}\n")
        return None

    # 纯文本 / GitHub Raw 直接走 Requests 加速
    is_fast_path = (
        "raw.githubusercontent.com" in url
        or url.endswith(".md")
        or url.endswith(".txt")
    )
    if is_fast_path or force_mode == "requests":
        return _requests_fetch(url, timeout, token)

    if force_mode == "browser":
        md = _browser_fetch(url, timeout, token)
        if not md:
            sys.stderr.write("[降级] 浏览器模式未取到内容，尝试 Requests 直连...\n")
            md = _requests_fetch(url, timeout, token)
        return md

    # auto 模式：优先浏览器，失败降级
    md = _browser_fetch(url, timeout, token)
    if md:
        return md
    sys.stderr.write("[降级] 浏览器不可用或渲染超时，切换 Requests 直连...\n")
    return _requests_fetch(url, timeout, token)


def _url_to_default_filename(url: str) -> str:
    """从 URL 推导一个合理的默认文件名。"""
    parsed = urlparse(url)
    path = unquote(parsed.path).strip("/")
    if "raw.githubusercontent.com" in parsed.netloc:
        parts = path.split("/")
        if len(parts) >= 4:
            return f"{'_'.join(parts[-2:]) or 'github_raw'}.md"
    netloc = parsed.netloc.replace(".", "_")
    name = (path.replace("/", "_") or netloc)[:120]
    safe = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.')).strip("._-")
    return (safe or "document") + ".md"


def main():
    parser = argparse.ArgumentParser(
        description="url2md - 将文档中心/帮助中心等单页网页抓取为 Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s https://docs.unitree.com/go2/sdk/intro
  %(prog)s https://support.unitree.com/hc/zh-cn/articles/... -o article.md
  %(prog)s https://github.com/unitreerobotics/unitree_mujoco --no-browser
        """,
    )
    parser.add_argument("url", help="要抓取的目标 URL")
    parser.add_argument(
        "-o", "--output",
        help="输出 Markdown 文件路径（缺省则打印到 stdout；若为目录则自动命名存入）",
        default=None,
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="禁用浏览器渲染，仅使用纯 HTTP Requests 模式（轻量快速，但不支持 JS 动态页面）",
    )
    parser.add_argument(
        "--use-browser", action="store_true",
        help="强制使用 Selenium 无头浏览器渲染（适合 SPA / 动态加载内容）",
    )
    parser.add_argument(
        "--timeout", type=int, default=15,
        help="超时时间（秒），默认 15",
    )
    parser.add_argument(
        "--token", default="",
        help="可选：附加 Authorization: Bearer <TOKEN> 请求头（私有仓库等场景）",
    )
    parser.add_argument(
        "--prepend-url", action="store_true",
        help="在 Markdown 顶部添加原始来源链接",
    )

    args = parser.parse_args()

    if args.no_browser and args.use_browser:
        sys.stderr.write("[错误] --no-browser 与 --use-browser 不能同时使用。\n")
        sys.exit(2)

    mode = "requests" if args.no_browser else ("browser" if args.use_browser else "auto")

    sys.stderr.write(f"[抓取] {args.url}  (模式: {mode}, 超时: {args.timeout}s)\n")
    md = fetch_url(args.url, timeout=args.timeout, force_mode=mode, token=args.token)

    if not md or not md.strip():
        sys.stderr.write("[失败] 未能获取到有效内容。\n")
        sys.exit(1)

    content = md.strip()
    if args.prepend_url:
        content = f"<!-- 来源: {args.url} -->\n\n{content}"

    output = args.output
    if output:
        output = os.path.expanduser(output)
        is_dir_intent = output.endswith(os.sep) or os.path.isdir(output)
        if is_dir_intent:
            os.makedirs(output, exist_ok=True)
            output = os.path.join(output, _url_to_default_filename(args.url))
        else:
            parent = os.path.dirname(os.path.abspath(output))
            if parent:
                os.makedirs(parent, exist_ok=True)
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            sys.stderr.write(f"[完成] 已保存至: {os.path.abspath(output)} ({len(content)} 字符)\n")
        except OSError as e:
            sys.stderr.write(f"[写入失败] {e}\n")
            sys.exit(1)
    else:
        sys.stdout.write(content + "\n")


if __name__ == "__main__":
    main()
