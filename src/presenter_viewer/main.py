from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from presenter_viewer.ui.presenter_window import PresenterWindow
from presenter_viewer.ui.projector_window import ProjectorWindow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Presenter Viewer")
    parser.add_argument(
        "pdf",
        nargs="?",
        help="Ruta del PDF a abrir",
    )
    return parser.parse_args()


def resolve_initial_pdf(pdf_arg: str | None) -> Path | None:
    if pdf_arg:
        pdf_path = Path(pdf_arg).expanduser().resolve()
        if pdf_path.exists() and pdf_path.is_file():
            return pdf_path
        print(f"[WARN] No existe el archivo PDF: {pdf_path}")
        return None

    demo_path = Path("demo.pdf").resolve()
    if demo_path.exists() and demo_path.is_file():
        return demo_path

    return None


def main() -> None:
    args = parse_args()

    app = QApplication(sys.argv)

    presenter = PresenterWindow()
    projector = ProjectorWindow()
    presenter.set_projector_window(projector)

    # Tamaño inicial "pro": 80% de la pantalla principal y centrado
    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        w = int(geometry.width() * 0.95)
        h = int(geometry.height() * 0.95)

        presenter.resize(w, h)
        presenter.move(
            geometry.x() + (geometry.width() - w) // 2,
            geometry.y() + (geometry.height() - h) // 2,
        )
    else:
        presenter.resize(1400, 900)

    presenter.show()
    presenter.refresh_screens(initial=True)

    pdf_path = resolve_initial_pdf(args.pdf)
    if pdf_path is not None:
        presenter.load_pdf(pdf_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()