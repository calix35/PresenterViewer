from __future__ import annotations

from typing import Callable, Literal

from PySide6.QtCore import QPointF, Qt, QRect, QRectF
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


FitMode = Literal["contain", "cover"]
MouseCallback = Callable[[float, float], None]
VoidCallback = Callable[[], None]


class SlideView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._pixmap: QPixmap | None = None
        self._fit_mode: FitMode = "contain"
        self._background_color: str = "#1b1b1b"
        self._status_indicators: list[tuple[str, str]] = []

        self._drawings_visible: bool = True
        self._drawings: list[dict] = []

        self._interaction_enabled: bool = False
        self._mouse_press_callback: MouseCallback | None = None
        self._mouse_move_callback: MouseCallback | None = None
        self._mouse_release_callback: MouseCallback | None = None
        self._mouse_hover_callback: MouseCallback | None = None
        self._right_click_callback: VoidCallback | None = None

        self._last_target_rect: QRectF | None = None

        # viewport normalizado sobre la slide completa
        self._viewport_norm: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)

        # Preview visual de herramienta
        self._tool_preview_enabled: bool = False
        self._tool_preview_color: str = "#ff0000"
        self._tool_preview_radius_px: float = 6.0
        self._tool_preview_pos_norm: tuple[float, float] | None = None

        # Pointer
        self._pointer_enabled: bool = False
        self._pointer_color: str = "#ff3b30"
        self._pointer_radius_px: float = 8.0
        self._pointer_pos_norm: tuple[float, float] | None = None

        # Spotlight
        self._spotlight_enabled: bool = False
        self._spotlight_radius_px: float = 80.0
        self._spotlight_pos_norm: tuple[float, float] | None = None

        # Selección rectangular
        self._selection_enabled: bool = False
        self._selection_rect_norm: tuple[float, float, float, float] | None = None

        self.setMouseTracking(True)

    def set_slide_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def clear_slide(self) -> None:
        self._pixmap = None
        self.update()

    def set_fit_mode(self, mode: FitMode) -> None:
        self._fit_mode = mode
        self.update()

    def set_background_color(self, color: str) -> None:
        self._background_color = color
        self.update()

    def set_status_indicators(self, indicators: list[tuple[str, str]]) -> None:
        self._status_indicators = indicators
        self.update()

    def set_drawings(self, drawings: list[dict], visible: bool = True) -> None:
        self._drawings = drawings
        self._drawings_visible = visible
        self.update()

    def enable_interaction(self, enabled: bool) -> None:
        self._interaction_enabled = enabled

    def set_mouse_callbacks(
        self,
        on_press: MouseCallback | None = None,
        on_move: MouseCallback | None = None,
        on_release: MouseCallback | None = None,
        on_hover: MouseCallback | None = None,
        on_right_click: VoidCallback | None = None,
    ) -> None:
        self._mouse_press_callback = on_press
        self._mouse_move_callback = on_move
        self._mouse_release_callback = on_release
        self._mouse_hover_callback = on_hover
        self._right_click_callback = on_right_click

    def get_content_rect(self) -> QRectF:
        if self._last_target_rect is None:
            return QRectF(0, 0, self.width(), self.height())
        return self._last_target_rect

    def set_viewport_norm(self, viewport: tuple[float, float, float, float] | None) -> None:
        if viewport is None:
            self._viewport_norm = (0.0, 0.0, 1.0, 1.0)
        else:
            x, y, w, h = viewport
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))
            w = max(1e-6, min(1.0, w))
            h = max(1e-6, min(1.0, h))
            if x + w > 1.0:
                x = 1.0 - w
            if y + h > 1.0:
                y = 1.0 - h
            self._viewport_norm = (x, y, w, h)
        self.update()

    def set_tool_preview(
        self,
        enabled: bool,
        color: str = "#ff0000",
        radius_px: float = 6.0,
        pos_norm: tuple[float, float] | None = None,
    ) -> None:
        self._tool_preview_enabled = enabled
        self._tool_preview_color = color
        self._tool_preview_radius_px = radius_px
        self._tool_preview_pos_norm = pos_norm if enabled else None
        self.update()

    def clear_tool_preview(self) -> None:
        self._tool_preview_pos_norm = None
        self.update()

    def set_pointer_overlay(
        self,
        enabled: bool,
        pos_norm: tuple[float, float] | None = None,
        radius_px: float = 8.0,
        color: str = "#ff3b30",
    ) -> None:
        self._pointer_enabled = enabled
        self._pointer_pos_norm = pos_norm
        self._pointer_radius_px = radius_px
        self._pointer_color = color
        self.update()

    def set_spotlight_overlay(
        self,
        enabled: bool,
        pos_norm: tuple[float, float] | None = None,
        radius_px: float = 80.0,
    ) -> None:
        self._spotlight_enabled = enabled
        self._spotlight_pos_norm = pos_norm
        self._spotlight_radius_px = radius_px
        self.update()

    def set_selection_overlay(
        self,
        enabled: bool,
        rect_norm: tuple[float, float, float, float] | None = None,
    ) -> None:
        self._selection_enabled = enabled
        self._selection_rect_norm = rect_norm if enabled else None
        self.update()

    def clear_selection_overlay(self) -> None:
        self._selection_enabled = False
        self._selection_rect_norm = None
        self.update()

    def clear_overlays(self) -> None:
        self._pointer_enabled = False
        self._pointer_pos_norm = None
        self._spotlight_enabled = False
        self._spotlight_pos_norm = None
        self._selection_enabled = False
        self._selection_rect_norm = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)

        self._last_target_rect = None

        if self._pixmap:
            img_w = self._pixmap.width() / max(self._pixmap.devicePixelRatio(), 1.0)
            img_h = self._pixmap.height() / max(self._pixmap.devicePixelRatio(), 1.0)

            if img_w > 0 and img_h > 0:
                widget_w = self.width()
                widget_h = self.height()

                scale_x = widget_w / img_w
                scale_y = widget_h / img_h

                if self._fit_mode == "cover":
                    scale = max(scale_x, scale_y)
                else:
                    scale = min(scale_x, scale_y)

                draw_w = int(img_w * scale)
                draw_h = int(img_h * scale)

                x = (widget_w - draw_w) // 2
                y = (widget_h - draw_h) // 2

                target_rect = QRect(x, y, draw_w, draw_h)
                target_rectf = QRectF(target_rect)
                self._last_target_rect = target_rectf

                vx, vy, vw, vh = self._viewport_norm
                source_rect = QRectF(
                    vx * self._pixmap.width(),
                    vy * self._pixmap.height(),
                    vw * self._pixmap.width(),
                    vh * self._pixmap.height(),
                )

                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                painter.drawPixmap(target_rectf, self._pixmap, source_rect)

                self._draw_drawings(painter, target_rectf)
                self._draw_spotlight_overlay(painter, target_rectf)
                self._draw_pointer_overlay(painter, target_rectf)
                self._draw_selection_overlay(painter, target_rectf)

        self._draw_tool_preview(painter)
        self._draw_status_indicators(painter)

    def _norm_to_target(self, target_rect: QRectF, nx: float, ny: float) -> QPointF | None:
        vx, vy, vw, vh = self._viewport_norm
        if vw <= 0.0 or vh <= 0.0:
            return None

        rx = (nx - vx) / vw
        ry = (ny - vy) / vh

        if rx < 0.0 or rx > 1.0 or ry < 0.0 or ry > 1.0:
            return None

        return QPointF(
            target_rect.x() + rx * target_rect.width(),
            target_rect.y() + ry * target_rect.height(),
        )

    def _draw_drawings(self, painter: QPainter, target_rect: QRectF) -> None:
        if not self._drawings_visible or not self._drawings:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for stroke in self._drawings:
            points = stroke.get("points", [])
            if len(points) < 2:
                continue

            color = QColor(stroke.get("color", "#ff3b30"))
            size = float(stroke.get("size", 6.0))
            pen = QPen(color)
            pen.setWidthF(size)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            qpoints: list[QPointF] = []
            for px, py in points:
                mapped = self._norm_to_target(target_rect, float(px), float(py))
                if mapped is not None:
                    qpoints.append(mapped)

            if len(qpoints) < 2:
                continue

            for i in range(len(qpoints) - 1):
                painter.drawLine(qpoints[i], qpoints[i + 1])

        painter.restore()

    def _draw_pointer_overlay(self, painter: QPainter, target_rect: QRectF) -> None:
        if not self._pointer_enabled or self._pointer_pos_norm is None:
            return

        mapped = self._norm_to_target(target_rect, self._pointer_pos_norm[0], self._pointer_pos_norm[1])
        if mapped is None:
            return

        cx = mapped.x()
        cy = mapped.y()

        core_r = max(2.0, self._pointer_radius_px * 0.28)
        glow_r = max(core_r + 3.0, self._pointer_radius_px)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 0, 0, 55))
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        painter.setBrush(QColor(255, 0, 0, 110))
        painter.drawEllipse(QPointF(cx, cy), glow_r * 0.55, glow_r * 0.55)

        painter.setBrush(QColor(255, 30, 30, 230))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawEllipse(QPointF(cx, cy), max(0.8, core_r * 0.35), max(0.8, core_r * 0.35))

        painter.restore()

    def _draw_spotlight_overlay(self, painter: QPainter, target_rect: QRectF) -> None:
        if not self._spotlight_enabled or self._spotlight_pos_norm is None:
            return

        mapped = self._norm_to_target(target_rect, self._spotlight_pos_norm[0], self._spotlight_pos_norm[1])
        if mapped is None:
            return

        cx = mapped.x()
        cy = mapped.y()
        r = max(10.0, self._spotlight_radius_px)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        from PySide6.QtGui import QPainterPath

        overlay = QPainterPath()
        overlay.addRect(target_rect)

        hole = QPainterPath()
        hole.addEllipse(QPointF(cx, cy), r, r)

        final_path = overlay.subtracted(hole)

        painter.fillPath(final_path, QColor(0, 0, 0, 170))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        painter.restore()

    def _draw_selection_overlay(self, painter: QPainter, target_rect: QRectF) -> None:
        if not self._selection_enabled or self._selection_rect_norm is None:
            return

        x, y, w, h = self._selection_rect_norm
        p1 = self._norm_to_target(target_rect, x, y)
        p2 = self._norm_to_target(target_rect, x + w, y + h)
        if p1 is None or p2 is None:
            return

        rect = QRectF(p1, p2).normalized()

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        from PySide6.QtGui import QPainterPath

        outside = QPainterPath()
        outside.addRect(target_rect)

        hole = QPainterPath()
        hole.addRect(rect)

        shaded = outside.subtracted(hole)
        painter.fillPath(shaded, QColor(0, 0, 0, 90))

        painter.setBrush(QColor(0, 229, 255, 18))
        painter.setPen(QPen(QColor("#00e5ff"), 2, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

        painter.restore()

    def _draw_tool_preview(self, painter: QPainter) -> None:
        if not self._tool_preview_enabled or self._tool_preview_pos_norm is None:
            return

        rect = self.get_content_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        mapped = self._norm_to_target(rect, self._tool_preview_pos_norm[0], self._tool_preview_pos_norm[1])
        if mapped is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        r = max(2.0, self._tool_preview_radius_px)
        x = mapped.x()
        y = mapped.y()

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(self._tool_preview_color), 2))
        painter.drawEllipse(QPointF(x, y), r, r)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._tool_preview_color))
        painter.drawEllipse(QPointF(x, y), 2.0, 2.0)

        painter.restore()

    def _draw_status_indicators(self, painter: QPainter) -> None:
        if not self._status_indicators:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)

        metrics = painter.fontMetrics()

        margin = 12
        row_gap = 8
        circle_d = 12
        padding_x = 12
        padding_y = 8
        text_gap = 8

        row_rects: list[tuple[QRectF, str, str]] = []
        max_width = 0.0

        for label, color in self._status_indicators:
            text_w = metrics.horizontalAdvance(label)
            text_h = metrics.height()

            row_h = max(circle_d, text_h)
            row_w = circle_d + text_gap + text_w

            rect_w = row_w + 2 * padding_x
            rect_h = row_h + 2 * padding_y

            row_rects.append((QRectF(0, 0, rect_w, rect_h), label, color))
            max_width = max(max_width, rect_w)

        panel_x = self.width() - max_width - margin
        panel_y = margin
        current_y = panel_y

        for rect, label, color in row_rects:
            rect = QRectF(panel_x, current_y, rect.width(), rect.height())

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 175))
            painter.drawRoundedRect(rect, 10, 10)

            circle_x = rect.x() + padding_x
            circle_y = rect.y() + (rect.height() - circle_d) / 2

            painter.setBrush(QColor(color))
            painter.drawEllipse(QRectF(circle_x, circle_y, circle_d, circle_d))

            text_x = circle_x + circle_d + text_gap
            text_y = rect.y()
            text_w = rect.width() - (text_x - rect.x()) - padding_x
            text_h = rect.height()

            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                QRectF(text_x, text_y, text_w, text_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label,
            )

            current_y += rect.height() + row_gap

        painter.restore()

    def _map_widget_pos_to_normalized(self, pos: QPointF) -> tuple[float, float] | None:
        rect = self.get_content_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return None

        if not rect.contains(pos):
            return None

        rx = (pos.x() - rect.x()) / rect.width()
        ry = (pos.y() - rect.y()) / rect.height()

        vx, vy, vw, vh = self._viewport_norm
        nx = vx + rx * vw
        ny = vy + ry * vh

        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        return nx, ny

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)

        if not self._interaction_enabled:
            return

        if event.button() == Qt.MouseButton.RightButton:
            if self._right_click_callback is not None:
                self._right_click_callback()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        mapped = self._map_widget_pos_to_normalized(event.position())
        if mapped is None:
            return

        if self._mouse_press_callback is not None:
            self._mouse_press_callback(mapped[0], mapped[1])

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        mapped = self._map_widget_pos_to_normalized(event.position())
        if mapped is not None and self._mouse_hover_callback is not None:
            self._mouse_hover_callback(mapped[0], mapped[1])

        if self._interaction_enabled and (event.buttons() & Qt.MouseButton.LeftButton):
            if mapped is not None and self._mouse_move_callback is not None:
                self._mouse_move_callback(mapped[0], mapped[1])

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if not self._interaction_enabled:
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        mapped = self._map_widget_pos_to_normalized(event.position())
        if mapped is None:
            return

        if self._mouse_release_callback is not None:
            self._mouse_release_callback(mapped[0], mapped[1])

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)