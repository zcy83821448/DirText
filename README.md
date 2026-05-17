# DirText v3.9

[![Release](https://img.shields.io/github/v/release/zcy83821448/DirText)](https://github.com/zcy83821448/DirText/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)](https://github.com/zcy83821448/DirText)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **English** | [中文说明](#中文说明)

A lightweight Windows GUI tool that scans folder structures and exports them as **TXT tree text**, **CSV table**, **XLSX spreadsheet**, or **JSON structured data**.

Built with PyQt6. Auto-detects system language (English / Chinese). No installation required.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📁 **Multi-folder Selection** | Add multiple folders via the built-in directory tree dialog (Ctrl+click multi-select) |
| 🖱️ **Drag & Drop** | Drag any folder directly into the window — auto-scans on drop |
| 📋 **Clipboard Auto-detect** | Automatically recognizes valid folder paths copied to clipboard on startup |
| 🔍 **Recursion Depth Control** | Free text input for recursion depth. `0` = current level only, `-1` = all levels. 1-second debounce auto-scan |
| 💾 **Export Format Selection** | Choose between **TXT** (tree text), **CSV** (table), **XLSX** (spreadsheet), **JSON** (structured data) before saving |
| 📊 **Metadata Export** | Optional metadata for CSV/JSON/XLSX: file size, creation date, modification date, last access date |
| 🌐 **Export Language Toggle** | Switch export content language (EN / 中文) independently from the UI language |
| 📈 **Export Progress Bar** | Real-time progress bar for exports with status updates |
| 🌐 **Auto Bilingual UI** | Interface automatically switches between English and Chinese based on system locale |
| ⚡ **Real-time Preview** | Live preview of directory tree while scanning |
| 🔎 **Search** | Search for files directly in the preview window |
| 🌙 **Dark Mode** | One-click toggle between dark and light themes |
| 📋 **Right-click to Copy Path** | Right-click any file or folder in the preview to copy its full path to clipboard |
| 🚫 **Custom Ignore Patterns** | Ignore specific file extensions; users can customize their own ignore list |
| 🔽 **Filter** | Filter files by specific date or size ranges |
| 🚀 **Multi-threaded Scanning** | Parallel directory scanning with ThreadPoolExecutor for faster performance |
| 🎯 **Performance Optimized** | Preview line limit, reduced animation frame rate, and overall performance improvements |

---

## 📥 Download

1. Go to [Releases](https://github.com/zcy83821448/DirText/releases)
2. Download `DirText.exe`
3. Double-click to run — **no installation required**

> ⚠️ Windows may show a SmartScreen warning because the `.exe` is not code-signed. Click **"More info" → "Run anyway"** to proceed.

---

## 🚀 Quick Start

1. **Launch** `DirText.exe`
2. **Add folders** by one of these methods:
   - Click **"Add Folder"** and select in the dialog
   - **Drag & drop** a folder into the window
   - Copy a folder path to clipboard before launch — it will auto-detect
3. **Set recursion depth** in the text field (default `0` = current level)
4. **Preview** the generated tree in real-time
5. Use the **Search** box above the preview to find specific files
6. Use **Filter** to narrow down results by date or size
7. Click **"Export"** → choose **TXT / CSV / XLSX / JSON** → save with auto-generated timestamp
8. *(CSV/JSON/XLSX only)* Click **"Metadata"** to optionally include file size, creation, modification and access dates
9. *(Optional)* Use the top-left **EN / 中文** toggle to change the export file language without affecting the UI
10. *(Optional)* Click the **theme toggle** to switch between light and dark mode
11. *(Optional)* Click **"Ignore"** to set custom file extensions to exclude from scanning

> 💡 **Tip:** If date columns show as `####` when opening CSV/XLSX in Excel, simply widen the column width.

---

## 🖼️ Screenshots

<img width="1405" height="694" alt="image" src="https://github.com/user-attachments/assets/4cd8be56-b72f-4115-a7a2-b578c5ed2d53" />


---

## 🛠️ Build from Source

```bash
# 1. Clone the repository
git clone https://github.com/zcy83821448/DirText.git
cd DirText

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python dirtext.py
```

### Build executable (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=app.ico dirtext.py
```

---

## 📝 Changelog

### v3.9
- **Search** — Added a search box above the preview window to quickly find files
- **Right-click to Copy Path** — Moved copy-path action from left-click to right-click context menu in the preview
- **XLSX Export** — New export format: Excel spreadsheet (.xlsx)
- **Filter** — Filter files by specific date or size ranges

### v3.8
- **Multi-threaded Scanning** — Parallel directory scanning with ThreadPoolExecutor for significantly faster performance on large directories
- **Preview Line Limit** — Preview window now limits to 5000 lines for smooth performance; full content available on export
- **Smoother Theme Transitions** — Reduced animation frame rate for theme switching to improve performance
- **Performance Optimizations** — Overall performance improvements and code refactoring

### v3.7
- **Dark Mode** — One-click toggle between dark and light themes
- **Click to Copy Path** — Click any file or folder in the preview tree to copy its full path to clipboard
- **Custom Ignore Patterns** — Support for ignoring specific file extensions with a user-customizable ignore list

### v3.5
- **Export Format Selection** — Choose TXT, CSV, or JSON before saving
- **Drag & Drop Support** — Drop folders anywhere in the window to auto-scan
- **Free Recursion Input** — Replaced dropdown with text input + 1s debounce auto-scan
- **Metadata Export** — Optional file size, creation, modification and access dates for CSV/JSON exports
- **Export Language Toggle** — Switch export content language (EN / 中文) independently from UI language
- **Export Progress Bar** — Real-time progress indicator for CSV/JSON exports
- **CSV Excel Compatibility Tip** — Post-export reminder for Excel date column width
- **Updated Welcome Page** — Added usage instructions for new features

### v3.0
- Multi-folder selection dialog
- Clipboard path auto-detection
- Recursive depth control (dropdown)
- Auto English/Chinese UI switching
- One-click export to `.txt`

---

## 🏷️ Keywords / Tags

`directory-tree` `folder-structure` `file-listing` `export-to-text` `tree-generator` `folder-export` `directory-listing` `csv-export` `xlsx-export` `json-export` `metadata-export` `file-metadata` `pyqt6` `python` `gui` `desktop-application` `windows` `productivity` `utility` `developer-tools` `documentation` `file-manager` `drag-and-drop` `dark-mode` `ignore-patterns` `multi-threaded` `search` `filter`

---

## 📄 License

[MIT](LICENSE)

---

---

<a name="中文说明"></a>

# DirText v3.9 中文说明

轻量级 Windows GUI 工具，扫描文件夹结构并导出为 **TXT 树形文本**、**CSV 表格**、**XLSX 电子表格** 或 **JSON 结构化数据**。

基于 PyQt6 构建，自动识别系统语言（英文/中文），无需安装，即开即用。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📁 **多文件夹选择** | 内置目录树对话框，支持 Ctrl+单击 多选 |
| 🖱️ **拖拽支持** | 直接将文件夹拖入窗口任意区域，松开后自动添加并扫描 |
| 📋 **剪贴板自动识别** | 启动时自动检测剪贴板中的有效文件夹路径 |
| 🔍 **递归深度自由输入** | 文本框输入递归层数，`0` = 仅当前层，`-1` = 全部层级，输入停止后 1 秒自动触发扫描 |
| 💾 **导出格式选择** | 导出前可选择 **TXT**（树形文本）、**CSV**（表格）、**XLSX**（电子表格）、**JSON**（结构化数据） |
| 📊 **元数据导出** | CSV/JSON/XLSX 可选导出文件大小、创建日期、修改日期、访问日期 |
| 🌐 **导出语言切换** | 左上角切换导出文件语言（EN / 中文），不影响程序界面语言 |
| 📈 **导出进度条** | 导出时底部显示精确进度条与状态提示 |
| 🌐 **自动双语界面** | 根据系统区域设置自动切换英文/中文界面 |
| ⚡ **实时预览** | 扫描过程中实时预览目录树结构 |
| 🔎 **搜索** | 预览窗口上方搜索框，可直接搜索对应文件 |
| 🌙 **深色模式** | 一键切换深色/浅色主题 |
| 📋 **右键复制路径** | 预览窗口中右键点击任意文件或文件夹，即可复制其完整路径到剪贴板 |
| 🚫 **自定义忽略规则** | 支持按文件后缀名忽略特定文件，用户可自定义忽略列表 |
| 🔽 **筛选** | 可按特定日期或大小范围筛选文件 |
| 🚀 **多线程扫描** | 使用 ThreadPoolExecutor 并行扫描目录，大幅提升大目录扫描速度 |
| 🎯 **性能优化** | 预览行数限制、降低主题切换帧率、整体性能提升与代码重构 |

---

## 📥 下载

1. 进入 [Releases](https://github.com/zcy83821448/DirText/releases)
2. 下载 `DirText.exe`
3. 双击运行 — **无需安装**

> ⚠️ Windows 可能会显示 SmartScreen 安全警告（因为未进行代码签名）。点击 **"更多信息" → "仍要运行"** 即可。

---

## 🚀 快速上手

1. **运行** `DirText.exe`
2. **添加文件夹**，任选一种方式：
   - 点击 **"添加文件夹"** 在对话框中选择
   - **拖拽** 文件夹到窗口内
   - 启动前复制文件夹路径到剪贴板 — 程序会自动识别
3. 在递归深度输入框中设置层数（默认 `0` = 仅当前层）
4. **实时预览** 生成的目录树
5. 使用预览区上方的 **搜索框** 快速查找文件
6. 使用 **筛选** 功能按日期或大小范围过滤结果
7. 点击 **"导出文本"** → 选择 **TXT / CSV / XLSX / JSON** → 自动带时间戳保存
8. *（CSV/JSON/XLSX 专属）* 点击 **"元数据"** 按钮，可选择附带文件大小、创建/修改/访问日期
9. *（可选）* 点击左上角 **EN / 中文** 切换导出文件语言，不影响程序界面
10. *（可选）* 点击 **主题切换按钮** 在深色/浅色模式间切换
11. *（可选）* 点击 **"忽略"** 按钮，设置需要排除扫描的特定文件后缀名

> 💡 **提示：** 若 CSV / XLSX 用 Excel 打开后日期列显示 `####`，拖宽列宽即可正常显示。

---

## 🖼️ 界面截图

> *(在 GitHub 编辑器中拖拽截图图片到此处即可自动上传)*

---

## 🛠️ 从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/zcy83821448/DirText.git
cd DirText

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python dirtext.py
```

### 打包为可执行文件（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=app.ico dirtext.py
```

---

## 📝 更新日志

### v3.9
- **搜索** — 预览窗口上方新增搜索框，可直接搜索对应文件
- **右键复制路径** — 左键点击复制路径功能废除，迁移至右键菜单
- **XLSX 导出** — 新增 Excel 电子表格 (.xlsx) 导出格式
- **筛选** — 可按特定日期或大小范围筛选文件

### v3.8
- **多线程扫描** — 使用 ThreadPoolExecutor 并行扫描目录，大幅提升大目录扫描速度
- **预览行数限制** — 预览窗口限制为 5000 行以保证流畅性能，导出可查看完整内容
- **主题切换优化** — 降低主题切换动画帧率，提升性能表现
- **性能优化** — 整体性能提升与代码重构

### v3.7
- **深色模式** — 支持一键切换深色/浅色主题
- **点击复制路径** — 预览树中点击任意文件或文件夹即可复制完整路径到剪贴板
- **自定义忽略规则** — 支持按文件后缀名过滤，用户可自定义忽略列表

### v3.5
- **导出格式选择** — 支持 TXT、CSV、JSON 三种格式
- **拖拽文件夹支持** — 拖入窗口任意区域即可自动添加扫描，重复文件夹自动跳过
- **递归深度自由输入** — 替换下拉框为文本输入，带 1 秒防抖自动扫描
- **元数据导出** — CSV/JSON 支持可选导出文件大小、创建/修改/访问日期
- **导出语言切换** — 可独立切换导出文件语言（EN / 中文），不影响界面语言
- **导出进度条** — CSV/JSON 导出时显示实时进度条与状态栏提示
- **CSV Excel 兼容提示** — 导出完成后提示 Excel 日期列宽问题
- **欢迎页面更新** — 新增使用说明

### v3.0
- 多文件夹选择对话框
- 剪贴板路径自动识别
- 递归深度控制（下拉框）
- 中英文界面自动切换
- 一键导出 `.txt`

---

## 🏷️ 关键词 / 标签

`目录树` `文件夹结构` `文件列表` `导出文本` `树形生成器` `文件夹导出` `CSV导出` `XLSX导出` `JSON导出` `元数据导出` `文件元数据` `PyQt6` `Python` `GUI工具` `桌面应用` `Windows工具` `效率工具` `开发工具` `文档工具` `文件管理` `拖拽支持` `深色模式` `忽略规则` `多线程` `搜索` `筛选`

---

## 📄 开源协议

[MIT](LICENSE)

---

> Written with [Claude Code](https://claude.ai/code)
