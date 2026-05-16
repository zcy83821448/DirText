"""
DirText - Directory to Text (PyQt6)
A lightweight directory listing tool with PyQt6 GUI.
轻量级文件夹目录提取工具 - PyQt6 版本
Automatically switches UI language based on system locale.
根据系统区域自动切换界面语言。
"""

import csv
import json
import locale
import os
import platform
import re
import sys
import time
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QPlainTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QDialog, QTreeView, QAbstractItemView,
    QComboBox, QProgressBar, QHeaderView, QGraphicsOpacityEffect, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QSortFilterProxyModel, QDir, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread
from PyQt6.QtGui import QFileSystemModel

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
        'title': 'DirText v3.0',
        'header': 'Directory to Text',
        'subtitle': 'Quickly browse folder contents and export list',
        'add': 'Add Folder',
        'clear': 'Clear',
        'export': 'Export',
        'ready': 'Ready',
        'welcome': "Welcome to Directory to Text\n\nInstructions:\n  1. Click 'Add Folder' or drag folders onto the window\n  2. Set depth in 'Recursion [N] Levels' (-1 = all, 0 = current)\n  3. Preview area shows the content\n  4. Click 'Export' to save\n\nClick a button to get started",
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
    },
    'zh': {
        'title': 'DirText v3.0',
        'header': '文件目录提取器',
        'subtitle': '快速浏览文件夹内容并导出列表',
        'add': '添加文件夹',
        'clear': '清空选择',
        'export': '导出文本',
        'ready': '就绪',
        'welcome': '欢迎使用文件目录提取器\n\n使用说明：\n  1. 点击「添加文件夹」或拖入文件夹到窗口\n  2. 在"递归【N】层"中设置深度（-1 = 全部，0 = 当前层）\n  3. 预览区显示内容\n  4. 点击「导出文本」保存\n\n点击按钮开始使用吧',
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
    }
}

def t(key, **kw):
    s = T.get(LANG, T['en']).get(key, key)
    return s.format(**kw) if kw else s


# ---------- 样式常量 / Style Constants ----------
BG = "#F5F5F7"
FG = "#1D1D1F"
FG2 = "#86868B"
SURFACE = "#FFFFFF"

