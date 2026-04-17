from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import fitz  # PyMuPDF
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap


RegionName = Literal["full", "slide", "notes"]


@dataclass
class RenderedPage:
    page_index: int
    width: int
    height: int
    pixmap: QPixmap


class PdfLoader:
    def __init__(self) -> None:
        self._doc: fitz.Document | None = None
        self._path: Path | None = None
        self._annot_extractor = None

        # Si el PDF exportó presenter notes en doble panel
        self.has_presenter_notes_layout: bool = False

        # Si sí hay notes layout, dónde están las notas
        self.notes_side: Literal["right", "left"] = "left"

    @property
    def is_loaded(self) -> bool:
        return self._doc is not None

    @property
    def page_count(self) -> int:
        return len(self._doc) if self._doc is not None else 0

    @property
    def path(self) -> Path | None:
        return self._path

    def load(self, pdf_path: Path) -> None:
        if not pdf_path.exists():
            raise FileNotFoundError(f"No existe el archivo: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError("El archivo debe ser un PDF")

        self.close()
        self._doc = fitz.open(pdf_path)
        self._path = pdf_path

        from presenter_viewer.pdf.annotation_extractor import AnnotationExtractor
        self._annot_extractor = AnnotationExtractor(self._doc)

        self.has_presenter_notes_layout = self._detect_presenter_notes_layout()

        print(
            f"PDF cargado correctamente | notes_layout={self.has_presenter_notes_layout} | notes_side={self.notes_side}",
            flush=True,
        )

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
        self._doc = None
        self._path = None
        self._annot_extractor = None
        self.has_presenter_notes_layout = False

    def get_pnotes(self, page_index: int) -> list[str]:
        if self._annot_extractor is None:
            return []
        return self._annot_extractor.get_pnotes_for_page(page_index)

    def render_page_region(
        self,
        page_index: int,
        region: RegionName = "full",
        target_width: int | None = None,
        target_height: int | None = None,
        device_pixel_ratio: float = 1.0,
    ) -> RenderedPage:
        if self._doc is None:
            raise RuntimeError("No hay PDF cargado")

        if page_index < 0 or page_index >= len(self._doc):
            raise IndexError(f"Índice de página fuera de rango: {page_index}")

        page = self._doc[page_index]
        rect = page.rect

        # Si el PDF NO tiene layout de notes:
        # - full = página completa
        # - slide = página completa
        # - notes = vacío
        if not self.has_presenter_notes_layout and region == "notes":
            empty = self._build_empty_pixmap(
                target_width=target_width,
                target_height=target_height,
                device_pixel_ratio=device_pixel_ratio,
            )
            return RenderedPage(
                page_index=page_index,
                width=empty.width(),
                height=empty.height(),
                pixmap=empty,
            )

        clip = self._region_clip(rect, region)

        clip_width = clip.width
        clip_height = clip.height

        if target_width and target_height and clip_width > 0 and clip_height > 0:
            scale_x = target_width / clip_width
            scale_y = target_height / clip_height
            scale = min(scale_x, scale_y)
            zoom_x = scale * device_pixel_ratio
            zoom_y = scale * device_pixel_ratio
        else:
            zoom_x = 2.0 * device_pixel_ratio
            zoom_y = 2.0 * device_pixel_ratio

        matrix = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=matrix, alpha=False, clip=clip)

        image_format = QImage.Format.Format_RGB888
        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            image_format,
        ).copy()

        qt_pixmap = QPixmap.fromImage(image)
        qt_pixmap.setDevicePixelRatio(device_pixel_ratio)

        return RenderedPage(
            page_index=page_index,
            width=pix.width,
            height=pix.height,
            pixmap=qt_pixmap,
        )

    def _detect_presenter_notes_layout(self) -> bool:
        if self._doc is None or len(self._doc) == 0:
            return False

        # Heurística:
        # Si la mayoría de páginas son claramente "doble panel" horizontal,
        # asumimos que es export de presenter notes.
        checked = min(len(self._doc), 5)
        wide_pages = 0

        for i in range(checked):
            page = self._doc[i]
            rect = page.rect
            if rect.height <= 0:
                continue

            aspect = rect.width / rect.height

            # PDFs normales 16:9 suelen andar aprox. 1.78
            # pero aquí lo que importa es que exportaste notes "en hoja alargada horizontal"
            # con slide + notes lado a lado.
            #
            # Si tus PDFs normales también son widescreen, necesitamos distinguir:
            # una página normal NO debe cortarse; una con notes suele ser todavía más ancha
            # o al menos estar pensada para dos regiones funcionales.
            #
            # Umbral conservador:
            if aspect >= 2.2:
                wide_pages += 1

        return wide_pages >= max(1, checked // 2)

    def _build_empty_pixmap(
        self,
        target_width: int | None,
        target_height: int | None,
        device_pixel_ratio: float,
    ) -> QPixmap:
        logical_w = max(200, target_width or 800)
        logical_h = max(120, target_height or 450)

        real_w = max(1, int(logical_w * device_pixel_ratio))
        real_h = max(1, int(logical_h * device_pixel_ratio))

        pixmap = QPixmap(real_w, real_h)
        pixmap.fill(QColor("#1b1b1b"))
        pixmap.setDevicePixelRatio(device_pixel_ratio)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setPen(QColor("#6b7280"))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Sin notas",
        )
        painter.end()

        return pixmap

    def _region_clip(self, rect: fitz.Rect, region: RegionName) -> fitz.Rect:
        if region == "full":
            return rect

        # Si no hay presenter notes layout:
        # slide = página completa
        # notes se maneja antes en render_page_region()
        if not self.has_presenter_notes_layout:
            return rect

        mid_x = rect.x0 + rect.width / 2.0

        left_rect = fitz.Rect(rect.x0, rect.y0, mid_x, rect.y1)
        right_rect = fitz.Rect(mid_x, rect.y0, rect.x1, rect.y1)

        if self.notes_side == "right":
            slide_rect = left_rect
            notes_rect = right_rect
        else:
            notes_rect = left_rect
            slide_rect = right_rect

        if region == "slide":
            return slide_rect

        if region == "notes":
            return notes_rect

        return rect