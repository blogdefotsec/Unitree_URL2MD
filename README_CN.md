# url2md

单页文档抓取 CLI 工具，输入网址，输出 Markdown。

专为 **宇树文档中心 / 帮助中心 / GitHub / 通用网页** 优化，自动识别页面主内容区域，过滤导航栏、侧边栏、页脚等冗余元素。

[English Version](README.md)

## 功能特性

- **双模式抓取**：纯 Requests 模式（轻量快速）+ Selenium 无头浏览器模式（支持 SPA / 动态加载）
- **智能主内容识别**：针对宇树文档中心、帮助中心、GitHub README 做了专属容器匹配
- **自动降级**：浏览器模式失败时自动回退到 Requests 模式
- **快速路径**：GitHub Raw / `.md` / `.txt` 文件直接透传，无需解析 HTML
- **灵活输出**：控制台打印 / 指定文件保存 / 目录自动命名存入
- **可选鉴权**：支持 `Authorization: Bearer` 请求头，用于私有仓库访问
- **单文件打包**：支持 PyInstaller 打包为独立可执行文件

## 环境要求

- Python 3.10+
- 浏览器模式需要系统已安装 **Chrome** 或 **Chromium**（打包后的完整版同样需要）

## 安装

```bash
# 克隆或进入项目目录后，安装核心依赖
pip install -r requirements.txt
```

如需启用浏览器渲染模式（处理 SPA / 动态页面），额外安装：

```bash
pip install selenium webdriver-manager
```

或直接取消 `requirements.txt` 中可选依赖的注释后再安装。

## 使用方法

### 基本用法

```bash
# 抓取 URL，输出到控制台
python url2md.py <URL>

# 保存到指定文件
python url2md.py <URL> -o output.md

# 存入目录，自动根据 URL 生成文件名
python url2md.py <URL> -o ./docs/
```

### 模式切换

```bash
# 禁用浏览器，仅使用 Requests 模式（推荐用于 GitHub、静态文档站）
python url2md.py <URL> --no-browser

# 强制启用浏览器渲染（SPA / 前端动态渲染页面）
python url2md.py <URL> --use-browser
```

### 其他参数

```bash
# 设置超时时间（默认 15 秒）
python url2md.py <URL> --timeout 20

# 附加 Bearer Token（私有仓库等场景）
python url2md.py <URL> --token ghp_xxxxxxxxxxxx

# 在 Markdown 顶部添加来源链接注释
python url2md.py <URL> --prepend-url
```

### 使用示例

```bash
# 宇树文档中心
python url2md.py https://docs.unitree.com/go2/sdk/intro -o go2_sdk.md

# 宇树帮助中心（需要浏览器模式）
python url2md.py https://support.unitree.com/home/zh/G1_developer/about_G1 \
  --use-browser -o g1_about.md

# GitHub 仓库 README（推荐走 Requests 模式）
python url2md.py https://github.com/unitreerobotics/unitree_mujoco --no-browser

# GitHub Raw 直链
python url2md.py https://raw.githubusercontent.com/unitreerobotics/unitree_mujoco/main/README.md
```

## 工作原理

### 抓取流程（auto 模式）

```
输入 URL
   │
   ├─► 是 Raw / .md / .txt ? ──► Requests 直连（快速路径）
   │
   └─► 尝试 Selenium 无头浏览器渲染
         │
         ├─ 成功 → 返回 Markdown
         └─ 失败 / 不可用 → 降级 Requests 直连
                              │
                              ├─ 返回 HTML → 解析主内容 → 转 Markdown
                              └─ 返回纯文本 → 直接返回
```

### 主内容容器匹配优先级

| 优先级 | 选择器 | 适用场景 |
|--------|--------|----------|
| 1 | `<article id="unitree-preview">` | 宇树文档中心 |
| 2 | `<div id="docCont">` | 宇树文档中心（旧版） |
| 3 | `<div class="article_wrapper">` | 宇树帮助中心 |
| 4 | `<article class="markdown-body entry-content container-lg">` | GitHub README |

未匹配到主容器时，Requests 模式会提示建议使用 `--use-browser`。

## 打包为单文件可执行程序

使用项目自带的 `build_url2md.sh` 脚本，基于 PyInstaller 打包：

```bash
# 精简版：仅 Requests，体积 ~30-60MB，不支持 SPA
./build_url2md.sh

# 完整版：含 Selenium，体积 ~200-400MB，支持 SPA（目标机仍需 Chrome/Chromium）
./build_url2md.sh full

# 清理构建产物
./build_url2md.sh clean
```

产物位置：`dist/url2md`（Linux ELF 单文件）

```bash
# 打包后使用示例
./dist/url2md https://github.com/unitreerobotics/unitree_mujoco --no-browser
./dist/url2md https://support.unitree.com/home/zh/G1_developer/about_G1 --use-browser -o out.md
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `url2md.py` | CLI 主入口，参数解析、抓取调度、输出管理 |
| `html_to_md.py` | HTML 主内容提取 + Markdown 转换核心模块 |
| `build_url2md.sh` | PyInstaller 打包脚本（精简版 / 完整版） |
| `requirements.txt` | Python 依赖清单 |
| `url2md` | 预构建的可执行文件（ELF） |

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 抓取失败 / 无有效内容 / 写入失败 |
| 2 | 参数错误（如同时使用 `--no-browser` 与 `--use-browser`） |

## 常见问题

**Q: 抓取的内容为空或只有少量文字？**
A: 目标页面大概率是前端渲染（SPA），加 `--use-browser` 重试。需确保已安装 `selenium` 和系统 Chrome/Chromium。

**Q: 浏览器模式报错找不到 ChromeDriver？**
A: 确认安装了 `webdriver-manager`，或手动确保 `chromedriver` 在 `PATH` 中。Linux 可尝试安装 `chromium-driver` 包。

**Q: GitHub 私有仓库怎么抓？**
A: 生成 Personal Access Token，使用 `--token <TOKEN>` 参数。Raw 直链和 HTML 页面都支持。

**Q: 想抓取整站而不是单页？**
A: 本工具定位是**单页抓取**，整站爬取需自行编写循环或使用 sitemap 驱动。