BTN_STYLE = f"""
    QPushButton {{
        font-family: 'Microsoft YaHei UI'; font-size: 10pt;
        padding: 6px 20px; background: {SURFACE};
        color: {FG}; border: 1px solid #d1d1d6; border-radius: 4px;
    }}
    QPushButton:hover {{ background: #e8e8ed; }}
    QPushButton:pressed {{ background: #d1d1d6; }}
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

        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

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
        lbl.setStyleSheet(f"color: {FG}; font-size: 9pt; background: transparent;")
        drive_bar.addWidget(lbl)
        self.drive_cb = QComboBox()
        self.drive_cb.setStyleSheet("QComboBox { font-size: 10pt; padding: 2px 4px; }")
        for drive in QDir.drives():
            self.drive_cb.addItem(os.path.normpath(drive.path()))
        self.drive_cb.currentIndexChanged.connect(self._switch_drive)
        drive_bar.addWidget(self.drive_cb, 1)
        layout.addLayout(drive_bar)

    def _setup_path_label(self, layout):
        self.path_label = QLabel()
        self.path_label.setStyleSheet(f"color: {FG2}; font-size: 9pt; background: transparent;")
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
                background: {SURFACE}; color: {FG};
                border: 1px solid #d1d1d6; border-radius: 4px;
                font-size: 10pt;
            }}
            QTreeView::item:selected {{
                background: #007aff; color: white;
            }}
        """)
        layout.addWidget(self.tree, stretch=1)

    def _setup_hint(self, layout):
        hint = QLabel(t('add_hint'))
        hint.setStyleSheet(f"color: {FG2}; font-size: 9pt; background: transparent;")
        layout.addWidget(hint)

    def _setup_dialog_buttons(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        for text, slot in [
            ('OK', self._accept),
            ('Cancel', self.reject),
        ]:
            btn = AnimatedButton(text)
            btn.setStyleSheet(BTN_STYLE)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _navigate_to(self, path):
        """导航到指定目录"""
        path = os.path.normpath(path)
        root_idx = self.model.setRootPath(path)
        # 保证代理模型和树视图同步
        self.tree.setRootIndex(self.proxy.mapFromSource(root_idx))
        # 展开第一级方便浏览
        self.tree.expandAll()
        # 更新路径提示
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
        # 去重
        self.selected_folders = list(dict.fromkeys(paths))
        if self.selected_folders:
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

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._tm = TransitionManager()
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.92)
        self.setGraphicsEffect(self._effect)

    def enterEvent(self, event):
        self._tm.stop_target(self._effect)
        self._tm.animate(
            self._effect, b"opacity", 0.92, 1.0, 180,
            QEasingCurve.Type.OutCubic,
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._tm.stop_target(self._effect)
        self._tm.animate(
            self._effect, b"opacity", 1.0, 0.92, 180,
            QEasingCurve.Type.OutCubic,
        )
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._tm.stop_target(self._effect)
        self._effect.setOpacity(0.72)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._tm.animate(
            self._effect, b"opacity", 0.72, 1.0, 220,
            QEasingCurve.Type.OutCubic,
        )
        super().mouseReleaseEvent(event)


# ---------- 扫描工作线程 / Scan Worker Thread ----------
class ScanWorker(QThread):
    folder_progress = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, int, int)

    def __init__(self, folders, recursion_depth):
        super().__init__()
        self.folders = folders
        self.recursion_depth = recursion_depth
        self._abort = False
        self.structured_data = []  # (folder_root, name, full_path, is_dir, level)

    def abort(self):
        self._abort = True

    def run(self):
        lines = []
        total_dirs = 0
        total_files = 0
        sep = '═' * 80

        self._item_index = 0
        self._last_emit_time = 0
        self._emit_interval = 0.1  # 100ms throttle

        for i, folder in enumerate(self.folders):
            if self._abort:
                lines.append(f"⚠ {t('cancelling')}")
                break
            self.folder_progress.emit(folder)
            lines.append(sep)
            if LANG == 'en':
                lines.append(f"Folder [{i + 1}]: {folder}")
            else:
                lines.append(f"文件夹 [{i + 1}]：{folder}")
            lines.append(sep)
            entry_lines, d, f = self._walk_dir(folder, self.recursion_depth, root=folder)
            lines.extend(entry_lines)
            total_dirs += d
            total_files += f
            lines.append("")

        lines.append(sep)
        if LANG == 'en':
            lines.append(f"Total: {len(self.folders)} folder(s)")
            lines.append(f"         {total_dirs} folders, {total_files} files")
        else:
            lines.append(f"总计：{len(self.folders)} 个文件夹")
            lines.append(f"         共 {total_dirs} 个文件夹，{total_files} 个文件")

        self.finished.emit(lines, total_dirs, total_files)

    def _should_emit_progress(self):
        now = time.perf_counter()
        if now - self._last_emit_time >= self._emit_interval:
            self.progress.emit(self._item_index)
            self._last_emit_time = now

    def _walk_dir(self, folder, max_depth, current_depth=0, prefix="", root=None):
        lines = []
        dir_count = 0
        file_count = 0

        if self._abort:
            return lines, dir_count, file_count

        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name)
        except PermissionError:
            if LANG == 'en':
                lines.append(f"{prefix}└── <Access denied>")
            else:
                lines.append(f"{prefix}└── <无法访问>")
            return lines, 0, 0
        except Exception as e:
            lines.append(f"{prefix}└── <Error: {e}>")
            return lines, 0, 0

        for i, entry in enumerate(entries):
            if self._abort:
                break
            self._item_index += 1
            self._should_emit_progress()

            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                dir_count += 1
                if root is not None:
                    self.structured_data.append((root, entry.name, entry.path, True, current_depth))
                if max_depth == -1 or current_depth < max_depth:
                    sub_lines, sub_dirs, sub_files = self._walk_dir(
                        entry.path, max_depth, current_depth + 1, prefix + child_prefix, root)
                    lines.extend(sub_lines)
                    dir_count += sub_dirs
                    file_count += sub_files
            else:
                lines.append(f"{prefix}{connector}{entry.name}")
                file_count += 1
                if root is not None:
                    self.structured_data.append((root, entry.name, entry.path, False, current_depth))

        return lines, dir_count, file_count


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
        self._text.setStyleSheet(f"color: {FG}; font-size: 10pt; background: transparent;")
        layout.addWidget(self._circle)
        layout.addWidget(self._text)
        layout.addStretch()
        self._update_circle()

    def _update_circle(self):
        if self._selected:
            self._circle.setText('<span style="color: #34c759; font-size: 11pt;">●</span>')
        else:
            self._circle.setText('<span style="color: #c6c6ca; font-size: 11pt;">○</span>')

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
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(8)

        prompt = QLabel(t('format_prompt'))
        prompt.setStyleSheet(f"color: {FG}; font-size: 10pt; background: transparent;")
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
            btn.setStyleSheet(BTN_STYLE)
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


