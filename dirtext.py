"""
DirText - Directory to Text (PyQt6)
A lightweight directory listing tool with PyQt6 GUI.
轻量级文件夹目录提取工具 - PyQt6 版本
Automatically switches UI language based on system locale.
根据系统区域自动切换界面语言。
"""

import ctypes
import csv
import fnmatch
import json
import locale
import os
import platform
import re
import subprocess
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QFrame, QMainWindow, QWidget, QLabel, QPushButton,
    QPlainTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QDialog, QTreeView, QAbstractItemView,
    QComboBox, QProgressBar, QHeaderView, QGraphicsOpacityEffect,
    QLineEdit, QCheckBox, QListWidget
)
from PyQt6.QtCore import Qt, QTimer, QSortFilterProxyModel, QDir, QPropertyAnimation, QVariantAnimation, QEasingCurve, QPoint, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFileSystemModel, QFont, QPalette
from animations import TransitionManager, AnimatedButton
from exporters import ExportFormatDialog, MetadataDialog, Exporter

# ---------- 预览行数限制 / Preview Line Limit ----------
PREVIEW_LINE_LIMIT = 5000

# ---------- 语言检测 / Language Detection ----------
def get_system_language():
    try:
        locale.setlocale(locale.LC_CTYPE, '')
    except:
        pass
    try:
        lang = locale.getlocale(locale.LC_CTYPE)[0]
        if lang:
            # Windows: 'Chinese_China', 'Chinese_Taiwan' → zh
            # POSIX:   'zh_CN', 'zh_TW'                 → zh
            if lang.startswith('zh') or lang.lower().startswith('chinese'):
                return 'zh'
    except:
        pass
    try:
        if os.environ.get('LANG', '').startswith('zh'):
            return 'zh'
    except:
        pass
    return 'en'

LANG = get_system_language()

# ---------- 国际化文本 / Internationalized Text ----------
T = {
    'en': {
        'title': 'DirText v3.6',
        'header': 'Directory to Text',
        'subtitle': 'Quickly browse folder contents and export list',
        'add': 'Add Folder',
        'clear': 'Clear',
        'export': 'Export',
        'ready': 'Ready',
        'welcome': "Welcome to Directory to Text\n\nInstructions:\n  1. Click 'Add Folder' or drag folders onto the window\n  2. Set depth in 'Recursion [N] Levels' (-1 = all, 0 = current)\n  3. Preview area shows the content\n  4. Click 'Export' to save\n  5. Right-click any file/dir name in preview for options\n     (Copy Path / Open File / Show in Explorer)\n\nClick a button to get started",
        'dup_folder': 'This folder is already in the list!',
        'no_content': 'No content to export!',
        'save_title': 'Save file list',
        'file_name': 'file_list_{ts}.txt',
        'success': 'File saved to:\n{path}',
        'fail': 'Save failed: {error}',
        'clipboard_load': 'Load from Clipboard',
        'clipboard_found': 'Detected path in clipboard:\n\n{path}\n\nLoad this folder?',
        'clipboard_invalid': 'No valid file path detected in clipboard.',
        'clipboard_error': 'Failed to read clipboard: {error}',
        'add_hint': 'Ctrl+click to select multiple / Ctrl+A to select all',
        'drive_switch': 'Drive:',
        'current_path': 'Current:',
        'recursion_prefix': 'Recursion ',
        'recursion_suffix': ' Levels',
        'recursion_hint': '(-1 = all, 0 = current)',
        'recursion_welcome': 'Usage: Type a number in "Recursion [N] Levels" to set depth.\n  -1 = all levels   0 = current level only   1+ = N levels deep',
        'cancel': 'Cancel',
        'scanning': 'Scanning: {path}',
        'cancelling': 'Cancelling...',
        'export_format': 'Export Format',
        'format_prompt': 'Select export format:',
        'format_txt': 'Text File (.txt)',
        'format_csv': 'CSV File (.csv)',
        'format_json': 'JSON File (.json)',
        'csv_save_title': 'Save CSV file list',
        'csv_file_name': 'file_list_{ts}.csv',
        'json_save_title': 'Save JSON file list',
        'json_file_name': 'file_list_{ts}.json',
        'csv_col_folder': 'Folder',
        'csv_col_name': 'Name',
        'csv_col_path': 'Full Path',
        'csv_col_type': 'Type',
        'csv_col_level': 'Level',
        'csv_type_dir': 'Directory',
        'csv_type_file': 'File',
        'metadata': 'Metadata',
        'metadata_title': 'Export Metadata Options',
        'metadata_prompt': 'Select metadata to include in export:',
        'metadata_size': 'File Size',
        'metadata_created': 'Creation Date',
        'metadata_modified': 'Modification Date',
        'metadata_accessed': 'Access Date',
        'csv_col_size': 'Size',
        'csv_col_created': 'Created',
        'csv_col_modified': 'Modified',
        'csv_col_accessed': 'Accessed',
        'csv_excel_hint': 'Tip: If date columns show "#####" in Excel, drag the column wider — the data is correct, the default width is just too narrow.',
        'metadata_txt_hint': 'Note: TXT format does not support metadata export (CSV/JSON only).',
        'exporting': 'Exporting...',
        'export_progress': 'Exporting %v / %m',
        'export_lang_label': 'Lang: ',
        'path_copied': 'File path copied to clipboard: {path}',
        'ignore': 'Ignore',
        'ignore_title': 'Ignore List',
        'ignore_prompt': 'Files / folders matching these patterns will be skipped during scan:',
        'ignore_hint': 'Supports wildcards (*.log, *.tmp). One pattern per line.',
        'ignore_add': 'Add',
        'ignore_remove': 'Remove',
        'search_placeholder': 'Search files...',
        'filter_result': 'Search: "{text}" → {count} items',
        'no_filter_match': 'No matches found',
        'copy_path': 'Copy Path',
        'open_file': 'Open File',
        'show_in_explorer': 'Show in Explorer',
        'filter': 'Filter',
        'ignore_filter': 'Ignore/Filter',
        'filter_title': 'Filter Criteria',
        'filter_time_start': 'Start:',
        'filter_time_end': 'End:',
        'filter_time_hint': 'YYYY-MM-DD HH:MM  (leave empty = no limit)',
        'filter_size_label': 'File Size:',
        'filter_size_min': 'Min (KB)',
        'filter_size_max': 'Max (KB)',
        'filter_size_hint': 'Leave empty = no limit  (1 MB = 1024 KB)',
        'filter_clear': 'Clear',
        'xlsx_save_title': 'Save Excel file list',
        'xlsx_file_name': 'file_list_{ts}.xlsx',
        'xlsx_no_module': 'This feature requires the openpyxl library.\n\nInstall it with:\npip install openpyxl',
        'format_xlsx': 'Excel File (.xlsx)',
        'no_format_selected': 'Please select at least one format.',
        'filter_active': '● Filters active',
    },
    'zh': {
        'title': 'DirText v3.6',
        'header': '文件目录提取器',
        'subtitle': '快速浏览文件夹内容并导出列表',
        'add': '添加文件夹',
        'clear': '清空选择',
        'export': '导出文本',
        'ready': '就绪',
        'welcome': '欢迎使用文件目录提取器\n\n使用说明：\n  1. 点击「添加文件夹」或拖入文件夹到窗口\n  2. 在"递归【N】层"中设置深度（-1 = 全部，0 = 当前层）\n  3. 预览区显示内容\n  4. 点击「导出文本」保存\n  5. 在预览中右键任意文件/文件夹名称即可：\n     复制路径 / 打开文件 / 在资源管理器中显示\n\n点击按钮开始使用吧',
        'dup_folder': '该文件夹已在列表中！',
        'no_content': '没有可导出的内容！',
        'save_title': '保存文件列表',
        'file_name': '文件列表_{ts}.txt',
        'success': '文件已保存到：\n{path}',
        'fail': '保存失败：{error}',
        'clipboard_load': '剪切板加载',
        'clipboard_found': '识别到剪切板中的路径：\n\n{path}\n\n是否加载该文件夹？',
        'clipboard_invalid': '剪切板中未检测到有效的文件路径。',
        'clipboard_error': '读取剪切板失败：{error}',
        'add_hint': 'Ctrl+单击 多选 / Ctrl+A 全选',
        'drive_switch': '驱动器:',
        'current_path': '当前位置:',
        'recursion_prefix': '递归 ',
        'recursion_suffix': ' 层',
        'recursion_hint': '（-1 = 全部层级，0 = 仅当前层）',
        'recursion_welcome': '用法：在"递归【N】层"中输入数字设置深度。\n  -1 = 全部层级   0 = 仅当前层   1+ = 向下N层',
        'cancel': '取消',
        'scanning': '正在扫描：{path}',
        'cancelling': '正在取消...',
        'export_format': '导出格式',
        'format_prompt': '请选择导出格式：',
        'format_txt': '文本文件 (.txt)',
        'format_csv': 'CSV 文件 (.csv)',
        'format_json': 'JSON 文件 (.json)',
        'csv_save_title': '保存 CSV 文件列表',
        'csv_file_name': '文件列表_{ts}.csv',
        'json_save_title': '保存 JSON 文件列表',
        'json_file_name': '文件列表_{ts}.json',
        'csv_col_folder': '所属文件夹',
        'csv_col_name': '名称',
        'csv_col_path': '完整路径',
        'csv_col_type': '类型',
        'csv_col_level': '层级',
        'csv_type_dir': '文件夹',
        'csv_type_file': '文件',
        'metadata': '元数据',
        'metadata_title': '导出元数据选项',
        'metadata_prompt': '选择导出时需要附带的元数据：',
        'metadata_size': '文件大小',
        'metadata_created': '创建日期',
        'metadata_modified': '修改日期',
        'metadata_accessed': '访问日期',
        'csv_col_size': '大小',
        'csv_col_created': '创建时间',
        'csv_col_modified': '修改时间',
        'csv_col_accessed': '访问时间',
        'csv_excel_hint': '提示：如果 Excel 中日期列显示为"#####"，请拖宽列宽即可正常显示（数据本身无误，只是默认列宽不够）。',
        'metadata_txt_hint': '注意：TXT 格式不支持元数据导出（仅 CSV / JSON 支持）。',
        'exporting': '正在导出...',
        'export_progress': '正在导出 %v / %m',
        'export_lang_label': '导出语言：',
        'path_copied': '已将该文件路径复制到剪贴板：{path}',
        'ignore': '忽略',
        'ignore_title': '忽略列表',
        'ignore_prompt': '扫描时将自动跳过匹配以下模式的文件 / 文件夹：',
        'ignore_hint': '支持通配符（*.log、*.tmp）。每行一个模式。',
        'ignore_add': '添加',
        'ignore_remove': '移除',
        'search_placeholder': '搜索文件...',
        'filter_result': '搜索："{text}" → {count} 项',
        'no_filter_match': '未找到匹配项',
        'copy_path': '复制路径',
        'open_file': '打开文件',
        'show_in_explorer': '在资源管理器中显示',
        'filter': '筛选',
        'ignore_filter': '忽略/筛选',
        'filter_title': '筛选条件',
        'filter_time_start': '起始：',
        'filter_time_end': '截止：',
        'filter_time_hint': '年-月-日 时:分  （留空=不限制）',
        'filter_size_label': '文件大小：',
        'filter_size_min': '最小 (KB)',
        'filter_size_max': '最大 (KB)',
        'filter_size_hint': '留空=不限制  （1 MB = 1024 KB）',
        'filter_clear': '清除',
        'xlsx_save_title': '保存 Excel 文件列表',
        'xlsx_file_name': '文件列表_{ts}.xlsx',
        'xlsx_no_module': '此功能需要 openpyxl 库。\n\n请使用以下命令安装：\npip install openpyxl',
        'format_xlsx': 'Excel 文件 (.xlsx)',
        'no_format_selected': '请至少选择一种导出格式。',
        'filter_active': '● 筛选已激活',
    }
}

