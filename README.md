# url2md

Single-page document scraping CLI tool. Feed it a URL, get Markdown back.

Optimized for **Unitree Doc Center / Help Center / GitHub / general web pages**. Automatically identifies the main content region and strips out navigation, sidebars, footers, and other noise.

[中文文档](README_CN.md)

## Features

- **Dual-mode scraping**: Plain Requests mode (lightweight & fast) + Selenium headless browser mode (supports SPAs / dynamically loaded content)
- **Smart main-content detection**: Dedicated container matchers for Unitree Doc Center, Help Center, and GitHub README
- **Automatic fallback**: Gracefully degrades to Requests mode when browser rendering fails
- **Fast path**: GitHub Raw / `.md` / `.txt` files are passed through directly without HTML parsing
- **Flexible output**: Print to stdout / save to a specific file / auto-named storage inside a directory
- **Optional auth**: Supports `Authorization: Bearer` header for private repository access
- **Single-file binary**: Packaged as a standalone executable via PyInstaller

## Requirements

- Python 3.10+
- Browser mode requires **Chrome** or **Chromium** installed on the system (also required by the full packaged binary)

## Installation

```bash
# Enter the project directory, install core dependencies
pip install -r requirements.txt
```

To enable browser rendering (for SPAs / dynamic pages), additionally install:

```bash
pip install selenium webdriver-manager
```

Or simply uncomment the optional dependencies in `requirements.txt` before installing.

## Usage

### Basics

```bash
# Scrape URL, print to stdout
python url2md.py <URL>

# Save to a specific file
python url2md.py <URL> -o output.md

# Save into a directory; filename is auto-derived from the URL
python url2md.py <URL> -o ./docs/
```

### Mode switching

```bash
# Disable browser, use Requests only (recommended for GitHub and static doc sites)
python url2md.py <URL> --no-browser

# Force Selenium headless browser rendering (for SPAs / client-rendered pages)
python url2md.py <URL> --use-browser
```

### Additional options

```bash
# Set timeout in seconds (default: 15)
python url2md.py <URL> --timeout 20

# Attach a Bearer Token (for private repositories, etc.)
python url2md.py <URL> --token ghp_xxxxxxxxxxxx

# Prepend a source URL comment at the top of the Markdown
python url2md.py <URL> --prepend-url
```

### Examples

```bash
# Unitree Doc Center
python url2md.py https://docs.unitree.com/go2/sdk/intro -o go2_sdk.md

# Unitree Help Center (requires browser mode)
python url2md.py https://support.unitree.com/home/zh/G1_developer/about_G1 \
  --use-browser -o g1_about.md

# GitHub repository README (use Requests mode)
python url2md.py https://github.com/unitreerobotics/unitree_mujoco --no-browser

# GitHub Raw direct link
python url2md.py https://raw.githubusercontent.com/unitreerobotics/unitree_mujoco/main/README.md
```

## How it works

### Scraping flow (auto mode)

```
Input URL
   │
   ├─► Raw / .md / .txt ? ──► Direct Requests (fast path)
   │
   └─► Try Selenium headless browser render
         │
         ├─ Success → return Markdown
         └─ Failure / unavailable → fall back to Requests
                                          │
                                          ├─ HTML returned → parse main content → convert to Markdown
                                          └─ Plain text returned → return as-is
```

### Main content container matching priority

| Priority | Selector | Target |
|----------|----------|--------|
| 1 | `<article id="unitree-preview">` | Unitree Doc Center |
| 2 | `<div id="docCont">` | Unitree Doc Center (legacy) |
| 3 | `<div class="article_wrapper">` | Unitree Help Center |
| 4 | `<article class="markdown-body entry-content container-lg">` | GitHub README |

When no main container is matched, Requests mode prints a hint suggesting `--use-browser`.

## Packaging as a single-file executable

Use the bundled `build_url2md.sh` script to build a PyInstaller binary:

```bash
# Lite: Requests only, ~30-60MB, no SPA support
./build_url2md.sh

# Full: includes Selenium, ~200-400MB, SPA support (target still needs Chrome/Chromium)
./build_url2md.sh full

# Clean build artifacts
./build_url2md.sh clean
```

Output location: `dist/url2md` (Linux ELF single file)

```bash
# Usage examples after packaging
./dist/url2md https://github.com/unitreerobotics/unitree_mujoco --no-browser
./dist/url2md https://support.unitree.com/home/zh/G1_developer/about_G1 --use-browser -o out.md
```

## File overview

| File | Purpose |
|------|---------|
| `url2md.py` | CLI entry point — argument parsing, scrape orchestration, output management |
| `html_to_md.py` | HTML main-content extraction + Markdown conversion core module |
| `build_url2md.sh` | PyInstaller packaging script (lite / full modes) |
| `requirements.txt` | Python dependency manifest |
| `url2md` | Pre-built executable (ELF) |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Scraping failed / no valid content / write failed |
| 2 | Argument error (e.g. both `--no-browser` and `--use-browser` specified) |

## FAQ

**Q: Output is empty or contains only a few lines?**
A: The page is very likely a client-rendered SPA. Retry with `--use-browser`. Ensure `selenium` is installed and Chrome/Chromium is present on the system.

**Q: Browser mode errors with ChromeDriver not found?**
A: Verify `webdriver-manager` is installed, or ensure `chromedriver` is on your `PATH` manually. On Linux try installing the `chromium-driver` package.

**Q: How to scrape a private GitHub repo?**
A: Generate a Personal Access Token and pass it via `--token <TOKEN>`. Works for both Raw links and HTML pages.

**Q: Can it scrape an entire site instead of one page?**
A: This tool is intentionally scoped as a **single-page scraper**. For whole-site crawling, drive it with a custom loop or a sitemap.
