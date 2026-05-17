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
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QFrame, QMainWindow, QWidget, QLabel, QPushButton,
    QPlainTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QDialog, QTreeView, QAbstractItemView,
    QComboBox, QProgressBar, QHeaderView, QGraphicsOpacityEffect,
    QLineEdit, QCheckBox, QListWidget
)
from PyQt6.QtCore import Qt, QTimer, QSortFilterProxyModel, QDir, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFileSystemModel, QFont, QPalette

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
        'welcome': "Welcome to Directory to Text\n\nInstructions:\n  1. Click 'Add Folder' or drag folders onto the window\n  2. Set depth in 'Recursion [N] Levels' (-1 = all, 0 = current)\n  3. Preview area shows the content\n  4. Click 'Export' to save\n  5. Click any file/dir name in preview to copy its path\n\nClick a button to get started",
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
    },
    'zh': {
        'title': 'DirText v3.6',
        'header': '文件目录提取器',
        'subtitle': '快速浏览文件夹内容并导出列表',
        'add': '添加文件夹',
        'clear': '清空选择',
        'export': '导出文本',
        'ready': '就绪',
        'welcome': '欢迎使用文件目录提取器\n\n使用说明：\n  1. 点击「添加文件夹」或拖入文件夹到窗口\n  2. 在"递归【N】层"中设置深度（-1 = 全部，0 = 当前层）\n  3. 预览区显示内容\n  4. 点击「导出文本」保存\n  5. 在预览中点击任意文件/文件夹名称即可复制路径\n\n点击按钮开始使用吧',
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


# ---------- 统一动画管理器 / Unified Transition Manager ----------
class TransitionManager:
    """管理应用内所有属性动画的生命周期与资源。

    - 持有运行中动画的强引用，防止 PyQt6 GC 回收导致动画中断
    - 统一创建和回收 graphicsEffect，避免复用冲突
    - 回调与链式衔接，无需硬编码延迟
    """

    def __init__(self):
        self._running = set()  # 持有引用，阻止 GC 回收运行中的动画

    def animate(self, target, prop_name, start_val, end_val,
                duration=300, easing=None, on_finished=None):
        """创建并启动一个受管理的属性动画，自动处理清理。"""
        anim = QPropertyAnimation(target, prop_name)
        anim.setDuration(duration)
        anim.setStartValue(start_val)
        anim.setEndValue(end_val)
        if easing:
            anim.setEasingCurve(easing)

        self._running.add(anim)
        anim.finished.connect(lambda a=anim, cb=on_finished: self._on_finished(a, cb))
        anim.start()
        return anim

    def _on_finished(self, anim, callback=None):
        self._running.discard(anim)
        if callback:
            callback()
        anim.deleteLater()  # 断开信号连接，彻底释放 C++ 资源

    def stop_target(self, target):
        """停止作用于 target 对象的所有动画，并清理。"""
        for anim in list(self._running):
            try:
                if anim.targetObject() is target:
                    anim.stop()
                    self._running.discard(anim)
                    anim.deleteLater()
            except RuntimeError:
                self._running.discard(anim)

    def stop_all(self):
        """停止全部动画并清理。"""
        for anim in self._running:
            try:
                anim.stop()
            except RuntimeError:
                pass
        self._running.clear()


# ---------- 交互动画按钮 / Animated Button ----------
class AnimatedButton(QPushButton):
    """带悬停高亮和按压反馈动画的按钮"""

    _shared_tm = TransitionManager()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.92)
        self.setGraphicsEffect(self._effect)
        self.destroyed.connect(self._cleanup_effect)

    def _cleanup_effect(self):
        if self._effect:
            AnimatedButton._shared_tm.stop_target(self._effect)
            self._effect.deleteLater()
            self._effect = None

    def enterEvent(self, event):
        AnimatedButton._shared_tm.stop_target(self._effect)
        AnimatedButton._shared_tm.animate(
            self._effect, b"opacity", 0.92, 1.0, 180,
            QEasingCurve.Type.OutCubic,
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        AnimatedButton._shared_tm.stop_target(self._effect)
        AnimatedButton._shared_tm.animate(
            self._effect, b"opacity", 1.0, 0.92, 180,
            QEasingCurve.Type.OutCubic,
        )
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        AnimatedButton._shared_tm.stop_target(self._effect)
        self._effect.setOpacity(0.72)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        AnimatedButton._shared_tm.animate(
            self._effect, b"opacity", 0.72, 1.0, 220,
            QEasingCurve.Type.OutCubic,
        )
        super().mouseReleaseEvent(event)


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
class FormatOption(QWidget):
    toggled = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._selected = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        self._circle = QLabel()
        self._circle.setFixedWidth(16)
        self._text = QLabel(text)
        self._text.setStyleSheet(f"color: {C['fg']}; font-size: 10pt; background: transparent;")
        layout.addWidget(self._circle)
        layout.addWidget(self._text)
        layout.addStretch()
        self._update_circle()

    def _update_circle(self):
        if self._selected:
            self._circle.setText(f'<span style="color: {C["accent_green"]}; font-size: 11pt;">●</span>')
        else:
            self._circle.setText(f'<span style="color: {C["option_circle"]}; font-size: 11pt;">○</span>')

    def set_selected(self, v):
        self._selected = v
        self._update_circle()

    def mousePressEvent(self, event):
        if not self._selected:
            self.set_selected(True)
            self.toggled.emit()


class ExportFormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_format = 'txt'
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(t('export_format'))
        self.setFixedSize(300, 195)
        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(8)

        prompt = QLabel(t('format_prompt'))
        prompt.setStyleSheet(f"color: {C['fg']}; font-size: 10pt; background: transparent;")
        layout.addWidget(prompt)

        self.opt_txt = FormatOption(t('format_txt'))
        self.opt_txt.set_selected(True)
        self.opt_txt.toggled.connect(lambda: self._on_option_toggled('txt'))
        layout.addWidget(self.opt_txt)

        self.opt_csv = FormatOption(t('format_csv'))
        self.opt_csv.toggled.connect(lambda: self._on_option_toggled('csv'))
        layout.addWidget(self.opt_csv)

        self.opt_json = FormatOption(t('format_json'))
        self.opt_json.toggled.connect(lambda: self._on_option_toggled('json'))
        layout.addWidget(self.opt_json)

        layout.addSpacing(6)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        for text, slot in [('OK', self._accept), ('Cancel', self.reject)]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(_make_btn_style(C))
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _on_option_toggled(self, fmt):
        self.selected_format = fmt
        self.opt_txt.set_selected(fmt == 'txt')
        self.opt_csv.set_selected(fmt == 'csv')
        self.opt_json.set_selected(fmt == 'json')

    def _accept(self):
        self.accept()


class MetadataDialog(QDialog):
    def __init__(self, parent=None, current_options=None):
        super().__init__(parent)
        self.options = dict(current_options) if current_options else {
            'size': False, 'created': False, 'modified': False, 'accessed': False,
        }
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(t('metadata_title'))
        self.setFixedSize(320, 280)
        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(8)

        prompt = QLabel(t('metadata_prompt'))
        prompt.setStyleSheet(f"color: {C['fg']}; font-size: 10pt; background: transparent;")
        layout.addWidget(prompt)

        hint = QLabel(t('metadata_txt_hint'))
        hint.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        checkbox_style = f"color: {C['fg']}; font-size: 10pt; background: transparent;"

        self.cb_size = QCheckBox(t('metadata_size'))
        self.cb_size.setChecked(self.options.get('size', False))
        self.cb_size.setStyleSheet(checkbox_style)
        layout.addWidget(self.cb_size)

        self.cb_created = QCheckBox(t('metadata_created'))
        self.cb_created.setChecked(self.options.get('created', False))
        self.cb_created.setStyleSheet(checkbox_style)
        layout.addWidget(self.cb_created)

        self.cb_modified = QCheckBox(t('metadata_modified'))
        self.cb_modified.setChecked(self.options.get('modified', False))
        self.cb_modified.setStyleSheet(checkbox_style)
        layout.addWidget(self.cb_modified)

        self.cb_accessed = QCheckBox(t('metadata_accessed'))
        self.cb_accessed.setChecked(self.options.get('accessed', False))
        self.cb_accessed.setStyleSheet(checkbox_style)
        layout.addWidget(self.cb_accessed)

        layout.addSpacing(6)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        for text, slot in [('OK', self._accept), ('Cancel', self.reject)]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(_make_btn_style(C))
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _accept(self):
        self.options = {
            'size': self.cb_size.isChecked(),
            'created': self.cb_created.isChecked(),
            'modified': self.cb_modified.isChecked(),
            'accessed': self.cb_accessed.isChecked(),
        }
        self.accept()


# ---------- 忽略列表对话框 / Ignore List Dialog ----------
class IgnoreListDialog(QDialog):
    def __init__(self, parent=None, patterns=None):
        super().__init__(parent)
        self.patterns = list(patterns) if patterns else []
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

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        for text, slot in [('OK', self._accept), ('Cancel', self.reject)]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(_make_btn_style(C))
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

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


# ---------- 可点击预览 / Clickable Preview ----------
class ClickablePreview(QPlainTextEdit):
    lineClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            block = cursor.block()
            line = block.blockNumber()
            if block.text().strip():
                self.lineClicked.emit(line)
        super().mouseReleaseEvent(event)


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
        self._line_paths = []
        self._scan_total_dirs = 0
        self._scan_total_files = 0
        self.metadata_options = {
            'size': False, 'created': False, 'modified': False, 'accessed': False,
        }
        self.ignore_patterns = list(self.cfg.get('ignore_patterns', []))
        self.export_lang = LANG
        self._copy_tip = None
        self._depth_timer = QTimer(self)
        self._depth_timer.setSingleShot(True)
        self._depth_timer.setInterval(1000)
        self._depth_timer.timeout.connect(self._apply_depth)
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
        if hasattr(self, '_theme_timer') and self._theme_timer:
            try:
                self._theme_timer.stop()
                self._theme_timer.timeout.disconnect()
                self._theme_timer.deleteLater()
            except:
                pass
        self.setWindowOpacity(1.0)
        self._save_timer.stop()
        self._progress_timer.stop()
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
        self._setup_preview(layout)
        self._setup_progress_bar(layout)
        self._setup_button_bar(layout)
        self._show_welcome()
        self._apply_menu_style()

    def _setup_window(self):
        self.setWindowTitle(t('title'))
        self.setMinimumSize(780, 500)
        self.setStyleSheet(f"QMainWindow {{ background: {C['bg']}; }}")
        self.setAcceptDrops(True)

        w, h = self.cfg.get('w', 900), self.cfg.get('h', 650)
        self.resize(w, h)

        central = QWidget()
        central.setObjectName("centralWidget")
        central.setStyleSheet(f"#centralWidget {{ background: {C['bg']}; }}")
        self.setCentralWidget(central)

    def _setup_header(self, layout):
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        self.lbl_export_lang = QLabel(t('export_lang_label'))
        self.lbl_export_lang.setStyleSheet(f"color: {C['fg2']}; font-size: 8pt; background: transparent;")
        header_row.addWidget(self.lbl_export_lang)

        self.btn_export_lang = QPushButton('EN' if self.export_lang == 'en' else '中文')
        self.btn_export_lang.setFixedSize(46, 22)
        self.btn_export_lang.setStyleSheet(f"""
            QPushButton {{
                font-size: 8pt; padding: 0px;
                background: {C['surface']}; color: {C['fg2']};
                border: 1px solid {C['border']}; border-radius: 3px;
            }}
            QPushButton:hover {{ color: {C['fg']}; border-color: {C['accent']}; }}
        """)
        self.btn_export_lang.clicked.connect(self._toggle_export_lang)
        header_row.addWidget(self.btn_export_lang)
        header_row.addStretch()

        self._title_label = QLabel(t('header'))
        self._title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {C['fg']}; background: transparent;")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self._title_label)
        header_row.addStretch()

        # theme toggle button (sun/moon)
        is_dark = self._color_mode == 'dark'
        self.btn_theme = QPushButton('☀️' if is_dark else '🌙')
        self.btn_theme.setFixedSize(30, 28)
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                font-size: 14pt; padding: 0px; border: none; background: transparent;
            }}
            QPushButton:hover {{ background: {C['hover_bg']}; border-radius: 4px; }}
        """)
        self.btn_theme.clicked.connect(self._on_theme_toggle)
        header_row.addWidget(self.btn_theme)

        layout.addLayout(header_row)

        self._subtitle_label = QLabel(t('subtitle'))
        self._subtitle_label.setStyleSheet(f"font-size: 9pt; color: {C['fg2']}; background: transparent;")
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._subtitle_label)

    def _setup_preview(self, layout):
        self.preview_frame = QWidget()
        self.preview_frame.setObjectName("previewFrame")
        self.preview_frame.setStyleSheet(f"""
            #previewFrame {{
                border: 1px solid {C['border']}; border-radius: 4px;
                background: {C['surface']};
            }}
        """)
        frame_layout = QVBoxLayout(self.preview_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = ClickablePreview()
        self.preview.setReadOnly(True)
        self.preview.lineClicked.connect(self._on_preview_line_clicked)
        self.preview.document().setDocumentMargin(10)
        self._apply_preview_colors(C)
        self._apply_preview_scrollbar(C)
        frame_layout.addWidget(self.preview)
        layout.addWidget(self.preview_frame, stretch=1)

        self._preview_effect = QGraphicsOpacityEffect(self.preview)
        self._preview_effect.setOpacity(1.0)
        self.preview.setGraphicsEffect(self._preview_effect)

    def _setup_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('0 items')
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; background: {C['progress_bg']};
                border-radius: 7px; font-size: 8pt;
                color: {C['fg']}; text-align: center;
            }}
            QProgressBar::chunk {{
                background: {C['accent']};
                border-radius: 7px;
            }}
        """)
        layout.addWidget(self.progress_bar)

    def _setup_button_bar(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        self.btn_add = AnimatedButton(t('add'))
        self.btn_add.setStyleSheet(_make_btn_style(C))
        self.btn_add.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.btn_add)

        self.btn_clipboard = AnimatedButton(t('clipboard_load'))
        self.btn_clipboard.setStyleSheet(_make_btn_style(C))
        self.btn_clipboard.clicked.connect(self.load_from_clipboard)
        btn_layout.addWidget(self.btn_clipboard)

        self.btn_clear = AnimatedButton(t('clear'))
        self.btn_clear.setStyleSheet(_make_btn_style(C))
        self.btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_export = AnimatedButton(t('export'))
        self.btn_export.setStyleSheet(_make_btn_style(C))
        self.btn_export.clicked.connect(self.export)
        btn_layout.addWidget(self.btn_export)

        self.btn_metadata = AnimatedButton(t('metadata'))
        self.btn_metadata.setStyleSheet(_make_btn_style(C))
        self.btn_metadata.clicked.connect(self._show_metadata_dialog)
        btn_layout.addWidget(self.btn_metadata)

        self.btn_ignore = AnimatedButton(t('ignore'))
        self.btn_ignore.setStyleSheet(_make_btn_style(C))
        self.btn_ignore.clicked.connect(self._show_ignore_dialog)
        btn_layout.addWidget(self.btn_ignore)

        btn_layout.addStretch()

        # 递归深度输入 / Recursion depth input
        self._depth_prefix = QLabel(t('recursion_prefix'))
        self._depth_prefix.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        btn_layout.addWidget(self._depth_prefix)

        self.depth_input = QLineEdit()
        self.depth_input.setText('0')
        self.depth_input.setFixedWidth(38)
        self.depth_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.depth_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 9pt; padding: 2px 2px;
                background: {C['surface']}; color: {C['fg']};
                border: 1px solid {C['border']}; border-radius: 4px;
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """)
        self.depth_input.textChanged.connect(self._on_depth_input)
        btn_layout.addWidget(self.depth_input)

        self._depth_suffix = QLabel(t('recursion_suffix'))
        self._depth_suffix.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt; background: transparent;")
        btn_layout.addWidget(self._depth_suffix)

        self._depth_hint = QLabel(t('recursion_hint'))
        self._depth_hint.setStyleSheet(f"color: {C['fg2']}; font-size: 8pt; background: transparent;")
        btn_layout.addWidget(self._depth_hint)

        layout.addLayout(btn_layout)

        self.status = self.statusBar()
        self.status.setStyleSheet(f"color: {C['fg2']}; font-size: 9pt;")
        self.status.showMessage(t('ready'))
        self.recursion_depth = 0

    # ----- 预览文本过渡 / Preview Text Transition -----
    def _set_preview_text(self, text):
        """预览文本淡入淡出：淡出 → 换文本 → 淡入。超过 PREVIEW_LINE_LIMIT 行则截断预览。"""
        self._transition.stop_target(self._preview_effect)
        self._full_preview_text = text
        lines = text.split('\n')
        if len(lines) > PREVIEW_LINE_LIMIT:
            if LANG == 'en':
                notice = f"\n\n... Showing first {PREVIEW_LINE_LIMIT} of {len(lines)} lines — export to view full content."
            else:
                notice = f"\n\n... 仅显示前 {PREVIEW_LINE_LIMIT} 行（共 {len(lines)} 行）— 导出可查看完整内容。"
            text = '\n'.join(lines[:PREVIEW_LINE_LIMIT]) + notice
        self._pending_text = text
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
        )

    def _show_welcome(self):
        self._set_preview_text(t('welcome'))

    def _on_preview_line_clicked(self, line):
        if line < len(self._line_paths):
            path = self._line_paths[line]
            if path is not None:
                QApplication.clipboard().setText(path)
                cursor = self.preview.textCursor()
                block = self.preview.document().findBlockByLineNumber(line)
                cursor.setPosition(block.position())
                rect = self.preview.cursorRect(cursor)
                pos = self.preview.mapToGlobal(rect.topLeft())
                self._show_copy_tip(pos, t('path_copied', path=path))

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
        self._full_preview_text = ""
        self._show_welcome()
        self.status.showMessage(t('ready'))

    # ----- 递归深度控制 / Recursion Depth Control -----
    def _on_depth_input(self):
        # Reset debounce timer on every keystroke
        if self._scanning:
            return
        self._depth_timer.start()

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
        
    # ----- 扫描状态管理 / Scan State Management -----
    def _set_scanning_state(self, scanning):
        self._scanning = scanning
        self.btn_add.setEnabled(not scanning)
        self.btn_clipboard.setEnabled(not scanning)
        self.btn_export.setEnabled(not scanning)
        self.btn_ignore.setEnabled(not scanning)
        self.depth_input.setEnabled(not scanning)
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
        self._set_preview_text("\n".join(lines))
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

    def _apply_theme(self):
        c = C
        self.setStyleSheet(f"QMainWindow {{ background: {c['bg']}; }}")
        self.centralWidget().setStyleSheet(f"#centralWidget {{ background: {c['bg']}; }}")

        btn_style = _make_btn_style(c)
        for btn in [self.btn_add, self.btn_clipboard, self.btn_clear,
                     self.btn_export, self.btn_metadata, self.btn_ignore]:
            btn.setStyleSheet(btn_style)

        self.btn_export_lang.setStyleSheet(f"""
            QPushButton {{
                font-size: 8pt; padding: 0px;
                background: {c['surface']}; color: {c['fg2']};
                border: 1px solid {c['border']}; border-radius: 3px;
            }}
            QPushButton:hover {{ color: {c['fg']}; border-color: {c['accent']}; }}
        """)
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                font-size: 14pt; padding: 0px; border: none; background: transparent;
            }}
            QPushButton:hover {{ background: {c['hover_bg']}; border-radius: 4px; }}
        """)
        self.lbl_export_lang.setStyleSheet(
            f"color: {c['fg2']}; font-size: 8pt; background: transparent;")

        self._title_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {c['fg']}; background: transparent;")
        self._subtitle_label.setStyleSheet(
            f"font-size: 9pt; color: {c['fg2']}; background: transparent;")

        self.preview_frame.setStyleSheet(f"""
            #previewFrame {{
                border: 1px solid {c['border']};
                border-radius: 4px;
                background: {c['surface']};
            }}
        """)
        self._apply_preview_colors(c)
        self._apply_preview_scrollbar(c)

        self.preview_frame.update()
        self.preview_frame.repaint()

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; background: {c['progress_bg']};
                border-radius: 7px; font-size: 8pt;
                color: {c['fg']}; text-align: center;
            }}
            QProgressBar::chunk {{
                background: {c['accent']}; border-radius: 7px;
            }}
        """)

        self.depth_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 9pt; padding: 2px 2px;
                background: {c['surface']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 4px;
            }}
            QLineEdit:focus {{ border-color: {c['accent']}; }}
        """)

        self._depth_prefix.setStyleSheet(
            f"color: {c['fg2']}; font-size: 9pt; background: transparent;")
        self._depth_suffix.setStyleSheet(
            f"color: {c['fg2']}; font-size: 9pt; background: transparent;")
        self._depth_hint.setStyleSheet(
            f"color: {c['fg2']}; font-size: 8pt; background: transparent;")

        self.status.setStyleSheet(f"color: {c['fg2']}; font-size: 9pt;")

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

        self.preview.update()
        self.preview.repaint()

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

    def _theme_tick(self):
        t = min((time.perf_counter() - self._theme_t0) / 0.55, 1.0)
        if t >= 1.0:
            C.update(self._theme_new_c)
            self._color_mode = self._theme_new_mode
            self.btn_theme.setText('☀️' if self._color_mode == 'dark' else '🌙')
            self.cfg['color_mode'] = self._color_mode
            self._save_config()

            self._theme_animating = False

            if hasattr(self, '_theme_timer') and self._theme_timer:
                try:
                    self._theme_timer.stop()
                    self._theme_timer.timeout.disconnect()
                    self._theme_timer.deleteLater()
                except:
                    pass
                self._theme_timer = None

            self._apply_theme()
            self._apply_menu_style()
        else:
            eased = 1.0 - (1.0 - t) ** 3
            for k in C:
                if k in self._theme_old_c and k in self._theme_new_c:
                    C[k] = self._lerp_hex(self._theme_old_c[k], self._theme_new_c[k], eased)
            self._apply_theme()

    def _on_theme_toggle(self):
        if getattr(self, '_theme_animating', False):
            return

        if hasattr(self, '_theme_timer') and self._theme_timer is not None:
            try:
                self._theme_timer.stop()
                self._theme_timer.timeout.disconnect()
            except:
                pass
            try:
                self._theme_timer.deleteLater()
            except:
                pass
            self._theme_timer = None

        self._theme_animating = True
        self._theme_new_mode = 'dark' if self._color_mode == 'light' else 'light'
        self._theme_old_c = dict(C)
        self._theme_new_c = dict(THEMES[self._theme_new_mode])
        self._theme_t0 = time.perf_counter()

        self._theme_timer = QTimer(self)
        self._theme_timer.timeout.connect(self._theme_tick)
        self._theme_timer.start(30)

    def _show_metadata_dialog(self):
        dlg = MetadataDialog(self, current_options=self.metadata_options)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.metadata_options = dlg.options

    def _show_ignore_dialog(self):
        dlg = IgnoreListDialog(self, patterns=self.ignore_patterns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.ignore_patterns = dlg.patterns
            self.cfg['ignore_patterns'] = self.ignore_patterns
            self._save_config()
            if self.folders:
                self._scan()

    def export(self):
        if not self.structured_data and not self._full_preview_text:
            QMessageBox.warning(self, 'Warning', t('no_content'))
            return

        fmt_dlg = ExportFormatDialog(self)
        if fmt_dlg.exec() != QDialog.DialogCode.Accepted:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if fmt_dlg.selected_format == 'csv':
            self._export_csv(timestamp)
        elif fmt_dlg.selected_format == 'json':
            self._export_json(timestamp)
        else:
            self._export_txt(timestamp)

    def _export_txt(self, timestamp):
        fname, _ = QFileDialog.getSaveFileName(
            self, t('save_title'),
            t('file_name', ts=timestamp),
            'Text files (*.txt);;All files (*.*)',
        )
        if not fname:
            return
        try:
            el = self.export_lang
            text = self._build_txt_content(el) if el != LANG else self._full_preview_text
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(text + f"\n\nGenerated: {datetime.now():%Y-%m-%d %H:%M:%S}")
            QMessageBox.information(self, 'Success', t('success', path=fname))
            self.status.showMessage(os.path.basename(fname))
            self._open_export_folder(fname)
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('fail', error=str(e)))

    def _build_txt_content(self, lang):
        """Rebuild TXT content from scan data using the given language."""
        sep = '═' * 80
        lines = []
        for i, folder in enumerate(self.folders):
            lines.append(sep)
            if lang == 'en':
                lines.append(f"Folder [{i + 1}]: {folder}")
            else:
                lines.append(f"文件夹 [{i + 1}]：{folder}")
            lines.append(sep)
            self._build_tree_lines(folder, self.recursion_depth, 0, '', lang, lines)
            lines.append('')
        lines.append(sep)
        if lang == 'en':
            lines.append(f"Total: {len(self.folders)} folder(s)")
            lines.append(f"         {self._scan_total_dirs} folders, {self._scan_total_files} files")
        else:
            lines.append(f"总计：{len(self.folders)} 个文件夹")
            lines.append(f"         共 {self._scan_total_dirs} 个文件夹，{self._scan_total_files} 个文件")
        return '\n'.join(lines)

    def _build_tree_lines(self, folder, max_depth, current_depth, prefix, lang, lines):
        """Recursively build tree lines for TXT export."""
        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name)
            if self.ignore_patterns:
                entries = [e for e in entries
                           if not any(fnmatch.fnmatch(e.name, p)
                                      for p in self.ignore_patterns)]
        except PermissionError:
            msg = '<Access denied>' if lang == 'en' else '<无法访问>'
            lines.append(f"{prefix}└── {msg}")
            return
        except Exception as e:
            lines.append(f"{prefix}└── <Error: {e}>")
            return

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                if max_depth == -1 or current_depth < max_depth:
                    self._build_tree_lines(entry.path, max_depth, current_depth + 1,
                                           prefix + child_prefix, lang, lines)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    @staticmethod
    def _open_export_folder(fname):
        folder = os.path.dirname(fname)
        desktop = os.path.normpath(os.path.join(os.path.expanduser('~'), 'Desktop'))
        if os.path.normpath(folder) == desktop:
            SHCNE_UPDATEDIR = 0x00001000
            SHCNF_PATHW = 0x0005
            ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, SHCNF_PATHW, folder, None)
        else:
            os.startfile(folder)

    def _export_csv(self, timestamp):
        fname, _ = QFileDialog.getSaveFileName(
            self, t('csv_save_title'),
            t('csv_file_name', ts=timestamp),
            'CSV files (*.csv);;All files (*.*)',
        )
        if not fname:
            return
        total = len(self.structured_data)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(t('export_progress'))
        self.progress_bar.show()
        self.status.showMessage(t('exporting'))
        el = self.export_lang
        try:
            with open(fname, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                meta = self.metadata_options
                headers = [
                    t('csv_col_folder', lang=el), t('csv_col_name', lang=el), t('csv_col_path', lang=el),
                    t('csv_col_type', lang=el), t('csv_col_level', lang=el),
                ]
                if meta.get('size'):
                    headers.append(t('csv_col_size', lang=el))
                if meta.get('created'):
                    headers.append(t('csv_col_created', lang=el))
                if meta.get('modified'):
                    headers.append(t('csv_col_modified', lang=el))
                if meta.get('accessed'):
                    headers.append(t('csv_col_accessed', lang=el))
                writer.writerow(headers)

                for i, entry in enumerate(self.structured_data):
                    row = [
                        entry['folder'], entry['name'], entry['path'],
                        t('csv_type_dir', lang=el) if entry['type'] == 'dir' else t('csv_type_file', lang=el),
                        entry['level'],
                    ]
                    if meta.get('size'):
                        if entry['type'] == 'file':
                            row.append(f"{entry['size']} B")
                        else:
                            row.append('')
                    if meta.get('created'):
                        row.append(format_timestamp(entry['created']))
                    if meta.get('modified'):
                        row.append(format_timestamp(entry['modified']))
                    if meta.get('accessed'):
                        row.append(format_timestamp(entry['accessed']))
                    writer.writerow(row)
                    if i % 50 == 0:
                        self.progress_bar.setValue(i + 1)
                self.progress_bar.setValue(total)
            success_msg = t('success', path=fname)
            if any(meta.get(k) for k in ('created', 'modified', 'accessed')):
                success_msg += '\n\n' + t('csv_excel_hint')
            QMessageBox.information(self, 'Success', success_msg)
            self.status.showMessage(os.path.basename(fname))
            self._open_export_folder(fname)
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('fail', error=str(e)))
        finally:
            self.progress_bar.hide()

    def _export_json(self, timestamp):
        fname, _ = QFileDialog.getSaveFileName(
            self, t('json_save_title'),
            t('json_file_name', ts=timestamp),
            'JSON files (*.json);;All files (*.*)',
        )
        if not fname:
            return
        total = len(self.structured_data)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(t('export_progress'))
        self.progress_bar.show()
        self.status.showMessage(t('exporting'))
        el = self.export_lang
        try:
            meta = self.metadata_options
            data = []
            for i, entry in enumerate(self.structured_data):
                item = {
                    t('csv_col_folder', lang=el): entry['folder'],
                    t('csv_col_name', lang=el): entry['name'],
                    t('csv_col_path', lang=el): entry['path'],
                    t('csv_col_type', lang=el): t('csv_type_dir', lang=el) if entry['type'] == 'dir' else t('csv_type_file', lang=el),
                    t('csv_col_level', lang=el): entry['level'],
                }
                if meta.get('size'):
                    item['size_bytes'] = entry['size'] if entry['type'] == 'file' else 0
                    item['size'] = format_size(entry['size']) if entry['type'] == 'file' else '-'
                if meta.get('created'):
                    item['created'] = format_timestamp(entry['created'])
                    item['created_timestamp'] = entry['created']
                if meta.get('modified'):
                    item['modified'] = format_timestamp(entry['modified'])
                    item['modified_timestamp'] = entry['modified']
                if meta.get('accessed'):
                    item['accessed'] = format_timestamp(entry['accessed'])
                    item['accessed_timestamp'] = entry['accessed']
                data.append(item)
                if i % 50 == 0:
                    self.progress_bar.setValue(i + 1)
            self.progress_bar.setValue(total)

            export = {
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'folders': self.folders,
                'total_folders': len(self.folders),
                'total_dirs': sum(1 for e in self.structured_data if e['type'] == 'dir'),
                'total_files': sum(1 for e in self.structured_data if e['type'] == 'file'),
                'entries': data,
            }
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(export, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, 'Success', t('success', path=fname))
            self.status.showMessage(os.path.basename(fname))
            self._open_export_folder(fname)
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('fail', error=str(e)))
        finally:
            self.progress_bar.hide()


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