def t(key, lang=None, **kw):
    s = T.get(lang or LANG, T['en']).get(key, key)
    return s.format(**kw) if kw else s


def format_size(bytes_val):
    if bytes_val is None or bytes_val == 0:
        return '0 B'
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(bytes_val)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    if i == 0:
        return f'{int(size)} B'
    return f'{size:.1f} {units[i]}'


def format_timestamp(ts):
    if not ts:
        return ''
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


# ---------- 主题颜色 / Theme Colors ----------
THEMES = {
    'light': {
        'bg': '#F5F5F7', 'fg': '#1D1D1F', 'fg2': '#86868B', 'surface': '#FFFFFF',
        'border': '#d1d1d6', 'hover_bg': '#e8e8ed', 'pressed_bg': '#d1d1d6',
        'accent': '#007aff', 'scroll_handle': '#c6c6ca', 'scroll_handle_hover': '#a8a8ae',
        'progress_bg': '#e0e0e5', 'option_circle': '#c6c6ca', 'accent_green': '#34c759',
    },
    'dark': {
        'bg': '#1C1C1E', 'fg': '#F5F5F7', 'fg2': '#98989D', 'surface': '#2C2C2E',
        'border': '#48484A', 'hover_bg': '#3A3A3C', 'pressed_bg': '#48484A',
        'accent': '#0A84FF', 'scroll_handle': '#636366', 'scroll_handle_hover': '#7C7C80',
        'progress_bg': '#3A3A3C', 'option_circle': '#636366', 'accent_green': '#30D158',
    },
}
C = dict(THEMES['light'])  # current theme, mutated on toggle


def _make_btn_style(c):
    return f"""
    QPushButton {{
        font-family: 'Microsoft YaHei'; font-weight: bold; font-size: 10pt;
        padding: 6px 20px; background: {c['surface']};
        color: {c['fg']}; border: 1px solid {c['border']}; border-radius: 4px;
    }}
    QPushButton:hover {{ background: {c['hover_bg']}; }}
    QPushButton:pressed {{ background: {c['pressed_bg']}; }}
"""


# ---------- 支持多选的文件夹对话框 / Multi-select Folder Dialog ----------
class DirFilterProxyModel(QSortFilterProxyModel):
    """只显示目录，隐藏文件 / Only show directories in tree"""
    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        if model is None:
            return False
        index = model.index(source_row, 0, source_parent)
        return model.isDir(index)


