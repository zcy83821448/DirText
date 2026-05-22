from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QPushButton, QGraphicsOpacityEffect


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