# ---------- 主应用 / Main Application ----------
class DirTextApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folders = []
        self.config_path = "dirtext_config.json"
        self._load_config()
        self._faded_in = False
        self._pending_text = ""
        self._transition = TransitionManager()
        self._worker = None
        self._scanning = False
        self.structured_data = []
        self._depth_timer = QTimer(self)
        self._depth_timer.setSingleShot(True)
        self._depth_timer.setInterval(1000)
        self._depth_timer.timeout.connect(self._apply_depth)
        self._setup_ui()

    # ----- 配置读写 / Config read/write -----
    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.cfg = json.load(f)
        except:
            self.cfg = {"w": 900, "h": 650, "x": None, "y": None}

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
        self._save_config()

    # ----- 窗口事件 / Window Events -----
    def closeEvent(self, event):
        self._transition.stop_all()
        self.setWindowOpacity(1.0)
        self._remember_geometry()
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

    def _setup_window(self):
        self.setWindowTitle(t('title'))
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")
        self.setAcceptDrops(True)

        w, h = self.cfg.get('w', 900), self.cfg.get('h', 650)
        self.resize(w, h)

        central = QWidget()
        central.setStyleSheet(f"background: {BG};")
        self.setCentralWidget(central)

    def _setup_header(self, layout):
        header = QLabel(t('header'))
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {FG}; background: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel(t('subtitle'))
        subtitle.setStyleSheet(f"font-size: 9pt; color: {FG2}; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

    def _setup_preview(self, layout):
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet(f"""
            QPlainTextEdit {{
                font-family: Consolas; font-size: 11pt;
                background: {SURFACE}; color: {FG};
                border: 1px solid #d1d1d6; border-radius: 4px;
                padding: 10px;
            }}
            QScrollBar:vertical {{
                width: 7px;
                background: transparent;
                margin: 2px 2px 2px 0;
            }}
            QScrollBar::handle:vertical {{
                background: #c6c6ca;
                border-radius: 3px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #a8a8ae;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        layout.addWidget(self.preview, stretch=1)

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
                border: none; background: #e0e0e5;
                border-radius: 7px; font-size: 8pt;
                color: {FG}; text-align: center;
            }}
            QProgressBar::chunk {{
                background: #007aff;
                border-radius: 7px;
            }}
        """)
        layout.addWidget(self.progress_bar)

    def _setup_button_bar(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        self.btn_add = AnimatedButton(t('add'))
        self.btn_add.setStyleSheet(BTN_STYLE)
        self.btn_add.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.btn_add)

        self.btn_clipboard = AnimatedButton(t('clipboard_load'))
        self.btn_clipboard.setStyleSheet(BTN_STYLE)
        self.btn_clipboard.clicked.connect(self.load_from_clipboard)
        btn_layout.addWidget(self.btn_clipboard)

        self.btn_clear = AnimatedButton(t('clear'))
        self.btn_clear.setStyleSheet(BTN_STYLE)
        self.btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_export = AnimatedButton(t('export'))
        self.btn_export.setStyleSheet(BTN_STYLE)
        self.btn_export.clicked.connect(self.export)
        btn_layout.addWidget(self.btn_export)

        btn_layout.addStretch()

        # 递归深度输入 / Recursion depth input
        depth_prefix = QLabel(t('recursion_prefix'))
        depth_prefix.setStyleSheet(f"color: {FG2}; font-size: 9pt; background: transparent;")
        btn_layout.addWidget(depth_prefix)

        self.depth_input = QLineEdit()
        self.depth_input.setText('0')
        self.depth_input.setFixedWidth(38)
        self.depth_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.depth_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 9pt; padding: 2px 2px;
                background: {SURFACE}; color: {FG};
                border: 1px solid #d1d1d6; border-radius: 4px;
            }}
            QLineEdit:focus {{ border-color: #007aff; }}
        """)
        self.depth_input.textChanged.connect(self._on_depth_input)
        btn_layout.addWidget(self.depth_input)

        depth_suffix = QLabel(t('recursion_suffix'))
        depth_suffix.setStyleSheet(f"color: {FG2}; font-size: 9pt; background: transparent;")
        btn_layout.addWidget(depth_suffix)

        depth_hint = QLabel(t('recursion_hint'))
        depth_hint.setStyleSheet(f"color: {FG2}; font-size: 8pt; background: transparent;")
        btn_layout.addWidget(depth_hint)

        layout.addLayout(btn_layout)

        self.status = self.statusBar()
        self.status.setStyleSheet(f"color: {FG2}; font-size: 9pt;")
        self.status.showMessage(t('ready'))
        self.recursion_depth = 0

    # ----- 预览文本过渡 / Preview Text Transition -----
    def _set_preview_text(self, text):
        """预览文本淡入淡出：淡出 → 换文本 → 淡入"""
        self._transition.stop_target(self._preview_effect)
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
        self.progress_bar.setFormat(f'{count} items')

    def _on_scan_finished(self, lines, total_dirs, total_files):
        if not self._scanning:
            return
        self.structured_data = self._worker.structured_data if self._worker else []
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
        self._worker = ScanWorker(self.folders, self.recursion_depth)
        self._worker.folder_progress.connect(self._on_folder_progress)
        self._worker.progress.connect(self._on_item_progress)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def export(self):
        content = self.preview.toPlainText().strip()
        if not content or content.startswith(t('welcome')[:20]):
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
            self._export_txt(content, timestamp)

    def _export_txt(self, content, timestamp):
        fname, _ = QFileDialog.getSaveFileName(
            self, t('save_title'),
            t('file_name', ts=timestamp),
            'Text files (*.txt);;All files (*.*)',
        )
        if not fname:
            return
        try:
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(content + f"\n\nGenerated: {datetime.now():%Y-%m-%d %H:%M:%S}")
            QMessageBox.information(self, 'Success', t('success', path=fname))
            self.status.showMessage(os.path.basename(fname))
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('fail', error=str(e)))

    def _export_csv(self, timestamp):
        fname, _ = QFileDialog.getSaveFileName(
            self, t('csv_save_title'),
            t('csv_file_name', ts=timestamp),
            'CSV files (*.csv);;All files (*.*)',
        )
        if not fname:
            return
        try:
            with open(fname, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    t('csv_col_folder'), t('csv_col_name'), t('csv_col_path'),
                    t('csv_col_type'), t('csv_col_level'),
                ])
                for root, name, path, is_dir, level in self.structured_data:
                    writer.writerow([
                        root, name, path,
                        t('csv_type_dir') if is_dir else t('csv_type_file'),
                        level,
                    ])
            QMessageBox.information(self, 'Success', t('success', path=fname))
            self.status.showMessage(os.path.basename(fname))
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('fail', error=str(e)))

    def _export_json(self, timestamp):
        fname, _ = QFileDialog.getSaveFileName(
            self, t('json_save_title'),
            t('json_file_name', ts=timestamp),
            'JSON files (*.json);;All files (*.*)',
        )
        if not fname:
            return
        try:
            data = []
            for root, name, path, is_dir, level in self.structured_data:
                data.append({
                    t('csv_col_folder'): root,
                    t('csv_col_name'): name,
                    t('csv_col_path'): path,
                    t('csv_col_type'): t('csv_type_dir') if is_dir else t('csv_type_file'),
                    t('csv_col_level'): level,
                })
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, 'Success', t('success', path=fname))
            self.status.showMessage(os.path.basename(fname))
        except Exception as e:
            QMessageBox.critical(self, 'Error', t('fail', error=str(e)))


# ---------- 入口 / Entry Point ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DirTextApp()
    window.show()
    sys.exit(app.exec())