class FolderSelectDialog(QDialog):
    """自定义文件夹选择对话框，支持 Ctrl/Shift 多选，带驱动器切换"""
    def __init__(self, parent=None, cfg=None):
        super().__init__(parent)
        self.cfg = cfg or {}
        self.selected_folders = []
        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        self.proxy = DirFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(t('add'))

        w = self.cfg.get('fd_w', 500)
        h = self.cfg.get('fd_h', 600)
        self.resize(w, h)

        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self._setup_drive_bar(layout)
        self._setup_path_label(layout)
        self._setup_tree_view(layout)
        self._setup_hint(layout)
        self._setup_dialog_buttons(layout)

        self._navigate_to(QDir.rootPath())
        self.tree.doubleClicked.connect(self._accept)

    def _setup_drive_bar(self, layout):
        if platform.system() != 'Windows':
            return
        drive_bar = QHBoxLayout()
        lbl = QLabel(t('drive_switch'))
        lbl.setStyleSheet(f"color: {C['fg']}; font-size: 9pt; background: transparent;")
        drive_bar.addWidget(lbl)
        self.drive_cb = QComboBox()
        self.drive_cb.setStyleSheet(f"QComboBox {{ font-size: 10pt; padding: 2px 4px; background: {C['surface']}; color: {C['fg']}; border: 1px solid {C['border']}; }}")
        for drive in QDir.drives():
            self.drive_cb.addItem(os.path.normpath(drive.path()))
        self.drive_cb.currentIndexChanged.connect(self._switch_drive)
        drive_bar.addWidget(self.drive_cb, 1)
        layout.addLayout(drive_bar)

    def _setup_path_label(self, layout):
        self.path_label = QLabel()
        self.path_label.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

    def _setup_tree_view(self, layout):
        self.tree = QTreeView()
        self.tree.setModel(self.proxy)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        for col in range(1, self.model.columnCount()):
            self.tree.setColumnHidden(col, True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setStyleSheet(f"""
            QTreeView {{
                background: {C['surface']}; color: {C['fg']};
                border: 1px solid {C['border']}; border-radius: 4px;
                font-size: 10pt;
            }}
            QTreeView::item:selected {{
                background: {C['accent']}; color: white;
            }}
        """)
        layout.addWidget(self.tree, stretch=1)

    def _setup_hint(self, layout):
        hint = QLabel(t('add_hint'))
        hint.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        layout.addWidget(hint)

    def _setup_dialog_buttons(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        for text, slot in [
            ('OK', self._accept),
            ('Cancel', self.reject),
        ]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(_make_btn_style(C))
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _navigate_to(self, path):
        """导航到指定目录"""
        path = os.path.normpath(path)
        self.tree.collapseAll()
        root_idx = self.model.setRootPath(path)
        self.tree.setRootIndex(self.proxy.mapFromSource(root_idx))
        self.tree.expand(self.tree.rootIndex())
        self.path_label.setText(f"{t('current_path')} {path}")

    def _switch_drive(self, index):
        """驱动器切换"""
        drive = self.drive_cb.itemText(index)
        if drive and os.path.isdir(drive):
            self._navigate_to(drive)

    def closeEvent(self, event):
        self.cfg['fd_w'] = self.width()
        self.cfg['fd_h'] = self.height()
        super().closeEvent(event)

    def _accept(self):
        indexes = self.tree.selectionModel().selectedRows(0)
        paths = []
        for idx in indexes:
            src_idx = self.proxy.mapToSource(idx)
            paths.append(self.model.filePath(src_idx))
        self.selected_folders = list(dict.fromkeys(paths))
        if not self.selected_folders:
            self.selected_folders = [self.model.rootPath()]
        self.accept()


# ---------- 扫描工作线程 / Scan Worker Thread ----------
class ScanWorker(QThread):
    folder_progress = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, int, int)

    def __init__(self, folders, recursion_depth, ignore_patterns=None):
        super().__init__()
        self.folders = folders
        self.recursion_depth = recursion_depth
        self.ignore_patterns = ignore_patterns or []
        self._abort_event = threading.Event()
        self.structured_data = []

    def abort(self):
        self._abort_event.set()

    def run(self):
        lines = []
        line_paths = []
        total_dirs = 0
        total_files = 0
        sep = '═' * 80
        item_count = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            for i, folder in enumerate(self.folders):
                if self._abort_event.is_set():
                    lines.append(f"⚠ {t('cancelling')}")
                    line_paths.append(None)
                    break
                self.folder_progress.emit(folder)
                lines.append(sep)
                line_paths.append(None)
                if LANG == 'en':
                    lines.append(f"Folder [{i + 1}]: {folder}")
                else:
                    lines.append(f"文件夹 [{i + 1}]：{folder}")
                line_paths.append(None)
                lines.append(sep)
                line_paths.append(None)

                entry_lines, entry_paths, d, f, added = self._process_folder(
                    folder, executor)
                lines.extend(entry_lines)
                line_paths.extend(entry_paths)
                total_dirs += d
                total_files += f
                item_count += added
                self.progress.emit(item_count)

                lines.append("")
                line_paths.append(None)

        lines.append(sep)
        line_paths.append(None)
        if LANG == 'en':
            lines.append(f"Total: {len(self.folders)} folder(s)")
            lines.append(f"         {total_dirs} folders, {total_files} files")
        else:
            lines.append(f"总计：{len(self.folders)} 个文件夹")
            lines.append(f"         共 {total_dirs} 个文件夹，{total_files} 个文件")
        line_paths.append(None)
        line_paths.append(None)

        self._line_paths = line_paths
        self.finished.emit(lines, total_dirs, total_files)

    def _process_folder(self, folder, executor):
        """Process a single top-level folder, parallelizing subdirectory scans."""
        lines = []
        line_paths = []
        dir_count = 0
        file_count = 0
        item_count = 0

        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name)
            if self.ignore_patterns:
                entries = [e for e in entries
                           if not any(fnmatch.fnmatch(e.name, p)
                                      for p in self.ignore_patterns)]
        except PermissionError:
            msg = '<Access denied>' if LANG == 'en' else '<无法访问>'
            lines.append(f"└── {msg}")
            line_paths.append(None)
            return lines, line_paths, 0, 0, 1
        except Exception as e:
            lines.append(f"└── <Error: {e}>")
            line_paths.append(None)
            return lines, line_paths, 0, 0, 1

        entry_infos = []
        future_to_idx = {}

        for idx, entry in enumerate(entries):
            is_last = (idx == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            info = {
                'name': entry.name,
                'path': entry.path,
                'is_dir': entry.is_dir(),
                'connector': connector,
                'child_prefix': child_prefix,
            }

            if entry.is_dir():
                st = self._safe_stat(entry)
                info['stat'] = st
                if self.recursion_depth == -1 or 0 < self.recursion_depth:
                    future = executor.submit(
                        self._scan_tree,
                        entry.path, self.recursion_depth, 1,
                        child_prefix, folder,
                        self.ignore_patterns, self._abort_event,
                    )
                    future_to_idx[future] = idx
            else:
                st = self._safe_stat(entry)
                info['stat'] = st

            entry_infos.append(info)

        sub_results = {}
        for future in as_completed(future_to_idx):
            if self._abort_event.is_set():
                break
            idx = future_to_idx[future]
            try:
                sub_results[idx] = future.result()
            except Exception:
                sub_results[idx] = ([], [], [], 0, 0)

        for idx, info in enumerate(entry_infos):
            if self._abort_event.is_set():
                break

            if info['is_dir']:
                lines.append(f"{info['connector']}{info['name']}/")
                line_paths.append(info['path'])
                dir_count += 1
                item_count += 1
                st = info['stat']
                self.structured_data.append({
                    'folder': folder, 'name': info['name'], 'path': info['path'],
                    'type': 'dir', 'level': 0,
                    'size': st['size'], 'created': st['created'],
                    'modified': st['modified'], 'accessed': st['accessed'],
                })
                if idx in sub_results:
                    sub_lines, sub_paths, sub_data, sub_dirs, sub_files = sub_results[idx]
                    lines.extend(sub_lines)
                    line_paths.extend(sub_paths)
                    self.structured_data.extend(sub_data)
                    dir_count += sub_dirs
                    file_count += sub_files
                    item_count += sub_dirs + sub_files
            else:
                lines.append(f"{info['connector']}{info['name']}")
                line_paths.append(info['path'])
                file_count += 1
                item_count += 1
                st = info['stat']
                self.structured_data.append({
                    'folder': folder, 'name': info['name'], 'path': info['path'],
                    'type': 'file', 'level': 0,
                    'size': st['size'], 'created': st['created'],
                    'modified': st['modified'], 'accessed': st['accessed'],
                })

        return lines, line_paths, dir_count, file_count, item_count

    @staticmethod
    def _scan_tree(folder, max_depth, current_depth, prefix, root,
                   ignore_patterns, abort_event):
        """Recursively scan a directory tree. Runs in any thread."""
        if abort_event.is_set():
            return [], [], [], 0, 0

        lines = []
        line_paths = []
        structured_data = []
        dir_count = 0
        file_count = 0

        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name)
            if ignore_patterns:
                entries = [e for e in entries
                           if not any(fnmatch.fnmatch(e.name, p)
                                      for p in ignore_patterns)]
        except PermissionError:
            msg = '<Access denied>' if LANG == 'en' else '<无法访问>'
            lines.append(f"{prefix}└── {msg}")
            line_paths.append(None)
            return lines, line_paths, [], 0, 0
        except Exception as e:
            lines.append(f"{prefix}└── <Error: {e}>")
            line_paths.append(None)
            return lines, line_paths, [], 0, 0

        for i, entry in enumerate(entries):
            if abort_event.is_set():
                break

            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                line_paths.append(entry.path)
                dir_count += 1
                st = ScanWorker._safe_stat(entry)
                structured_data.append({
                    'folder': root, 'name': entry.name, 'path': entry.path,
                    'type': 'dir', 'level': current_depth,
                    'size': st['size'], 'created': st['created'],
                    'modified': st['modified'], 'accessed': st['accessed'],
                })
                if max_depth == -1 or current_depth < max_depth:
                    sub_lines, sub_paths, sub_data, sub_dirs, sub_files = ScanWorker._scan_tree(
                        entry.path, max_depth, current_depth + 1,
                        prefix + child_prefix, root,
                        ignore_patterns, abort_event,
                    )
                    lines.extend(sub_lines)
                    line_paths.extend(sub_paths)
                    structured_data.extend(sub_data)
                    dir_count += sub_dirs
                    file_count += sub_files
            else:
                lines.append(f"{prefix}{connector}{entry.name}")
                line_paths.append(entry.path)
                file_count += 1
                st = ScanWorker._safe_stat(entry)
                structured_data.append({
                    'folder': root, 'name': entry.name, 'path': entry.path,
                    'type': 'file', 'level': current_depth,
                    'size': st['size'], 'created': st['created'],
                    'modified': st['modified'], 'accessed': st['accessed'],
                })

        return lines, line_paths, structured_data, dir_count, file_count

    @staticmethod
    def _safe_stat(entry):
        try:
            st = entry.stat()
            return {
                'size': st.st_size,
                'created': st.st_ctime,
                'modified': st.st_mtime,
                'accessed': st.st_atime,
            }
        except OSError:
            return {'size': 0, 'created': 0, 'modified': 0, 'accessed': 0}


