import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from presenter_viewer.ui.presenter_window import PresenterWindow
from presenter_viewer.ui.projector_window import ProjectorWindow


def run() -> None:
    app = QApplication(sys.argv)

    presenter = PresenterWindow()
    projector = ProjectorWindow()

    presenter.set_projector_window(projector)
    presenter.refresh_screens(initial=True)

    # Re-detectar pantallas dinámicamente
    qapp = QGuiApplication.instance()
    if qapp is not None:
        qapp.screenAdded.connect(lambda screen: presenter.refresh_screens())
        qapp.screenRemoved.connect(lambda screen: presenter.refresh_screens())

    presenter.resize(1400, 900)
    presenter.show()

    sample_pdf = Path("samples/demo.pdf")
    if sample_pdf.exists():
        presenter.load_pdf(sample_pdf)

    sys.exit(app.exec())