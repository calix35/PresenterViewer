from __future__ import annotations

from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QWidget, QVBoxLayout

from presenter_viewer.pdf.pdf_loader import PdfLoader
from presenter_viewer.ui.widgets.slide_view import SlideView


class ProjectorWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Projector")
        self.pdf_loader: PdfLoader | None = None
        self.current_page_index = 0
        self.is_black = False
        self.current_drawings: list[dict] = []
        self.drawings_visible: bool = True

        self.pointer_enabled = False
        self.pointer_pos_norm: tuple[float, float] | None = None
        self.pointer_radius_px: float = 8.0

        self.spotlight_enabled = False
        self.spotlight_pos_norm: tuple[float, float] | None = None
        self.spotlight_radius_px: float = 80.0

        self.zoom_viewport_norm: tuple[float, float, float, float] | None = None

        self.slide_view = SlideView()
        self.slide_view.set_fit_mode("contain")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.slide_view)

        # Cache del último render base del PDF
        self._last_render_key: tuple | None = None

    def set_pdf_loader(self, pdf_loader: PdfLoader) -> None:
        self.pdf_loader = pdf_loader
        self._invalidate_render_cache()

    def move_to_screen(self, screen: QScreen) -> None:
        geometry = screen.geometry()
        self.setGeometry(geometry)

    def show_projector(self, fullscreen: bool = True) -> None:
        if fullscreen:
            self.showFullScreen()
        else:
            self.show()

    def display_page(
        self,
        page_index: int,
        black: bool = False,
        drawings: list[dict] | None = None,
        drawings_visible: bool = True,
        pointer_enabled: bool = False,
        pointer_pos_norm: tuple[float, float] | None = None,
        pointer_radius_px: float = 8.0,
        spotlight_enabled: bool = False,
        spotlight_pos_norm: tuple[float, float] | None = None,
        spotlight_radius_px: float = 80.0,
        zoom_viewport_norm: tuple[float, float, float, float] | None = None,
    ) -> None:
        old_page = self.current_page_index
        old_black = self.is_black
        old_zoom = self.zoom_viewport_norm

        self.current_page_index = page_index
        self.is_black = black
        self.current_drawings = drawings or []
        self.drawings_visible = drawings_visible

        self.pointer_enabled = pointer_enabled
        self.pointer_pos_norm = pointer_pos_norm
        self.pointer_radius_px = pointer_radius_px

        self.spotlight_enabled = spotlight_enabled
        self.spotlight_pos_norm = spotlight_pos_norm
        self.spotlight_radius_px = spotlight_radius_px

        self.zoom_viewport_norm = zoom_viewport_norm

        # Re-render base solo si realmente cambió algo estructural
        if (
            old_page != self.current_page_index
            or old_black != self.is_black
            or old_zoom != self.zoom_viewport_norm
        ):
            self._render_base(force=False)

        self._apply_overlay_state()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render_base(force=False)
        self._apply_overlay_state()

    def _invalidate_render_cache(self) -> None:
        self._last_render_key = None

    def _normalized_zoom_key(self) -> tuple | None:
        if self.zoom_viewport_norm is None:
            return None
        x, y, w, h = self.zoom_viewport_norm
        return (round(x, 4), round(y, 4), round(w, 4), round(h, 4))

    def _compute_render_key(self) -> tuple:
        w = max(self.slide_view.width(), 100)
        h = max(self.slide_view.height(), 100)

        screen = self.windowHandle().screen() if self.windowHandle() else None
        dpr = screen.devicePixelRatio() if screen else 1.0

        return (
            id(self.pdf_loader),
            self.current_page_index,
            self.is_black,
            self._normalized_zoom_key(),
            w,
            h,
            round(float(dpr), 3),
        )

    def _render_base(self, force: bool = False) -> None:
        render_key = self._compute_render_key()

        if not force and render_key == self._last_render_key:
            return

        self._last_render_key = render_key

        if self.is_black:
            self.slide_view.clear_slide()
            self.slide_view.setStyleSheet("background-color: black;")
            return

        self.slide_view.setStyleSheet("")

        if self.pdf_loader is None or not self.pdf_loader.is_loaded:
            self.slide_view.clear_slide()
            return

        w = max(self.slide_view.width(), 100)
        h = max(self.slide_view.height(), 100)

        scale_factor = 1.0
        if self.zoom_viewport_norm is not None:
            _, _, vw, vh = self.zoom_viewport_norm
            if vw > 0.0 and vh > 0.0:
                scale_factor = min(3.0, max(1.0 / vw, 1.0 / vh))

        render_w = int(w * scale_factor)
        render_h = int(h * scale_factor)

        screen = self.windowHandle().screen() if self.windowHandle() else None
        dpr = screen.devicePixelRatio() if screen else 1.0

        rendered = self.pdf_loader.render_page_region(
            page_index=self.current_page_index,
            region="slide",
            target_width=max(render_w, 100),
            target_height=max(render_h, 100),
            device_pixel_ratio=dpr,
        )
        self.slide_view.set_slide_pixmap(rendered.pixmap)

    def _apply_overlay_state(self) -> None:
        if self.is_black:
            self.slide_view.set_drawings([], visible=False)
            self.slide_view.clear_overlays()
            self.slide_view.set_viewport_norm(None)
            self.slide_view.set_status_indicators([])
            self.slide_view.set_tool_preview(False)
            self.slide_view.update()
            return

        if self.pdf_loader is None or not self.pdf_loader.is_loaded:
            self.slide_view.set_drawings([], visible=False)
            self.slide_view.clear_overlays()
            self.slide_view.set_viewport_norm(None)
            self.slide_view.set_status_indicators([])
            self.slide_view.set_tool_preview(False)
            self.slide_view.update()
            return

        self.slide_view.set_viewport_norm(self.zoom_viewport_norm)
        self.slide_view.set_drawings(self.current_drawings, visible=self.drawings_visible)
        self.slide_view.set_status_indicators([])
        self.slide_view.set_tool_preview(False)

        self.slide_view.set_pointer_overlay(
            enabled=self.pointer_enabled,
            pos_norm=self.pointer_pos_norm,
            radius_px=self.pointer_radius_px,
            color="#ff3b30",
        )
        self.slide_view.set_spotlight_overlay(
            enabled=self.spotlight_enabled,
            pos_norm=self.spotlight_pos_norm,
            radius_px=self.spotlight_radius_px,
        )

        self.slide_view.update()