# ---------- 导出格式选择对话框 / Export Format Dialog ----------

# ---------- 忽略列表对话框 / Ignore List Dialog ----------
class IgnoreListDialog(QDialog):
    def __init__(self, parent=None, patterns=None, filter_criteria=None):
        super().__init__(parent)
        self.patterns = list(patterns) if patterns else []
        self.filter_criteria = dict(filter_criteria) if filter_criteria else {
            'time_start': '', 'time_end': '',
            'size_min': '', 'size_max': '',
        }
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(t('ignore_title'))
        self.setMinimumSize(340, 320)
        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(8)

        prompt = QLabel(t('ignore_prompt'))
        prompt.setStyleSheet(f"color: {C['fg']}; font-size: 10pt; background: transparent;")
        prompt.setWordWrap(True)
        layout.addWidget(prompt)

        hint = QLabel(t('ignore_hint'))
        hint.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # pattern list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: {C['surface']}; color: {C['fg']};
                border: 1px solid {C['border']}; border-radius: 4px;
                font-size: 10pt;
            }}
            QListWidget::item:selected {{
                background: {C['accent']}; color: white;
            }}
        """)
        for p in self.patterns:
            self.list_widget.addItem(p)
        layout.addWidget(self.list_widget, stretch=1)

        # input row
        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText('node_modules')
        self.input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 10pt; padding: 4px 6px;
                background: {C['surface']}; color: {C['fg']};
                border: 1px solid {C['border']}; border-radius: 4px;
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """)
        self.input.returnPressed.connect(self._add)
        input_row.addWidget(self.input)

        btn_add = AnimatedButton(t('ignore_add'))
        btn_add.setStyleSheet(_make_btn_style(C))
        btn_add.clicked.connect(self._add)
        input_row.addWidget(btn_add)

        btn_remove = AnimatedButton(t('ignore_remove'))
        btn_remove.setStyleSheet(_make_btn_style(C))
        btn_remove.clicked.connect(self._remove)
        input_row.addWidget(btn_remove)

        layout.addLayout(input_row)

        layout.addSpacing(6)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self.filter_status = QLabel()
        self._update_filter_status()
        filter_row.addWidget(self.filter_status)
        filter_row.addStretch()
        btn_filter = AnimatedButton(t('filter'))
        btn_filter.setStyleSheet(_make_btn_style(C))
        btn_filter.clicked.connect(self._open_filter)
        filter_row.addWidget(btn_filter)
        layout.addLayout(filter_row)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        for text, slot in [('OK', self._accept), ('Cancel', self.reject)]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(_make_btn_style(C))
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    def _update_filter_status(self):
        fc = self.filter_criteria
        active = any(fc.get(k) for k in ('time_start', 'time_end', 'size_min', 'size_max'))
        if active:
            self.filter_status.setText(t('filter_active'))
            self.filter_status.setStyleSheet(f"color: {C['accent_green']}; font-size: 9pt; background: transparent;")
        else:
            self.filter_status.setText('')
            self.filter_status.setStyleSheet("background: transparent;")

    def _open_filter(self):
        dlg = FilterDialog(self, criteria=self.filter_criteria)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.filter_criteria = dlg.criteria
            self._update_filter_status()

    def _add(self):
        text = self.input.text().strip()
        if text and text not in self.patterns:
            self.patterns.append(text)
            self.list_widget.addItem(text)
        self.input.clear()
        self.input.setFocus()

    def _remove(self):
        for item in self.list_widget.selectedItems():
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            if row < len(self.patterns):
                self.patterns.pop(row)

    def _accept(self):
        self.patterns = []
        for i in range(self.list_widget.count()):
            self.patterns.append(self.list_widget.item(i).text())
        self.accept()


# ---------- 筛选条件对话框 / Filter Criteria Dialog ----------
class FilterDialog(QDialog):
    def __init__(self, parent=None, criteria=None):
        super().__init__(parent)
        self.criteria = dict(criteria) if criteria else {
            'time_start': '', 'time_end': '',
            'size_min': '', 'size_max': '',
        }
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(t('filter_title'))
        self.setFixedSize(360, 250)
        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(8)

        label_style = f"color: {C['fg']}; font-size: 10pt; background: transparent;"
        hint_style = f"color: {C['fg2']}; font-size: 8pt; background: transparent;"
        input_style = f"""
            QLineEdit {{
                font-size: 10pt; padding: 4px 6px;
                background: {C['surface']}; color: {C['fg']};
                border: 1px solid {C['border']}; border-radius: 4px;
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """

        # Time range
        layout.addWidget(QLabel(t('filter_time_start')))
        time_row = QHBoxLayout()
        time_row.setSpacing(6)
        self.time_start = QLineEdit()
        self.time_start.setPlaceholderText('2024-01-01 00:00')
        self.time_start.setText(self.criteria.get('time_start', ''))
        self.time_start.setStyleSheet(input_style)
        time_row.addWidget(self.time_start)
        self.time_end = QLineEdit()
        self.time_end.setPlaceholderText('2024-12-31 23:59')
        self.time_end.setText(self.criteria.get('time_end', ''))
        self.time_end.setStyleSheet(input_style)
        time_row.addWidget(self.time_end)
        layout.addLayout(time_row)

        time_hint = QLabel(t('filter_time_hint'))
        time_hint.setStyleSheet(hint_style)
        time_hint.setWordWrap(True)
        layout.addWidget(time_hint)

        layout.addSpacing(4)

        # File size
        size_label = QLabel(t('filter_size_label'))
        size_label.setStyleSheet(label_style)
        layout.addWidget(size_label)

        size_row = QHBoxLayout()
        size_row.setSpacing(6)
        self.size_min = QLineEdit()
        self.size_min.setPlaceholderText('0')
        self.size_min.setText(self.criteria.get('size_min', ''))
        self.size_min.setStyleSheet(input_style)
        size_row.addWidget(self.size_min)

        size_lbl_min = QLabel(t('filter_size_min'))
        size_lbl_min.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        size_row.addWidget(size_lbl_min)

        self.size_max = QLineEdit()
        self.size_max.setPlaceholderText('')
        self.size_max.setText(self.criteria.get('size_max', ''))
        self.size_max.setStyleSheet(input_style)
        size_row.addWidget(self.size_max)

        size_lbl_max = QLabel(t('filter_size_max'))
        size_lbl_max.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        size_row.addWidget(size_lbl_max)
        layout.addLayout(size_row)

        size_hint = QLabel(t('filter_size_hint'))
        size_hint.setStyleSheet(hint_style)
        size_hint.setWordWrap(True)
        layout.addWidget(size_hint)

        layout.addSpacing(6)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_clear = AnimatedButton(t('filter_clear'))
        btn_clear.setStyleSheet(_make_btn_style(C))
        btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(btn_clear)

        for text, slot in [('OK', self._accept), ('Cancel', self.reject)]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(_make_btn_style(C))
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    def _clear(self):
        self.time_start.clear()
        self.time_end.clear()
        self.size_min.clear()
        self.size_max.clear()

    def _accept(self):
        self.criteria = {
            'time_start': self.time_start.text().strip(),
            'time_end': self.time_end.text().strip(),
            'size_min': self.size_min.text().strip(),
            'size_max': self.size_max.text().strip(),
        }
        self.accept()


# ---------- 可点击预览 / Clickable Preview ----------
class ClickablePreview(QPlainTextEdit):
    contextMenuRequested = pyqtSignal(int, QPoint)

    def contextMenuEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        block = cursor.block()
        line = block.blockNumber()
        if block.text().strip():
            self.contextMenuRequested.emit(line, event.globalPos())


# ---------- 主应用 / Main Application ----------
class DirTextApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folders = []
        self.config_path = "dirtext_config.json"
        self._load_config()
        self._color_mode = self.cfg.get('color_mode', 'light')
        C.update(THEMES[self._color_mode])
        self._faded_in = False
        self._pending_text = ""
        self._transition = TransitionManager()
        self._worker = None
        self._scanning = False
        self.structured_data = []
        self._full_preview_text = ""
        self._full_line_paths = []
        self._line_paths = []
        self._scan_total_dirs = 0
        self._scan_total_files = 0
        self.metadata_options = {
            'size': False, 'created': False, 'modified': False, 'accessed': False,
        }
        self.ignore_patterns = list(self.cfg.get('ignore_patterns', []))
        self.filter_criteria = dict(self.cfg.get('filter_criteria', {
            'time_start': '', 'time_end': '',
            'size_min': '', 'size_max': '',
        }))
        self.export_lang = LANG
        self.exporter = Exporter(
            app=self,
            t=t,
            lang=LANG,
            format_size=format_size,
            format_timestamp=format_timestamp,
            get_filtered_entries=self._get_filtered_entries,
            get_structured_data=lambda: self.structured_data,
            get_full_preview_text=lambda: self._full_preview_text,
            get_scan_total_dirs=lambda: self._scan_total_dirs,
            get_scan_total_files=lambda: self._scan_total_files,
        )
        self._copy_tip = None
        self._depth_timer = QTimer(self)
        self._depth_timer.setSingleShot(True)
        self._depth_timer.setInterval(1000)
        self._depth_timer.timeout.connect(self._apply_depth)
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(200)
        self._filter_timer.timeout.connect(self._apply_filter)
        self._progress_timer = QTimer(self)
        self._progress_timer.setSingleShot(True)
        self._progress_timer.setInterval(100)
        self._progress_timer.timeout.connect(self._flush_progress)
        self._pending_progress = 0
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_config)
        self._setup_ui()

    # ----- 配置读写 / Config read/write -----
    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.cfg = json.load(f)
        except:
            self.cfg = {"w": 900, "h": 650, "x": None, "y": None, "color_mode": "light",
                        "ignore_patterns": ["node_modules", ".git", "__pycache__", "*.pyc", "*.log", "*.tmp"]}

    def _save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, indent=2)
        except:
            pass

    def _remember_geometry(self):
        self.cfg['w'] = self.width()
        self.cfg['h'] = self.height()
        self.cfg['x'] = self.x()
        self.cfg['y'] = self.y()
        self._save_timer.start()

    # ----- 窗口事件 / Window Events -----
    def closeEvent(self, event):
        self._transition.stop_all()
        if hasattr(self, '_theme_anim') and self._theme_anim:
            try:
                self._theme_anim.stop()
            except:
                pass
        self.setWindowOpacity(1.0)
        self._save_timer.stop()
        self._progress_timer.stop()
        self._filter_timer.stop()
        self._remember_geometry()
        self._save_config()
        if self._worker is not None and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait(3000)
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.isVisible():
            self._remember_geometry()

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.isVisible():
            self._remember_geometry()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        added = 0
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path) and path not in self.folders:
                self.folders.append(path)
                added += 1
        if added:
            self._scan()

    # ----- 过渡效果 / Transition Effects -----
    def showEvent(self, event):
        super().showEvent(event)
        if not self._faded_in:
            self._faded_in = True
            self.setWindowOpacity(0.0)
            QTimer.singleShot(0, self._init_window_geometry)

    def _init_window_geometry(self):
        """延迟设置窗口位置并开始淡入，避免 __init__ 中提前创建原生窗口导致的卡顿。"""
        x, y = self.cfg.get('x'), self.cfg.get('y')
        w, h = self.cfg.get('w', 900), self.cfg.get('h', 650)
        if x is None or y is None:
            screen = self.screen().geometry()
            x = (screen.width() - w) // 2
            y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

        self._transition.animate(
            self, b"windowOpacity", 0.0, 1.0, 400,
            QEasingCurve.Type.OutCubic,
            on_finished=self._on_fade_in_done,
        )

    def _on_fade_in_done(self):
        QTimer.singleShot(300, self._auto_clipboard_check)

    # ----- 界面构建 / UI Building -----
    def _setup_ui(self):
        self._setup_window()
        layout = QVBoxLayout(self.centralWidget())
        layout.setContentsMargins(15, 15, 15, 10)
        layout.setSpacing(8)
        self._setup_header(layout)
        self._setup_search_bar(layout)
        self._setup_preview(layout)
        self._setup_progress_bar(layout)
        self._setup_button_bar(layout)
        self._show_welcome()
        self._apply_theme()
        self._apply_menu_style()

    def _setup_window(self):
        self.setWindowTitle(t('title'))
        self.setMinimumSize(780, 500)
        self.setAcceptDrops(True)

        w, h = self.cfg.get('w', 900), self.cfg.get('h', 650)
        self.resize(w, h)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

    def _setup_header(self, layout):
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        self.lbl_export_lang = QLabel(t('export_lang_label'))
        self.lbl_export_lang.setObjectName("lblExportLang")
        header_row.addWidget(self.lbl_export_lang)

        self.btn_export_lang = QPushButton('EN' if self.export_lang == 'en' else '中文')
        self.btn_export_lang.setObjectName("btnExportLang")
        self.btn_export_lang.setFixedSize(46, 22)
        self.btn_export_lang.clicked.connect(self._toggle_export_lang)
        header_row.addWidget(self.btn_export_lang)
        header_row.addStretch()

        self._title_label = QLabel(t('header'))
        self._title_label.setObjectName("titleLabel")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self._title_label)
        header_row.addStretch()

        # theme toggle button (sun/moon)
        is_dark = self._color_mode == 'dark'
        self.btn_theme = QPushButton('☀️' if is_dark else '🌙')
        self.btn_theme.setObjectName("btnTheme")
        self.btn_theme.setFixedSize(30, 28)
        self.btn_theme.clicked.connect(self._on_theme_toggle)
        header_row.addWidget(self.btn_theme)

        layout.addLayout(header_row)

        self._subtitle_label = QLabel(t('subtitle'))
        self._subtitle_label.setObjectName("subtitleLabel")
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._subtitle_label)

    def _setup_search_bar(self, layout):
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(t('search_placeholder'))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_input)

    def _setup_preview(self, layout):
        self.preview_frame = QWidget()
        self.preview_frame.setObjectName("previewFrame")
        frame_layout = QVBoxLayout(self.preview_frame)
        frame_layout.setContentsMargins(4, 4, 4, 4)

        self.preview = ClickablePreview()
        self.preview.setReadOnly(True)
        self.preview.contextMenuRequested.connect(self._on_preview_context_menu)
        self.preview.document().setDocumentMargin(10)
        self._apply_preview_colors(C)
        self._apply_preview_scrollbar(C)
        frame_layout.addWidget(self.preview)
        layout.addWidget(self.preview_frame, stretch=1)

        self._preview_effect = None  # created on-demand in _set_preview_text

    def _setup_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('0 items')
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

    def _setup_button_bar(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        self.btn_add = AnimatedButton(t('add'))
        self.btn_add.setObjectName("btnAdd")
        self.btn_add.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.btn_add)

        self.btn_clipboard = AnimatedButton(t('clipboard_load'))
        self.btn_clipboard.setObjectName("btnClipboard")
        self.btn_clipboard.clicked.connect(self.load_from_clipboard)
        btn_layout.addWidget(self.btn_clipboard)

        self.btn_clear = AnimatedButton(t('clear'))
        self.btn_clear.setObjectName("btnClear")
        self.btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_export = AnimatedButton(t('export'))
        self.btn_export.setObjectName("btnExport")
        self.btn_export.clicked.connect(self.export)
        btn_layout.addWidget(self.btn_export)

        self.btn_metadata = AnimatedButton(t('metadata'))
        self.btn_metadata.setObjectName("btnMetadata")
        self.btn_metadata.clicked.connect(self._show_metadata_dialog)
        btn_layout.addWidget(self.btn_metadata)

        self.btn_ignore = AnimatedButton(t('ignore_filter'))
        self.btn_ignore.setObjectName("btnIgnore")
        self.btn_ignore.clicked.connect(self._show_ignore_dialog)
        btn_layout.addWidget(self.btn_ignore)

        btn_layout.addStretch()

        # 递归深度输入 / Recursion depth input
        self._depth_prefix = QLabel(t('recursion_prefix'))
        self._depth_prefix.setObjectName("depthPrefix")
        btn_layout.addWidget(self._depth_prefix)

        self.depth_input = QLineEdit()
        self.depth_input.setObjectName("depthInput")
        self.depth_input.setText('0')
        self.depth_input.setFixedWidth(38)
        self.depth_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.depth_input.textChanged.connect(self._on_depth_input)
        btn_layout.addWidget(self.depth_input)

        self._depth_suffix = QLabel(t('recursion_suffix'))
        self._depth_suffix.setObjectName("depthSuffix")
        btn_layout.addWidget(self._depth_suffix)

        self._depth_hint = QLabel(t('recursion_hint'))
        self._depth_hint.setObjectName("depthHint")
        btn_layout.addWidget(self._depth_hint)

        layout.addLayout(btn_layout)

        self.status = self.statusBar()
        self.status.setObjectName("appStatusBar")
        self.status.showMessage(t('ready'))
        self.recursion_depth = 0

    # ----- 预览文本过渡 / Preview Text Transition -----
    def _set_preview_text(self, text, save_full=True):
        """预览文本淡入淡出：淡出 → 换文本 → 淡入。超过 PREVIEW_LINE_LIMIT 行则截断预览。"""
        # 移除旧的 graphics effect，让预览框正常显示父边框
        if self._preview_effect:
            self._transition.stop_target(self._preview_effect)
        self.preview.setGraphicsEffect(None)
        self._preview_effect = None
        if save_full:
            self._full_preview_text = text
        lines = text.split('\n')
        if len(lines) > PREVIEW_LINE_LIMIT:
            if LANG == 'en':
                notice = f"\n\n... Showing first {PREVIEW_LINE_LIMIT} of {len(lines)} lines — export to view full content."
            else:
                notice = f"\n\n... 仅显示前 {PREVIEW_LINE_LIMIT} 行（共 {len(lines)} 行）— 导出可查看完整内容。"
            text = '\n'.join(lines[:PREVIEW_LINE_LIMIT]) + notice
        self._pending_text = text

        # 创建临时 graphics effect 用于过渡动画，动画结束后移除
        if self._preview_effect is None:
            self._preview_effect = QGraphicsOpacityEffect(self.preview_frame)
            self._preview_effect.setOpacity(1.0)
            self.preview_frame.setGraphicsEffect(self._preview_effect)

        self._transition.animate(
            self._preview_effect, b"opacity", 1.0, 0.1, 100,
            QEasingCurve.Type.OutCubic,
            on_finished=self._on_preview_fade_out,
        )

    def _on_preview_fade_out(self):
        self.preview.setPlainText(self._pending_text)
        self._transition.animate(
            self._preview_effect, b"opacity", 0.1, 1.0, 100,
            QEasingCurve.Type.InCubic,
            on_finished=self._remove_preview_effect,
        )

    def _remove_preview_effect(self):
        """淡入完成后移除 graphics effect，确保 frame 边框正常渲染。"""
        if not self._preview_effect:
            return
        try:
            self._transition.stop_target(self._preview_effect)
        except RuntimeError:
            pass
        self.preview_frame.setGraphicsEffect(None)
        self._preview_effect = None

    def _show_welcome(self):
        self._set_preview_text(t('welcome'))

    def _on_preview_context_menu(self, line, global_pos):
        if line >= len(self._line_paths):
            return
        path = self._line_paths[line]
        if path is None or not os.path.exists(path):
            return

        def _copy_path():
            QApplication.clipboard().setText(path)
            self._show_copy_tip(global_pos, t('path_copied', path=path))

        menu = self.preview.createStandardContextMenu()
        menu.clear()
        menu.addAction(t('copy_path'), _copy_path)
        menu.addSeparator()
        menu.addAction(t('open_file'), lambda: os.startfile(path))
        menu.addAction(t('show_in_explorer'), lambda: subprocess.Popen(['explorer', '/select,', os.path.normpath(path)]))
        menu.exec(global_pos)

    def _show_copy_tip(self, pos, text):
        if hasattr(self, '_copy_tip') and self._copy_tip:
            try:
                self._transition.stop_target(self._copy_tip_effect)
                self._copy_tip.hide()
                self._copy_tip.deleteLater()
            except RuntimeError:
                pass
        if hasattr(self, '_copy_tip_timer') and self._copy_tip_timer:
            self._copy_tip_timer.stop()

        tip = QLabel(text, self)
        tip.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.WindowTransparentForInput
        )
        tip.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        tip.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        tip.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        tip.setAutoFillBackground(False)
        tip.setStyleSheet(f"""
            QLabel {{
                background: {C['surface']}; color: {C['fg']};
                border: 1px solid {C['border']};
                padding: 5px 10px; border-radius: 5px;
                font-size: 10pt;
            }}
        """)
        tip.adjustSize()
        tip.move(pos)

        effect = QGraphicsOpacityEffect(tip)
        effect.setOpacity(0.0)
        tip.setGraphicsEffect(effect)
        tip.show()

        self._copy_tip = tip
        self._copy_tip_effect = effect

        # fade in: fast start (transparent), slow end (opaque) → OutCubic
        self._transition.animate(
            effect, b"opacity", 0.0, 1.0, 350,
            QEasingCurve.Type.OutCubic,
            on_finished=self._on_copy_tip_fade_in_done,
        )

    def _on_copy_tip_fade_in_done(self):
        # stay at full opacity, then fade out
        self._copy_tip_timer = QTimer(self)
        self._copy_tip_timer.setSingleShot(True)
        self._copy_tip_timer.timeout.connect(self._fade_out_copy_tip)
        self._copy_tip_timer.start(1300)

    def _fade_out_copy_tip(self):
        if not hasattr(self, '_copy_tip_effect') or not self._copy_tip_effect:
            return
        # fade out: slow start (opaque), fast end (transparent) → InCubic
        self._transition.animate(
            self._copy_tip_effect, b"opacity", 1.0, 0.0, 350,
            QEasingCurve.Type.InCubic,
            on_finished=self._hide_copy_tip,
        )

    def _hide_copy_tip(self):
        if hasattr(self, '_copy_tip') and self._copy_tip:
            try:
                self._copy_tip.hide()
                self._copy_tip.deleteLater()
            except RuntimeError:
                pass
            self._copy_tip = None

    # ----- 核心功能 / Core Functions -----
    def add_folder(self):
        dlg = FolderSelectDialog(self, cfg=self.cfg)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        added = 0
        for path in dlg.selected_folders:
            if path not in self.folders:
                self.folders.append(path)
                added += 1
        if added:
            self._scan()
        elif dlg.selected_folders:
            QMessageBox.information(self, 'Info', t('dup_folder'))

    def _auto_clipboard_check(self):
        try:
            clip_text = QApplication.clipboard().text().strip()
        except Exception:
            return
        if not clip_text:
            return
        clip_text = clip_text.strip('"').strip("'")
        if os.path.isfile(clip_text):
            clip_text = os.path.dirname(clip_text)
        if not os.path.isdir(clip_text) or clip_text in self.folders:
            return
        reply = QMessageBox.question(
            self, t('clipboard_load'),
            t('clipboard_found', path=clip_text),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.folders.append(clip_text)
            self._scan()

    def load_from_clipboard(self):
        try:
            clip_text = QApplication.clipboard().text().strip()
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('clipboard_error', error=str(e)))
            return
        if not clip_text:
            QMessageBox.information(self, 'Info', t('clipboard_invalid'))
            return
        clip_text = clip_text.strip('"').strip("'")
        if os.path.isfile(clip_text):
            clip_text = os.path.dirname(clip_text)
        if not os.path.isdir(clip_text):
            QMessageBox.information(self, 'Info', t('clipboard_invalid'))
            return
        if clip_text in self.folders:
            QMessageBox.information(self, 'Info', t('dup_folder'))
            return
        reply = QMessageBox.question(
            self, t('clipboard_load'),
            t('clipboard_found', path=clip_text),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.folders.append(clip_text)
            self._scan()

    def clear(self):
        self.folders.clear()
        self.structured_data.clear()
        self._line_paths.clear()
        self._full_line_paths.clear()
        self._full_preview_text = ""
        self.filter_criteria = {'time_start': '', 'time_end': '', 'size_min': '', 'size_max': ''}
        self.search_input.clear()
        self._show_welcome()
        self.status.showMessage(t('ready'))

    # ----- 递归深度控制 / Recursion Depth Control -----
    def _on_depth_input(self):
        # Reset debounce timer on every keystroke
        if self._scanning:
            return
        self._depth_timer.start()

    def _on_search_text_changed(self):
        if self._scanning:
            return
        self._filter_timer.start()

    def _apply_depth(self):
        if self._scanning:
            return

        text = self.depth_input.text().strip()
        if not text:
            new_depth = 0
        else:
            match = re.match(r'^-?\d+', text)
            if match:
                new_depth = int(match.group())
            else:
                new_depth = 0
                self.depth_input.setText('0')

        if new_depth == self.recursion_depth:
            return

        self.recursion_depth = new_depth
        self._scan()

    # ----- 搜索过滤 / Search Filter -----
    def _parse_filter_criteria(self):
        """Convert string filter criteria to typed values.
        Returns (time_start, time_end, size_min_bytes, size_max_bytes)."""
        fc = self.filter_criteria
        time_start = None
        time_end = None
        size_min = None
        size_max = None

        for field in ('time_start', 'time_end'):
            val = fc.get(field, '').strip()
            if val:
                for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M', '%Y/%m/%d'):
                    try:
                        dt = datetime.strptime(val, fmt)
                        if field == 'time_end' and fmt in ('%Y-%m-%d', '%Y/%m/%d'):
                            dt = dt.replace(hour=23, minute=59, second=59)
                        if field == 'time_start':
                            time_start = dt
                        else:
                            time_end = dt
                        break
                    except ValueError:
                        continue

        for field in ('size_min', 'size_max'):
            val = fc.get(field, '').strip()
            if val:
                try:
                    kb = float(val)
                    bytes_val = int(kb * 1024)
                    if field == 'size_min':
                        size_min = bytes_val
                    else:
                        size_max = bytes_val
                except ValueError:
                    pass

        return time_start, time_end, size_min, size_max

    def _get_filtered_entries(self):
        """Return structured_data entries matching active time/size filters."""
        time_start, time_end, size_min, size_max = self._parse_filter_criteria()
        has_time = time_start is not None or time_end is not None
        has_size = size_min is not None or size_max is not None

        if not has_time and not has_size:
            return self.structured_data

        result = []
        for entry in self.structured_data:
            if has_time:
                ts = entry.get('modified', 0)
                if not ts:
                    if time_start is not None:
                        continue
                else:
                    dt = datetime.fromtimestamp(ts)
                    if time_start is not None and dt < time_start:
                        continue
                    if time_end is not None and dt > time_end:
                        continue

            if has_size and entry['type'] == 'file':
                size = entry.get('size', 0)
                if size_min is not None and size < size_min:
                    continue
                if size_max is not None and size > size_max:
                    continue

            result.append(entry)
        return result

    def _build_filtered_display(self, matching, extra_line=None):
        """Build filtered display lines and paths from matching entries."""
        sep = '═' * 80
        lines = []
        line_paths = []

        if not matching:
            lines.append(sep)
            line_paths.append(None)
            lines.append(f'  {t("no_filter_match")}')
            line_paths.append(None)
            lines.append(sep)
            line_paths.append(None)
        else:
            grouped = {}
            for e in matching:
                grouped.setdefault(e['folder'], []).append(e)

            for i, folder in enumerate(self.folders):
                if folder not in grouped:
                    continue
                entries = grouped[folder]
                lines.append(sep)
                line_paths.append(None)
                if LANG == 'en':
                    lines.append(f"Folder [{i + 1}]: {folder}")
                else:
                    lines.append(f"文件夹 [{i + 1}]：{folder}")
                line_paths.append(None)
                lines.append(sep)
                line_paths.append(None)

                entries.sort(key=lambda e: e['path'])
                for entry in entries:
                    try:
                        rel = os.path.relpath(entry['path'], folder)
                    except ValueError:
                        rel = entry['path']
                    if entry['type'] == 'dir':
                        lines.append(f"  {rel}/")
                    else:
                        lines.append(f"  {rel}")
                    line_paths.append(entry['path'])

            lines.append(sep)
            line_paths.append(None)
            if extra_line:
                lines.append(extra_line)
                line_paths.append(None)

        return lines, line_paths

    def _apply_filter(self):
        if not self._full_preview_text or not self.structured_data:
            return

        filtered = self._get_filtered_entries()
        text = self.search_input.text().strip()
        has_search = bool(text)
        has_criteria = any(self.filter_criteria.get(k)
                          for k in ('time_start', 'time_end', 'size_min', 'size_max'))

        if not has_search and not has_criteria:
            self._line_paths = list(self._full_line_paths)
            self._set_preview_text(self._full_preview_text, save_full=False)
            return

        if has_search:
            text_lower = text.lower()
            matching = [e for e in filtered if text_lower in e['name'].lower()]
        else:
            matching = filtered

        extra = t('filter_result', text=text, count=len(matching)) if has_search else None
        lines, line_paths = self._build_filtered_display(matching, extra_line=extra)
        self._line_paths = line_paths
        self._set_preview_text('\n'.join(lines), save_full=False)

    # ----- 扫描状态管理 / Scan State Management -----
    def _set_scanning_state(self, scanning):
        self._scanning = scanning
        self.btn_add.setEnabled(not scanning)
        self.btn_clipboard.setEnabled(not scanning)
        self.btn_export.setEnabled(not scanning)
        self.btn_ignore.setEnabled(not scanning)
        self.depth_input.setEnabled(not scanning)
        self.search_input.setEnabled(not scanning)
        try:
            self.btn_clear.clicked.disconnect()
        except TypeError:
            pass
        if scanning:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat('0 items')
            self.progress_bar.show()
            self.btn_clear.setEnabled(True)
            self.btn_clear.setText(t('cancel'))
            self.btn_clear.clicked.connect(self._cancel_scan)
        else:
            self.progress_bar.hide()
            self.btn_clear.setEnabled(True)
            self.btn_clear.setText(t('clear'))
            self.btn_clear.clicked.connect(self.clear)

    def _cancel_scan(self):
        if self._worker is not None:
            self._worker.abort()
            self.status.showMessage(t('cancelling'))
            self.btn_clear.setEnabled(False)

    def _on_folder_progress(self, folder):
        self.status.showMessage(t('scanning', path=folder))

    def _on_item_progress(self, count):
        self._pending_progress = count
        if not self._progress_timer.isActive():
            self._progress_timer.start()

    def _flush_progress(self):
        self.progress_bar.setFormat(f'{self._pending_progress} items')

    def _on_scan_finished(self, lines, total_dirs, total_files):
        if not self._scanning:
            return
        self.structured_data = self._worker.structured_data if self._worker else []
        self._line_paths = self._worker._line_paths if self._worker else []
        self._scan_total_dirs = total_dirs
        self._scan_total_files = total_files
        self._worker = None
        self._set_scanning_state(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat('%p%')
        self._full_preview_text = "\n".join(lines)
        self._full_line_paths = list(self._line_paths)
        self._apply_filter()
        msg = f"Scanned {len(self.folders)} folder(s)" if LANG == 'en' else f"已扫描 {len(self.folders)} 个文件夹"
        self.status.showMessage(msg)

    def _scan(self):
        if self._scanning:
            return
        if not self.folders:
            self._show_welcome()
            return
        self._set_scanning_state(True)
        self._worker = ScanWorker(self.folders, self.recursion_depth, self.ignore_patterns)
        self._worker.folder_progress.connect(self._on_folder_progress)
        self._worker.progress.connect(self._on_item_progress)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _toggle_export_lang(self):
        self.export_lang = 'en' if self.export_lang == 'zh' else 'zh'
        self.btn_export_lang.setText('EN' if self.export_lang == 'en' else '中文')

    def _apply_theme(self, intermediate=False):
        """应用主题样式：合并为单一 stylesheet，性能优化。

        Args:
            intermediate: 动画中间帧时跳过开销较大且视觉影响小的更新（menu、scrollbar）
        """
        c = C
        self.setStyleSheet(f"""
            QMainWindow {{ background: {c['bg']}; }}
            #centralWidget {{ background: {c['bg']}; }}

            #titleLabel {{
                font-size: 18px; font-weight: bold; color: {c['fg']};
                background: transparent;
            }}
            #subtitleLabel {{
                font-size: 9pt; color: {c['fg2']}; background: transparent;
            }}
            #lblExportLang {{
                color: {c['fg2']}; font-size: 8pt; background: transparent;
            }}
            #depthPrefix, #depthSuffix {{
                color: {c['fg2']}; font-size: 9pt; background: transparent;
            }}
            #depthHint {{
                color: {c['fg2']}; font-size: 8pt; background: transparent;
            }}

            #btnExportLang {{
                font-size: 8pt; padding: 0px;
                background: {c['surface']}; color: {c['fg2']};
                border: 1px solid {c['border']}; border-radius: 3px;
            }}
            #btnExportLang:hover {{ color: {c['fg']}; border-color: {c['accent']}; }}

            #btnTheme {{
                font-size: 14pt; padding: 0px; border: none; background: transparent;
            }}
            #btnTheme:hover {{ background: {c['hover_bg']}; border-radius: 4px; }}

            #btnAdd, #btnClipboard, #btnClear, #btnExport, #btnMetadata, #btnIgnore {{
                font-family: 'Microsoft YaHei'; font-weight: bold; font-size: 10pt;
                padding: 6px 20px; background: {c['surface']};
                color: {c['fg']}; border: 1px solid {c['border']}; border-radius: 4px;
            }}
            #btnAdd:hover, #btnClipboard:hover, #btnClear:hover,
            #btnExport:hover, #btnMetadata:hover, #btnIgnore:hover {{
                background: {c['hover_bg']};
            }}
            #btnAdd:pressed, #btnClipboard:pressed, #btnClear:pressed,
            #btnExport:pressed, #btnMetadata:pressed, #btnIgnore:pressed {{
                background: {c['pressed_bg']};
            }}

            #previewFrame {{
                border: 1px solid {c['border']}; border-radius: 4px;
                background: {c['surface']};
            }}

            #progressBar {{
                border: none; background: {c['progress_bg']};
                border-radius: 7px; font-size: 8pt;
                color: {c['fg']}; text-align: center;
            }}
            #progressBar::chunk {{
                background: {c['accent']}; border-radius: 7px;
            }}

            #searchInput {{
                font-size: 10pt; padding: 5px 8px;
                background: {c['surface']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 4px;
            }}
            #searchInput:focus {{ border-color: {c['accent']}; }}

            #depthInput {{
                font-size: 9pt; padding: 2px 2px;
                background: {c['surface']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 4px;
            }}
            #depthInput:focus {{ border-color: {c['accent']}; }}

            QStatusBar#appStatusBar {{ color: {c['fg2']}; font-size: 9pt; }}
        """)
        self._apply_preview_colors(c)
        if not intermediate:
            self._apply_preview_scrollbar(c)
            self._apply_menu_style()

    def _apply_preview_colors(self, c):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Base, QColor(c['surface']))
        p.setColor(QPalette.ColorRole.Text, QColor(c['fg']))
        p.setColor(QPalette.ColorRole.Window, QColor(c['surface']))
        p.setColor(QPalette.ColorRole.WindowText, QColor(c['fg']))
        p.setColor(QPalette.ColorRole.Highlight, QColor(c['accent']))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
        self.preview.setPalette(p)
        self.preview.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {c['surface']};
                color: {c['fg']};
                border: none;
                font-family: Consolas, 'Microsoft YaHei';
                font-size: 11pt;
            }}
        """)

    def _apply_preview_scrollbar(self, c):
        self.preview.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                width: 7px; background: transparent; margin: 2px 2px 2px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c['scroll_handle']}; border-radius: 3px; min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['scroll_handle_hover']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{ background: none; }}
        """)

    def _apply_menu_style(self):
        c = C
        QApplication.instance().setStyleSheet(f"""
            QMenu {{
                background: {c['surface']}; color: {c['fg']};
                border: 1px solid {c['border']}; padding: 4px 0;
            }}
            QMenu::item {{
                padding: 5px 24px;
            }}
            QMenu::item:selected {{
                background: {c['accent']}; color: white;
            }}
            QMenu::separator {{
                height: 1px; background: {c['border']};
                margin: 3px 10px;
            }}
        """)

    @staticmethod
    def _lerp_hex(a, b, t):
        ra, ga, ba = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
        rb, gb, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
        return f'#{int(ra+(rb-ra)*t):02x}{int(ga+(gb-ga)*t):02x}{int(ba+(bb-ba)*t):02x}'

    def _theme_tick(self, value):
        """QVariantAnimation valueChanged 回调：value 为经 eased 后的 0~1 值。"""
        for k in C:
            if k in self._theme_old_c and k in self._theme_new_c:
                C[k] = self._lerp_hex(self._theme_old_c[k], self._theme_new_c[k], value)
        self._apply_theme(intermediate=True)

    def _theme_finished(self):
        """动画完成：锁定最终颜色、保存配置、全量刷新。"""
        C.update(self._theme_new_c)
        self._color_mode = self._theme_new_mode
        self.btn_theme.setText('☀️' if self._color_mode == 'dark' else '🌙')
        self.cfg['color_mode'] = self._color_mode
        self._save_config()
        self._theme_animating = False
        self._theme_anim = None
        self._apply_theme(intermediate=False)

    def _on_theme_toggle(self):
        if getattr(self, '_theme_animating', False):
            return

        self._theme_animating = True
        self._theme_new_mode = 'dark' if self._color_mode == 'light' else 'light'
        self._theme_old_c = dict(C)
        self._theme_new_c = dict(THEMES[self._theme_new_mode])

        self._theme_anim = QVariantAnimation(self)
        self._theme_anim.setDuration(550)
        self._theme_anim.setStartValue(0.0)
        self._theme_anim.setEndValue(1.0)
        self._theme_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._theme_anim.valueChanged.connect(self._theme_tick)
        self._theme_anim.finished.connect(self._theme_finished)
        self._theme_anim.start()

    def _show_metadata_dialog(self):
        dlg = MetadataDialog(self, current_options=self.metadata_options,
                             t=t, C=C, make_btn_style=_make_btn_style)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.metadata_options = dlg.options

    def _show_ignore_dialog(self):
        dlg = IgnoreListDialog(self, patterns=self.ignore_patterns, filter_criteria=self.filter_criteria)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.ignore_patterns = dlg.patterns
            self.filter_criteria = dlg.filter_criteria
            self.cfg['ignore_patterns'] = self.ignore_patterns
            self.cfg['filter_criteria'] = self.filter_criteria
            self._save_config()
            if self.folders:
                self._scan()

    def export(self):
        if not self.structured_data and not self._full_preview_text:
            QMessageBox.warning(self, 'Warning', t('no_content'))
            return

        fmt_dlg = ExportFormatDialog(self, t=t, C=C, make_btn_style=_make_btn_style)
        if fmt_dlg.exec() != QDialog.DialogCode.Accepted:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for fmt in fmt_dlg.selected_formats:
            if fmt == 'csv':
                self.exporter.export_csv(timestamp)
            elif fmt == 'json':
                self.exporter.export_json(timestamp)
            elif fmt == 'xlsx':
                self.exporter.export_xlsx(timestamp)
            else:
                self.exporter.export_txt(timestamp)


# ---------- 入口 / Entry Point ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    f = app.font()
    f.setFamily('Microsoft YaHei')
    f.setPointSize(9)
    f.setWeight(QFont.Weight.Medium)
    app.setFont(f)
    window = DirTextApp()
    window.show()
    sys.exit(app.exec())
