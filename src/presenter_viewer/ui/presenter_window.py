from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCursor, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from presenter_viewer.config import (
    PANEL_KEYS,
    LayoutConfig,
    load_layout_config,
    save_layout_config,
)
from presenter_viewer.pdf.pdf_loader import PdfLoader
from presenter_viewer.ui.projector_window import ProjectorWindow
from presenter_viewer.ui.widgets.slide_view import SlideView


class PresenterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Presenter Viewer")

        self.pdf_loader = PdfLoader()

        self.current_page_index = 0
        self.projector_page_index = 0

        self.layout_config: LayoutConfig = load_layout_config()
        self.customize_mode = False
        self._applying_layout = False
        self._updating_duplicates_checkbox = False

        self.is_black = False
        self.is_frozen = False
        self.show_pnote = True
        self.is_fullscreen = False

        self.show_help_bar = False
        self.show_panel_role_labels = True

        self.projector_window: ProjectorWindow | None = None

        self.available_screens = []
        self.projector_screen_index: int | None = None

        # Panel seleccionado (para shortcuts)
        self.selected_panel_key: str | None = None

        # Herramientas / modos
        self.tool_mode = "normal"   # normal | pen | eraser | pointer | spotlight
        self.pen_size = 8
        self.eraser_size = 8
        self.pointer_size = 10
        self.spotlight_size = 80

        self.drawings_visible = True
        self.page_drawings: dict[int, list[dict]] = {}
        self.current_stroke: dict | None = None

        # Historial por página
        self.page_undo: dict[int, list[list[dict]]] = {}
        self.page_redo: dict[int, list[list[dict]]] = {}
        self._operation_snapshot_taken = False

        # Posición actual del puntero en coords normalizadas de la slide actual
        self.overlay_pointer_pos_norm: tuple[float, float] | None = None

        # Selección rectangular
        self.selection_start_norm: tuple[float, float] | None = None
        self.selection_end_norm: tuple[float, float] | None = None
        self.selection_rect_norm: tuple[float, float, float, float] | None = None
        self.is_selecting: bool = False

        # Zoom
        self.control_zoom_viewport_norm: tuple[float, float, float, float] | None = None
        self.projector_zoom_viewport_norm: tuple[float, float, float, float] | None = None

        # Cronómetro
        self.presentation_elapsed_seconds = 0
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._on_clock_tick)

        # Throttle para actualizaciones del proyector
        self.projector_update_timer = QTimer(self)
        self.projector_update_timer.setSingleShot(True)
        self.projector_update_timer.timeout.connect(self._update_projector)

        # Widgets de paneles
        self.current_slide_view = SlideView()   # panel main_left
        self.next_slide_view = SlideView()      # panel right_top
        self.current_note_view = SlideView()    # panel right_middle
        self.next_note_view = SlideView()       # panel right_bottom

        self.current_slide_view.set_fit_mode("contain")
        self.next_slide_view.set_fit_mode("contain")
        self.current_note_view.set_fit_mode("contain")
        self.next_note_view.set_fit_mode("contain")

        self.pnote_bar = QLabel("pnote: sin contenido")
        self.pnote_bar.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.pnote_bar.setStyleSheet(
            "background-color: #2b2b2b; color: white; padding: 8px;"
        )

        self.mode_bar = QLabel("Modo normal")
        self.mode_bar.setStyleSheet(
            "background-color: #1f1f1f; color: #d0d0d0; padding: 4px;"
        )

        self.screen_status_label = QLabel("Pantallas: 0 | Proyector: no asignado")
        self.screen_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.screen_status_label.setStyleSheet(
            "color: #9ecbff; padding: 0px;"
        )

        self.screen_timer_label = QLabel("Tiempo: 00:00:00")
        self.screen_timer_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.screen_timer_label.setStyleSheet(
            "color: #f5f5f5; padding: 0px; font-weight: bold;"
        )

        self.screen_bar = QWidget()
        self.screen_bar.setStyleSheet(
            "background-color: #101010; padding: 4px;"
        )
        screen_bar_layout = QHBoxLayout(self.screen_bar)
        screen_bar_layout.setContentsMargins(8, 4, 8, 4)
        screen_bar_layout.setSpacing(12)
        screen_bar_layout.addWidget(self.screen_status_label, stretch=1)
        screen_bar_layout.addWidget(self.screen_timer_label, stretch=0)

        self.help_bar = QLabel(self._build_help_text())
        self.help_bar.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.help_bar.setWordWrap(True)
        self.help_bar.setStyleSheet(
            "background-color: #151515; color: #cfcfcf; padding: 6px;"
        )

        self.allow_duplicates_checkbox = QCheckBox("Permitir duplicados")
        self.allow_duplicates_checkbox.setChecked(self.layout_config.allow_duplicate_roles)
        self.allow_duplicates_checkbox.toggled.connect(self._on_allow_duplicates_toggled)

        self.main_splitter: QSplitter | None = None
        self.right_splitter: QSplitter | None = None
        self.outer_splitter: QSplitter | None = None

        self._build_ui()
        self._configure_active_slide_view()
        self._build_toolbar()
        self._build_shortcuts()
        self._update_current_tool_cursor()
        self._update_tool_preview()

        self._update_help_bar_visibility()
        self._update_timer_label()
        self.clock_timer.start(1000)

        QTimer.singleShot(0, self._apply_layout_to_splitters)

    def _build_help_text(self) -> str:
        return (
            "Atajos: ←/→ o Espacio navegar | 1 normal | 2 pointer | 3 pen | 4 eraser | 5 spotlight | "
            "+/- tamaño | Z zoom | Esc salir zoom | X limpiar selección | L mostrar/ocultar etiquetas | "
            "C limpiar dibujo | D mostrar/ocultar dibujos | B black | F freeze | P pnote | "
            "T iniciar/pausar cronómetro | Shift+T reiniciar cronómetro | "
            "W fullscreen | H ayuda | Shift+C customize | Ctrl/Cmd+M mover proyector | Ctrl/Cmd+R re-detectar pantallas | Ctrl/Cmd+Q salir | "
            "Ctrl/Cmd+1..4 seleccionar panel | Alt/Option+1..4 asignar contenido | "
            "Clic derecho en panel: cambiar contenido"
        )

    def _update_help_bar_visibility(self) -> None:
        self.help_bar.setVisible(self.show_help_bar)

    def toggle_help_bar(self) -> None:
        self.show_help_bar = not self.show_help_bar
        self._update_help_bar_visibility()

    def toggle_panel_role_labels(self) -> None:
        self.show_panel_role_labels = not self.show_panel_role_labels
        self._render_views()
        self._update_mode_bar_for_state(
            "Etiquetas visibles" if self.show_panel_role_labels else "Etiquetas ocultas"
        )

    def _get_panel_view(self, panel_key: str) -> SlideView:
        mapping = {
            "main_left": self.current_slide_view,
            "right_top": self.next_slide_view,
            "right_middle": self.current_note_view,
            "right_bottom": self.next_note_view,
        }
        return mapping[panel_key]
    
    def select_panel(self, panel_key: str) -> None:
        self.selected_panel_key = panel_key

        # limpiar todos
        for key in ["main_left", "right_top", "right_middle", "right_bottom"]:
            view = self._get_panel_view(key)
            view.set_panel_selected(False)

        # marcar seleccionado
        view = self._get_panel_view(panel_key)
        view.set_panel_selected(True)

        self._update_mode_bar_for_state(f"Panel seleccionado: {panel_key}")

    def assign_to_selected_panel(self, role: str) -> None:
        if self.selected_panel_key is None:
            return

        # cargar layout actual
        layout = self.layout_config.panel_roles.copy()

        if not self.layout_config.allow_duplicate_roles:
            # evitar duplicados: swap automático
            for k, v in layout.items():
                if v == role:
                    layout[k] = layout[self.selected_panel_key]

        layout[self.selected_panel_key] = role
        self.layout_config.panel_roles = layout
        save_layout_config(self.layout_config)

        self._render_views()
        self._update_mode_bar_for_state(f"{role} → {self.selected_panel_key}")

    def _format_elapsed_time(self, total_seconds: int) -> str:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _update_timer_label(self) -> None:
        self.screen_timer_label.setText(
            f"Tiempo: {self._format_elapsed_time(self.presentation_elapsed_seconds)}"
        )

    def _on_clock_tick(self) -> None:
        self.presentation_elapsed_seconds += 1
        self._update_timer_label()

    def _reset_presentation_timer(self) -> None:
        self.presentation_elapsed_seconds = 0
        self._update_timer_label()

    def toggle_presentation_timer(self) -> None:
        if self.clock_timer.isActive():
            self.clock_timer.stop()
            self._update_mode_bar_for_state("Cronómetro pausado")
        else:
            self.clock_timer.start(1000)
            self._update_mode_bar_for_state("Cronómetro iniciado")

    def restart_presentation_timer(self) -> None:
        self.presentation_elapsed_seconds = 0
        self._update_timer_label()
        if not self.clock_timer.isActive():
            self.clock_timer.start(1000)
        self._update_mode_bar_for_state("Cronómetro reiniciado")
    
    def _schedule_projector_update(self, delay_ms: int = 16) -> None:
        if not self.projector_update_timer.isActive():
            self.projector_update_timer.start(delay_ms)

    def _get_panel_widget(self, panel_key: str) -> SlideView:
        mapping = {
            "main_left": self.current_slide_view,
            "right_top": self.next_slide_view,
            "right_middle": self.current_note_view,
            "right_bottom": self.next_note_view,
        }
        return mapping[panel_key]

    def _get_panel_display_name(self, panel_key: str) -> str:
        labels = {
            "main_left": "Panel izquierdo grande",
            "right_top": "Panel derecho superior",
            "right_middle": "Panel derecho medio",
            "right_bottom": "Panel derecho inferior",
        }
        return labels.get(panel_key, panel_key)

    def _get_panel_role(self, panel_key: str) -> str:
        return self.layout_config.panel_roles.get(panel_key, "slide_current")

    def _get_panel_key_for_role(self, role: str) -> str | None:
        for panel_key in PANEL_KEYS:
            if self._get_panel_role(panel_key) == role:
                return panel_key
        return None

    def _get_view_for_role(self, role: str) -> SlideView | None:
        panel_key = self._get_panel_key_for_role(role)
        if panel_key is None:
            return None
        return self._get_panel_widget(panel_key)

    def _get_active_slide_view(self) -> SlideView:
        return self._get_view_for_role("slide_current") or self.current_slide_view

    def _panel_role_label(self, role: str) -> str:
        labels = {
            "slide_current": "Filmina actual",
            "slide_next": "Filmina siguiente",
            "notes_current": "Notas actuales",
            "notes_next": "Notas siguientes",
        }
        return labels.get(role, role)

    def _panel_role_color(self, role: str) -> str:
        colors = {
            "slide_current": "#ef4444",
            "slide_next": "#f59e0b",
            "notes_current": "#3b82f6",
            "notes_next": "#a855f7",
        }
        return colors.get(role, "#6b7280")

    def _show_panel_context_menu(self, panel_key: str) -> None:
        menu = QMenu(self)

        title_action = QAction(f"Cambiar contenido de: {self._get_panel_display_name(panel_key)}", self)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        current_role = self._get_panel_role(panel_key)
        role_items = [
            ("slide_current", "Filmina actual"),
            ("slide_next", "Filmina siguiente"),
            ("notes_current", "Notas actuales"),
            ("notes_next", "Notas siguientes"),
        ]

        for role_value, label in role_items:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(current_role == role_value)
            action.triggered.connect(
                lambda checked=False, pk=panel_key, rv=role_value: self._assign_role_to_panel(pk, rv)
            )
            menu.addAction(action)

        menu.exec(QCursor.pos())

    def _assign_role_to_panel(self, panel_key: str, new_role: str) -> None:
        current_role = self._get_panel_role(panel_key)
        if current_role == new_role:
            return

        if self.layout_config.allow_duplicate_roles:
            self.layout_config.panel_roles[panel_key] = new_role
        else:
            other_panel = self._get_panel_key_for_role(new_role)
            if other_panel is not None and other_panel != panel_key:
                self.layout_config.panel_roles[other_panel] = current_role
            self.layout_config.panel_roles[panel_key] = new_role

        save_layout_config(self.layout_config)

        self._configure_active_slide_view()
        self._clear_selection_state()
        self.control_zoom_viewport_norm = None
        self.projector_zoom_viewport_norm = None
        self.overlay_pointer_pos_norm = None

        self._render_views()
        self._update_projector()
        self._update_mode_bar_for_state(
            f"{self._panel_role_label(new_role)} en {self._get_panel_display_name(panel_key)}"
        )

    def _on_allow_duplicates_toggled(self, checked: bool) -> None:
        if self._updating_duplicates_checkbox:
            return

        self.layout_config.allow_duplicate_roles = checked
        save_layout_config(self.layout_config)

        self.layout_config = load_layout_config()

        self._updating_duplicates_checkbox = True
        self.allow_duplicates_checkbox.setChecked(self.layout_config.allow_duplicate_roles)
        self._updating_duplicates_checkbox = False

        self._configure_active_slide_view()
        self._clear_selection_state()
        self.control_zoom_viewport_norm = None
        self.projector_zoom_viewport_norm = None
        self.overlay_pointer_pos_norm = None

        self._render_views()
        self._update_projector()
        self._update_mode_bar_for_state(
            "Duplicados permitidos" if self.layout_config.allow_duplicate_roles else "Duplicados desactivados"
        )

    def _configure_active_slide_view(self) -> None:
        for panel_key in PANEL_KEYS:
            view = self._get_panel_widget(panel_key)
            view.enable_interaction(False)
            view.set_mouse_callbacks(
                on_press=None,
                on_move=None,
                on_release=None,
                on_hover=None,
                on_right_click=lambda pk=panel_key: self._show_panel_context_menu(pk),
            )
            view.unsetCursor()

        active_view = self._get_active_slide_view()
        active_panel_key = None
        for panel_key in PANEL_KEYS:
            if self._get_panel_widget(panel_key) is active_view:
                active_panel_key = panel_key
                break

        active_view.enable_interaction(True)
        active_view.set_mouse_callbacks(
            on_press=self._on_current_slide_mouse_press,
            on_move=self._on_current_slide_mouse_move,
            on_release=self._on_current_slide_mouse_release,
            on_hover=self._on_current_slide_mouse_hover,
            on_right_click=lambda pk=active_panel_key or "main_left": self._show_panel_context_menu(pk),
        )

    def _resolve_role_content(self, role: str) -> tuple[int | None, str]:
        next_idx = self.current_page_index + 1

        if role == "slide_current":
            return self.current_page_index, "slide"

        if role == "slide_next":
            if next_idx < self.pdf_loader.page_count:
                return next_idx, "slide"
            return None, "slide"

        if role == "notes_current":
            return self.current_page_index, "notes"

        if role == "notes_next":
            if next_idx < self.pdf_loader.page_count:
                return next_idx, "notes"
            return None, "notes"

        return None, "slide"

    def set_projector_window(self, projector_window: ProjectorWindow) -> None:
        self.projector_window = projector_window
        self.projector_window.set_pdf_loader(self.pdf_loader)

    def refresh_screens(self, initial: bool = False) -> None:
        self.available_screens = list(QApplication.screens())

        if self.projector_window is None:
            self._update_screen_bar()
            return

        if not self.available_screens:
            self._update_screen_bar()
            return

        primary_screen = self.available_screens[0]

        if len(self.available_screens) >= 2:
            if self.projector_screen_index is None or self.projector_screen_index >= len(self.available_screens):
                self.projector_screen_index = 1
        else:
            self.projector_screen_index = 0

        projector_screen = self.available_screens[self.projector_screen_index]

        self.projector_window.move_to_screen(projector_screen)

        if projector_screen != primary_screen:
            self.projector_window.show_projector(fullscreen=True)
        else:
            self.projector_window.show_projector(fullscreen=False)

        self._update_projector()
        self._update_mode_bar_for_state(
            extra_message=f"Pantallas detectadas: {len(self.available_screens)} | Proyector en: {projector_screen.name()}"
        )
        self._update_screen_bar()

    def move_projector_to_next_screen(self) -> None:
        if self.projector_window is None:
            self._update_screen_bar()
            return

        screens = list(QApplication.screens())
        if not screens:
            self._update_screen_bar()
            return

        self.available_screens = screens

        if self.projector_screen_index is None:
            self.projector_screen_index = 0
        else:
            self.projector_screen_index = (self.projector_screen_index + 1) % len(screens)

        screen = screens[self.projector_screen_index]
        primary_screen = screens[0]

        self.projector_window.move_to_screen(screen)

        if screen != primary_screen:
            self.projector_window.show_projector(fullscreen=True)
        else:
            self.projector_window.show_projector(fullscreen=False)

        self._update_projector()
        self._update_mode_bar_for_state(
            extra_message=f"Proyector movido a: {screen.name()}"
        )
        self._update_screen_bar()

    def _build_ui(self) -> None:
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.addWidget(self.next_slide_view)
        self.right_splitter.addWidget(self.current_note_view)
        self.right_splitter.addWidget(self.next_note_view)
        self.right_splitter.setChildrenCollapsible(False)
        self.right_splitter.setOpaqueResize(True)
        self.right_splitter.splitterMoved.connect(self._on_right_splitter_moved)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.current_slide_view)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setOpaqueResize(True)
        self.main_splitter.splitterMoved.connect(self._on_main_splitter_moved)

        self.outer_splitter = QSplitter(Qt.Orientation.Vertical)
        self.outer_splitter.addWidget(self.main_splitter)
        self.outer_splitter.addWidget(self.pnote_bar)
        self.outer_splitter.setChildrenCollapsible(False)
        self.outer_splitter.setOpaqueResize(True)
        self.outer_splitter.splitterMoved.connect(self._on_outer_splitter_moved)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        layout.addWidget(self.outer_splitter, stretch=1)
        layout.addWidget(self.mode_bar)
        layout.addWidget(self.screen_bar)
        layout.addWidget(self.help_bar)

        self.setCentralWidget(central)
        self._apply_customize_visuals()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)

        open_action = QAction("Abrir PDF", self)
        open_action.triggered.connect(self.open_pdf_dialog)
        toolbar.addAction(open_action)

        toggle_customize_action = QAction("Customize (Shift+C)", self)
        toggle_customize_action.triggered.connect(self.toggle_customize_mode)
        toolbar.addAction(toggle_customize_action)

        prev_action = QAction("Anterior", self)
        prev_action.triggered.connect(self.go_previous_page)
        toolbar.addAction(prev_action)

        next_action = QAction("Siguiente", self)
        next_action.triggered.connect(self.go_next_page)
        toolbar.addAction(next_action)

        move_projector_action = QAction("Mover proyector (Ctrl+M / Cmd+M)", self)
        move_projector_action.triggered.connect(self.move_projector_to_next_screen)
        toolbar.addAction(move_projector_action)

        refresh_screens_action = QAction("Re-detectar pantallas (Ctrl+R / Cmd+R)", self)
        refresh_screens_action.triggered.connect(self.refresh_screens)
        toolbar.addAction(refresh_screens_action)

        toolbar.addSeparator()
        toolbar.addWidget(self.allow_duplicates_checkbox)
        toolbar.addSeparator()

        toggle_help_action = QAction("Ayuda (H)", self)
        toggle_help_action.triggered.connect(self.toggle_help_bar)
        toolbar.addAction(toggle_help_action)

        toggle_timer_action = QAction("Cronómetro (T)", self)
        toggle_timer_action.triggered.connect(self.toggle_presentation_timer)
        toolbar.addAction(toggle_timer_action)

        restart_timer_action = QAction("Reiniciar cronómetro (Shift+T)", self)
        restart_timer_action.triggered.connect(self.restart_presentation_timer)
        toolbar.addAction(restart_timer_action)

        quit_action = QAction("Salir (Ctrl+Q / Cmd+Q)", self)
        quit_action.triggered.connect(QApplication.quit)
        toolbar.addAction(quit_action)

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=self.go_next_page)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self.go_next_page)
        QShortcut(QKeySequence(Qt.Key.Key_Down), self, activated=self.go_next_page)
        QShortcut(QKeySequence(Qt.Key.Key_PageDown), self, activated=self.go_next_page)

        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=self.go_previous_page)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self, activated=self.go_previous_page)
        QShortcut(QKeySequence(Qt.Key.Key_Up), self, activated=self.go_previous_page)
        QShortcut(QKeySequence(Qt.Key.Key_PageUp), self, activated=self.go_previous_page)

        QShortcut(QKeySequence(Qt.Key.Key_Home), self, activated=self.go_first_page)
        QShortcut(QKeySequence(Qt.Key.Key_End), self, activated=self.go_last_page)

        QShortcut(QKeySequence("Shift+C"), self, activated=self.toggle_customize_mode)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.handle_escape)

        QShortcut(QKeySequence("B"), self, activated=self.toggle_black_screen)
        QShortcut(QKeySequence("F"), self, activated=self.toggle_freeze)
        QShortcut(QKeySequence("W"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("P"), self, activated=self.toggle_pnote)

        QShortcut(QKeySequence("Ctrl+M"), self, activated=self.move_projector_to_next_screen)
        QShortcut(QKeySequence("Meta+M"), self, activated=self.move_projector_to_next_screen)

        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_screens)
        QShortcut(QKeySequence("Meta+R"), self, activated=self.refresh_screens)

        QShortcut(QKeySequence("Ctrl+Q"), self, activated=QApplication.quit)
        QShortcut(QKeySequence("Meta+Q"), self, activated=QApplication.quit)

        QShortcut(QKeySequence("1"), self, activated=self.set_tool_normal)
        QShortcut(QKeySequence("2"), self, activated=self.set_tool_pointer)
        QShortcut(QKeySequence("3"), self, activated=self.set_tool_pen)
        QShortcut(QKeySequence("4"), self, activated=self.set_tool_eraser)
        QShortcut(QKeySequence("5"), self, activated=self.set_tool_spotlight)

        QShortcut(QKeySequence("C"), self, activated=self.clear_current_page_drawings)
        QShortcut(QKeySequence("D"), self, activated=self.toggle_drawings_visible)

        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self.undo_current_page)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.redo_current_page)

        QShortcut(QKeySequence("Z"), self, activated=self.apply_zoom_from_selection)
        QShortcut(QKeySequence("X"), self, activated=self.clear_selection_only)
        QShortcut(QKeySequence("L"), self, activated=self.toggle_panel_role_labels)

        QShortcut(QKeySequence("H"), self, activated=self.toggle_help_bar)

        QShortcut(QKeySequence("T"), self, activated=self.toggle_presentation_timer)
        QShortcut(QKeySequence("Shift+T"), self, activated=self.restart_presentation_timer)

        # Mac
        QShortcut(QKeySequence("Meta+1"), self, activated=lambda: self.select_panel("main_left"))
        QShortcut(QKeySequence("Meta+2"), self, activated=lambda: self.select_panel("right_top"))
        QShortcut(QKeySequence("Meta+3"), self, activated=lambda: self.select_panel("right_middle"))
        QShortcut(QKeySequence("Meta+4"), self, activated=lambda: self.select_panel("right_bottom"))

        # Windows / Linux
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.select_panel("main_left"))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.select_panel("right_top"))
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self.select_panel("right_middle"))
        QShortcut(QKeySequence("Ctrl+4"), self, activated=lambda: self.select_panel("right_bottom"))

        QShortcut(QKeySequence("Alt+1"), self, activated=lambda: self.assign_to_selected_panel("slide_current"))
        QShortcut(QKeySequence("Alt+2"), self, activated=lambda: self.assign_to_selected_panel("slide_next"))
        QShortcut(QKeySequence("Alt+3"), self, activated=lambda: self.assign_to_selected_panel("notes_current"))
        QShortcut(QKeySequence("Alt+4"), self, activated=lambda: self.assign_to_selected_panel("notes_next"))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        text = event.text()
        key = event.key()

        if text == "+" or (key == Qt.Key.Key_Equal and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.increase_tool_size()
            event.accept()
            return

        if text == "-":
            self.decrease_tool_size()
            event.accept()
            return

        if key == Qt.Key.Key_Plus:
            self.increase_tool_size()
            event.accept()
            return

        if key == Qt.Key.Key_Minus:
            self.decrease_tool_size()
            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        if self.projector_window is not None:
            self.projector_window.close()
        super().closeEvent(event)

    def open_pdf_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            "",
            "PDF Files (*.pdf)",
        )
        if file_path:
            self.load_pdf(Path(file_path))

    def load_pdf(self, pdf_path: Path) -> None:
        try:
            self.pdf_loader.load(pdf_path)
            self.current_page_index = 0
            self.projector_page_index = 0
            self.current_stroke = None
            self._operation_snapshot_taken = False
            self.overlay_pointer_pos_norm = None
            self._clear_selection_state()
            self.control_zoom_viewport_norm = None
            self.projector_zoom_viewport_norm = None
            self._reset_presentation_timer()
            self._configure_active_slide_view()

            if self.projector_window is not None:
                self.projector_window.set_pdf_loader(self.pdf_loader)

            self._render_views()
            self._update_projector()
            self._update_screen_bar()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def go_previous_page(self) -> None:
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.current_stroke = None
            self._operation_snapshot_taken = False
            self._clear_selection_state()
            self.control_zoom_viewport_norm = None
            self.projector_zoom_viewport_norm = None

            if not self.is_frozen:
                self.projector_page_index = self.current_page_index
                self._update_projector()

            self._render_views()
            self._update_mode_bar_for_state()
            self._update_screen_bar()

    def go_next_page(self) -> None:
        if self.pdf_loader.is_loaded and self.current_page_index < self.pdf_loader.page_count - 1:
            self.current_page_index += 1
            self.current_stroke = None
            self._operation_snapshot_taken = False
            self._clear_selection_state()
            self.control_zoom_viewport_norm = None
            self.projector_zoom_viewport_norm = None

            if not self.is_frozen:
                self.projector_page_index = self.current_page_index
                self._update_projector()

            self._render_views()
            self._update_mode_bar_for_state()
            self._update_screen_bar()

    def go_first_page(self) -> None:
        if self.pdf_loader.is_loaded:
            self.current_page_index = 0
            self.current_stroke = None
            self._operation_snapshot_taken = False
            self._clear_selection_state()
            self.control_zoom_viewport_norm = None
            self.projector_zoom_viewport_norm = None

            if not self.is_frozen:
                self.projector_page_index = self.current_page_index
                self._update_projector()

            self._render_views()
            self._update_mode_bar_for_state()
            self._update_screen_bar()

    def go_last_page(self) -> None:
        if self.pdf_loader.is_loaded:
            self.current_page_index = self.pdf_loader.page_count - 1
            self.current_stroke = None
            self._operation_snapshot_taken = False
            self._clear_selection_state()
            self.control_zoom_viewport_norm = None
            self.projector_zoom_viewport_norm = None

            if not self.is_frozen:
                self.projector_page_index = self.current_page_index
                self._update_projector()

            self._render_views()
            self._update_mode_bar_for_state()
            self._update_screen_bar()

    def set_tool_normal(self) -> None:
        self.tool_mode = "normal"
        self.current_stroke = None
        self._operation_snapshot_taken = False
        self._clear_selection_state()
        self._update_mode_bar_for_state()
        self._update_current_slide_indicators()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()
        self._update_projector()

    def set_tool_pointer(self) -> None:
        self.tool_mode = "pointer"
        self.current_stroke = None
        self._operation_snapshot_taken = False
        self._update_mode_bar_for_state()
        self._update_current_slide_indicators()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()
        self._update_projector()

    def set_tool_pen(self) -> None:
        self.tool_mode = "pen"
        self.current_stroke = None
        self._operation_snapshot_taken = False
        self._clear_selection_state()
        self._update_mode_bar_for_state()
        self._update_current_slide_indicators()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()

    def set_tool_eraser(self) -> None:
        self.tool_mode = "eraser"
        self.current_stroke = None
        self._operation_snapshot_taken = False
        self._clear_selection_state()
        self._update_mode_bar_for_state()
        self._update_current_slide_indicators()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()

    def set_tool_spotlight(self) -> None:
        self.tool_mode = "spotlight"
        self.current_stroke = None
        self._operation_snapshot_taken = False
        self._update_mode_bar_for_state()
        self._update_current_slide_indicators()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()
        self._update_projector()

    def increase_tool_size(self) -> None:
        if self.tool_mode == "pen":
            self.pen_size = min(80, self.pen_size + 2)
        elif self.tool_mode == "eraser":
            self.eraser_size = min(80, self.eraser_size + 2)
        elif self.tool_mode == "pointer":
            self.pointer_size = min(80, self.pointer_size + 2)
        elif self.tool_mode == "spotlight":
            self.spotlight_size = min(300, self.spotlight_size + 10)
        else:
            return

        self._update_mode_bar_for_state()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()
        self._update_projector()

    def decrease_tool_size(self) -> None:
        if self.tool_mode == "pen":
            self.pen_size = max(2, self.pen_size - 2)
        elif self.tool_mode == "eraser":
            self.eraser_size = max(2, self.eraser_size - 2)
        elif self.tool_mode == "pointer":
            self.pointer_size = max(2, self.pointer_size - 2)
        elif self.tool_mode == "spotlight":
            self.spotlight_size = max(20, self.spotlight_size - 10)
        else:
            return

        self._update_mode_bar_for_state()
        self._update_current_tool_cursor()
        self._update_tool_preview()
        self._render_views()
        self._update_projector()

    def clear_current_page_drawings(self) -> None:
        page = self.current_page_index
        current = self._get_page_drawings(page)
        if not current:
            return

        self._push_undo_snapshot(page, current)
        self.page_drawings[page] = []
        self._clear_redo(page)
        self.current_stroke = None
        self._operation_snapshot_taken = False

        self._update_mode_bar_for_state("Dibujo actual limpiado")
        self._render_views()
        self._update_projector()

    def toggle_drawings_visible(self) -> None:
        self.drawings_visible = not self.drawings_visible
        msg = "Drawings ON" if self.drawings_visible else "Drawings OFF"
        self._update_mode_bar_for_state(msg)
        self._render_views()
        self._update_projector()

    def undo_current_page(self) -> None:
        page = self.current_page_index
        undo_stack = self.page_undo.setdefault(page, [])
        if not undo_stack:
            return

        current = deepcopy(self._get_page_drawings(page))
        previous = undo_stack.pop()

        self.page_redo.setdefault(page, []).append(current)
        self.page_drawings[page] = deepcopy(previous)

        self.current_stroke = None
        self._operation_snapshot_taken = False

        self._update_mode_bar_for_state("Undo")
        self._render_views()
        self._update_projector()

    def redo_current_page(self) -> None:
        page = self.current_page_index
        redo_stack = self.page_redo.setdefault(page, [])
        if not redo_stack:
            return

        current = deepcopy(self._get_page_drawings(page))
        restored = redo_stack.pop()

        self.page_undo.setdefault(page, []).append(current)
        self.page_drawings[page] = deepcopy(restored)

        self.current_stroke = None
        self._operation_snapshot_taken = False

        self._update_mode_bar_for_state("Redo")
        self._render_views()
        self._update_projector()

    def apply_zoom_from_selection(self) -> None:
        if self.selection_rect_norm is None:
            return

        x, y, w, h = self.selection_rect_norm
        if w < 0.001 or h < 0.001:
            return

        self.control_zoom_viewport_norm = (x, y, w, h)
        self.projector_zoom_viewport_norm = (x, y, w, h)
        self._clear_selection_state()
        self._update_mode_bar_for_state("Zoom aplicado")
        self._render_views()
        self._update_projector()

    def clear_selection_only(self) -> None:
        if self.selection_rect_norm is None and not self.is_selecting:
            return
        self._clear_selection_state()
        self._update_mode_bar_for_state("Selección limpiada")
        self._render_views()

    def handle_escape(self) -> None:
        if self.selected_panel_key is not None:
            for key in ["main_left", "right_top", "right_middle", "right_bottom"]:
                self._get_panel_view(key).set_panel_selected(False)

            self.selected_panel_key = None
            self._update_mode_bar_for_state("Selección de panel limpiada")
            return
        if self.control_zoom_viewport_norm is not None or self.projector_zoom_viewport_norm is not None:
            self.control_zoom_viewport_norm = None
            self.projector_zoom_viewport_norm = None
            self._clear_selection_state()
            self._update_mode_bar_for_state("Zoom desactivado")
            self._render_views()
            self._update_projector()
            return

        if self.selection_rect_norm is not None or self.is_selecting:
            self._clear_selection_state()
            self._render_views()
            return

        if self.customize_mode:
            self.customize_mode = False
            self._apply_customize_visuals()
            return

        if self.is_fullscreen:
            self.toggle_fullscreen()

    def toggle_customize_mode(self) -> None:
        self.customize_mode = not self.customize_mode
        self._apply_customize_visuals()

    def exit_customize_mode(self) -> None:
        if self.customize_mode:
            self.customize_mode = False
            self._apply_customize_visuals()
            return

        if self.is_fullscreen:
            self.toggle_fullscreen()

    def toggle_black_screen(self) -> None:
        self.is_black = not self.is_black
        self._update_mode_bar_for_state()
        self._update_projector()
        self._update_screen_bar()
        self._update_current_slide_indicators()

    def toggle_freeze(self) -> None:
        self.is_frozen = not self.is_frozen

        if not self.is_frozen:
            self.projector_page_index = self.current_page_index
            self._update_projector()

        self._update_mode_bar_for_state()
        self._update_screen_bar()
        self._update_current_slide_indicators()

    def toggle_fullscreen(self) -> None:
        if self.is_fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()

        self.is_fullscreen = not self.is_fullscreen
        self._update_screen_bar()

    def toggle_pnote(self) -> None:
        self.show_pnote = not self.show_pnote
        self.pnote_bar.setVisible(self.show_pnote)

        if self.outer_splitter is not None and not self.show_pnote:
            sizes = self.outer_splitter.sizes()
            if len(sizes) == 2:
                self.outer_splitter.setSizes([sum(sizes), 0])

        if self.outer_splitter is not None and self.show_pnote:
            self._apply_layout_to_splitters()

        if self.pdf_loader.is_loaded:
            self._render_views()

    def _update_mode_bar_for_state(self, extra_message: str | None = None) -> None:
        if self.customize_mode:
            self.mode_bar.setText("Modo customize activado — arrastra bordes, Esc para salir")
            self.mode_bar.setStyleSheet(
                "background-color: #3a2f00; color: #ffd54f; padding: 4px; font-weight: bold;"
            )
            return

        flags: list[str] = []

        if self.tool_mode == "pen":
            flags.append(f"PEN size={self.pen_size}")
        elif self.tool_mode == "eraser":
            flags.append(f"ERASER size={self.eraser_size}")
        elif self.tool_mode == "pointer":
            flags.append(f"POINTER size={self.pointer_size}")
        elif self.tool_mode == "spotlight":
            flags.append(f"SPOTLIGHT size={self.spotlight_size}")

        if self.control_zoom_viewport_norm is not None:
            flags.append("ZOOM")

        if self.selection_rect_norm is not None or self.is_selecting:
            flags.append("SELECTION")

        if not self.drawings_visible:
            flags.append("DRAWINGS OFF")

        if self.is_frozen:
            flags.append(
                f"FREEZE mostrado={self.projector_page_index + 1} control={self.current_page_index + 1}"
            )

        if self.is_black:
            flags.append("BLACK")

        if extra_message:
            flags.append(extra_message)

        if flags:
            self.mode_bar.setText(" | ".join(flags))
            self.mode_bar.setStyleSheet(
                "background-color: #003049; color: #ffffff; padding: 4px; font-weight: bold;"
            )
        else:
            self.mode_bar.setText("Modo normal")
            self.mode_bar.setStyleSheet(
                "background-color: #1f1f1f; color: #d0d0d0; padding: 4px;"
            )

    def _update_screen_bar(self) -> None:
        total = len(self.available_screens)
        if total == 0:
            self.screen_status_label.setText("Pantallas: 0 | Proyector: no asignado")
            return

        projector_name = "no asignado"
        mode = "window"

        if self.projector_screen_index is not None and 0 <= self.projector_screen_index < total:
            screen = self.available_screens[self.projector_screen_index]
            projector_name = screen.name()
            primary = self.available_screens[0]
            mode = "fullscreen" if screen != primary else "window"

        self.screen_status_label.setText(
            f"Pantallas: {total} | Proyector: {projector_name} | Modo: {mode} | Control: {self.current_page_index + 1} | Mostrado: {self.projector_page_index + 1}"
        )

    def _apply_customize_visuals(self) -> None:
        if self.main_splitter is None or self.right_splitter is None or self.outer_splitter is None:
            return

        splitters = [self.main_splitter, self.right_splitter, self.outer_splitter]

        if self.customize_mode:
            self.mode_bar.setText("Modo customize activado — arrastra bordes, Esc para salir")
            self.mode_bar.setStyleSheet(
                "background-color: #3a2f00; color: #ffd54f; padding: 4px; font-weight: bold;"
            )
            handle_style = """
                QSplitter::handle {
                    background-color: #ffd54f;
                }
            """
            for splitter in splitters:
                splitter.setHandleWidth(12)
                splitter.setStyleSheet(handle_style)
                for i in range(1, splitter.count()):
                    splitter.handle(i).setEnabled(True)
        else:
            self._update_mode_bar_for_state()
            for splitter in splitters:
                splitter.setHandleWidth(2)
                splitter.setStyleSheet("")
                for i in range(1, splitter.count()):
                    splitter.handle(i).setEnabled(False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.main_splitter is not None and self.right_splitter is not None and self.outer_splitter is not None:
            if not self._applying_layout:
                self._apply_layout_to_splitters()
        if self.pdf_loader.is_loaded:
            self._render_views()

    def _apply_layout_to_splitters(self) -> None:
        if self.main_splitter is None or self.right_splitter is None or self.outer_splitter is None:
            return

        self._applying_layout = True
        try:
            total_w = max(self.main_splitter.width(), 100)
            left_w = int(total_w * self.layout_config.main_split_ratio)
            right_w = max(total_w - left_w, 1)
            self.main_splitter.setSizes([left_w, right_w])

            total_h = max(self.right_splitter.height(), 300)
            stack = self.layout_config.right_stack_ratios
            h1 = int(total_h * stack[0])
            h2 = int(total_h * stack[1])
            h3 = max(total_h - h1 - h2, 1)
            self.right_splitter.setSizes([h1, h2, h3])

            if self.show_pnote:
                total_outer_h = max(self.outer_splitter.height(), 300)
                content_h = int(total_outer_h * self.layout_config.content_vs_pnote_ratio)
                pnote_h = max(total_outer_h - content_h, 24)
                self.outer_splitter.setSizes([content_h, pnote_h])
            else:
                sizes = self.outer_splitter.sizes()
                total_outer_h = sum(sizes) if sizes else max(self.outer_splitter.height(), 300)
                self.outer_splitter.setSizes([total_outer_h, 0])
        finally:
            self._applying_layout = False

    def _on_main_splitter_moved(self, pos: int, index: int) -> None:
        if self._applying_layout or not self.customize_mode or self.main_splitter is None:
            return

        sizes = self.main_splitter.sizes()
        total = sum(sizes)
        if total <= 0:
            return

        self.layout_config.main_split_ratio = sizes[0] / total
        save_layout_config(self.layout_config)

        if self.pdf_loader.is_loaded:
            self._render_views()

    def _on_right_splitter_moved(self, pos: int, index: int) -> None:
        if self._applying_layout or not self.customize_mode or self.right_splitter is None:
            return

        sizes = self.right_splitter.sizes()
        total = sum(sizes)
        if total <= 0:
            return

        self.layout_config.right_stack_ratios = [s / total for s in sizes]
        save_layout_config(self.layout_config)

        if self.pdf_loader.is_loaded:
            self._render_views()

    def _on_outer_splitter_moved(self, pos: int, index: int) -> None:
        if self._applying_layout or not self.customize_mode or self.outer_splitter is None:
            return

        if not self.show_pnote:
            return

        sizes = self.outer_splitter.sizes()
        total = sum(sizes)
        if total <= 0:
            return

        self.layout_config.content_vs_pnote_ratio = sizes[0] / total
        save_layout_config(self.layout_config)

        if self.pdf_loader.is_loaded:
            self._render_views()

    def _normalize_rect(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
    ) -> tuple[float, float, float, float]:
        x1, y1 = start
        x2, y2 = end
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        return (x, y, w, h)

    def _clear_selection_state(self) -> None:
        self.selection_start_norm = None
        self.selection_end_norm = None
        self.selection_rect_norm = None
        self.is_selecting = False

    def _on_current_slide_mouse_hover(self, nx: float, ny: float) -> None:
        self.overlay_pointer_pos_norm = (nx, ny)

        self._update_tool_preview()

        active_view = self._get_active_slide_view()

        if self.tool_mode == "pointer":
            active_view.set_pointer_overlay(
                enabled=True,
                pos_norm=self.overlay_pointer_pos_norm,
                radius_px=float(self.pointer_size),
                color="#ff3b30",
            )
        elif self.tool_mode == "spotlight":
            active_view.set_spotlight_overlay(
                enabled=True,
                pos_norm=self.overlay_pointer_pos_norm,
                radius_px=float(self.spotlight_size),
            )

        active_view.update()
        self._schedule_projector_update()        

    def _on_current_slide_mouse_press(self, nx: float, ny: float) -> None:
        if not self.pdf_loader.is_loaded or self.customize_mode:
            return

        self.overlay_pointer_pos_norm = (nx, ny)

        if self.tool_mode in ("pointer", "spotlight"):
            self.selection_start_norm = (nx, ny)
            self.selection_end_norm = (nx, ny)
            self.selection_rect_norm = (nx, ny, 0.0, 0.0)
            self.is_selecting = True
            self._render_views()
            return

        if self.tool_mode == "pen":
            self._begin_page_operation_snapshot(self.current_page_index)
            self.current_stroke = {
                "tool": "pen",
                "color": "#ff3b30",
                "size": float(self.pen_size),
                "points": [(nx, ny)],
            }
            self._render_views()
        elif self.tool_mode == "eraser":
            self.current_stroke = None
            self._begin_page_operation_snapshot(self.current_page_index)
            self._erase_at(nx, ny)
            self._render_views()
            self._update_projector()

    def _on_current_slide_mouse_move(self, nx: float, ny: float) -> None:
        if not self.pdf_loader.is_loaded or self.customize_mode:
            return

        self.overlay_pointer_pos_norm = (nx, ny)

        if self.is_selecting and self.tool_mode in ("pointer", "spotlight") and self.selection_start_norm is not None:
            self.selection_end_norm = (nx, ny)
            self.selection_rect_norm = self._normalize_rect(self.selection_start_norm, self.selection_end_norm)
            self._render_views()
            return

        if self.tool_mode == "pen" and self.current_stroke is not None:
            points = self.current_stroke["points"]
            if not points:
                points.append((nx, ny))
            else:
                px, py = points[-1]
                dist = math.hypot(nx - px, ny - py)
                if dist >= 0.002:
                    points.append((nx, ny))
            self._render_views()
        elif self.tool_mode == "eraser":
            self._erase_at(nx, ny)
            self._render_views()
            self._update_projector()
        elif self.tool_mode in ("pointer", "spotlight"):
            active_view = self._get_active_slide_view()

            if self.tool_mode == "pointer":
                active_view.set_pointer_overlay(
                    enabled=True,
                    pos_norm=self.overlay_pointer_pos_norm,
                    radius_px=float(self.pointer_size),
                    color="#ff3b30",
                )
                active_view.set_spotlight_overlay(False)
            else:
                active_view.set_spotlight_overlay(
                    enabled=True,
                    pos_norm=self.overlay_pointer_pos_norm,
                    radius_px=float(self.spotlight_size),
                )
                active_view.set_pointer_overlay(False)

            if self.selection_rect_norm is not None:
                active_view.set_selection_overlay(
                    enabled=True,
                    rect_norm=self.selection_rect_norm,
                )

            self._update_tool_preview()
            active_view.update()
            self._schedule_projector_update()

    def _current_selection_min_size(self) -> tuple[float, float]:
        if self.control_zoom_viewport_norm is None:
            return (0.001, 0.001)

        _, _, vw, vh = self.control_zoom_viewport_norm
        return (
            max(0.001, vw * 0.01),
            max(0.001, vh * 0.01),
        )

    def _on_current_slide_mouse_release(self, nx: float, ny: float) -> None:
        if not self.pdf_loader.is_loaded or self.customize_mode:
            return

        self.overlay_pointer_pos_norm = (nx, ny)

        if self.is_selecting and self.tool_mode in ("pointer", "spotlight") and self.selection_start_norm is not None:
            self.selection_end_norm = (nx, ny)
            rect = self._normalize_rect(self.selection_start_norm, self.selection_end_norm)

            min_w, min_h = self._current_selection_min_size()
            if rect[2] < min_w or rect[3] < min_h:
                self.selection_rect_norm = None
            else:
                self.selection_rect_norm = rect

            self.is_selecting = False
            self._render_views()
            self._update_mode_bar_for_state()
            return

        if self.tool_mode == "pen" and self.current_stroke is not None:
            points = self.current_stroke["points"]
            if not points or points[-1] != (nx, ny):
                points.append((nx, ny))

            if len(points) >= 2:
                self._get_page_drawings(self.current_page_index).append(self.current_stroke)
                self._clear_redo(self.current_page_index)

            self.current_stroke = None
            self._operation_snapshot_taken = False
            self._render_views()
            self._update_projector()

        elif self.tool_mode == "eraser":
            if self._operation_snapshot_taken:
                self._clear_redo(self.current_page_index)
            self._operation_snapshot_taken = False

        elif self.tool_mode in ("pointer", "spotlight"):
            self._render_views()
            self._update_projector()

    def _get_page_drawings(self, page_index: int) -> list[dict]:
        if page_index not in self.page_drawings:
            self.page_drawings[page_index] = []
        return self.page_drawings[page_index]

    def _get_page_undo(self, page_index: int) -> list[list[dict]]:
        if page_index not in self.page_undo:
            self.page_undo[page_index] = []
        return self.page_undo[page_index]

    def _get_page_redo(self, page_index: int) -> list[list[dict]]:
        if page_index not in self.page_redo:
            self.page_redo[page_index] = []
        return self.page_redo[page_index]

    def _push_undo_snapshot(self, page_index: int, drawings: list[dict]) -> None:
        self._get_page_undo(page_index).append(deepcopy(drawings))

    def _clear_redo(self, page_index: int) -> None:
        self.page_redo[page_index] = []

    def _begin_page_operation_snapshot(self, page_index: int) -> None:
        if self._operation_snapshot_taken:
            return
        self._push_undo_snapshot(page_index, self._get_page_drawings(page_index))
        self._operation_snapshot_taken = True

    def _erase_at(self, nx: float, ny: float) -> None:
        strokes = self._get_page_drawings(self.current_page_index)
        if not strokes:
            return

        active_view = self._get_active_slide_view()
        rect = active_view.get_content_rect()
        base = max(min(rect.width(), rect.height()), 1.0)
        radius = self.eraser_size / base

        new_strokes: list[dict] = []

        for stroke in strokes:
            split_parts = self._split_stroke_by_eraser(stroke, nx, ny, radius)
            new_strokes.extend(split_parts)

        self.page_drawings[self.current_page_index] = new_strokes

    def _split_stroke_by_eraser(
        self,
        stroke: dict,
        ex: float,
        ey: float,
        radius: float,
    ) -> list[dict]:
        points = stroke.get("points", [])
        if len(points) < 2:
            return []

        kept_segments: list[list[tuple[float, float]]] = []
        current_segment: list[tuple[float, float]] = []

        for px, py in points:
            dist = math.hypot(px - ex, py - ey)
            keep_point = dist > radius

            if keep_point:
                current_segment.append((px, py))
            else:
                if len(current_segment) >= 2:
                    kept_segments.append(current_segment)
                current_segment = []

        if len(current_segment) >= 2:
            kept_segments.append(current_segment)

        result: list[dict] = []
        for seg in kept_segments:
            result.append(
                {
                    "tool": stroke.get("tool", "pen"),
                    "color": stroke.get("color", "#ff3b30"),
                    "size": float(stroke.get("size", 6.0)),
                    "points": seg,
                }
            )

        return result

    def _compose_current_page_drawings(self) -> list[dict]:
        drawings = list(self._get_page_drawings(self.current_page_index))
        if self.current_stroke is not None and self.tool_mode == "pen":
            drawings.append(self.current_stroke)
        return drawings

    def _clear_view_overlays(self, view: SlideView) -> None:
        view.set_drawings([], visible=False)
        view.set_pointer_overlay(False)
        view.set_spotlight_overlay(False)
        view.clear_selection_overlay()
        view.set_status_indicators([])
        view.set_tool_preview(False)

    def _update_panel_role_labels(self) -> None:
        for panel_key in PANEL_KEYS:
            view = self._get_panel_widget(panel_key)
            if not self.show_panel_role_labels:
                view.clear_panel_label()
                continue

            role = self._get_panel_role(panel_key)
            view.set_panel_label(
                visible=True,
                text=self._panel_role_label(role),
                color=self._panel_role_color(role),
            )

    def _render_views(self) -> None:
        if not self.pdf_loader.is_loaded:
            for panel_key in PANEL_KEYS:
                view = self._get_panel_widget(panel_key)
                view.clear_slide()
                self._clear_view_overlays(view)
                view.clear_panel_label()
                view.set_panel_selected(False)
            self.pnote_bar.setText("pnote: sin contenido")
            return

        self._configure_active_slide_view()

        for panel_key in PANEL_KEYS:
            role = self._get_panel_role(panel_key)
            view = self._get_panel_widget(panel_key)
            page_index, region = self._resolve_role_content(role)

            if page_index is None:
                view.clear_slide()
                self._clear_view_overlays(view)
                view.set_panel_selected(panel_key == self.selected_panel_key)
                continue

            apply_zoom = role == "slide_current"
            self._render(view, page_index, region, apply_zoom=apply_zoom)

            if role == "slide_current":
                view.set_viewport_norm(self.control_zoom_viewport_norm)
            else:
                view.set_viewport_norm(None)

            self._clear_view_overlays(view)
            view.set_panel_selected(panel_key == self.selected_panel_key)

        current_drawings = self._compose_current_page_drawings() if self.drawings_visible else []
        active_view = self._get_active_slide_view()
        active_view.set_drawings(current_drawings, visible=self.drawings_visible)

        if self.tool_mode == "pointer" and self.overlay_pointer_pos_norm is not None:
            active_view.set_pointer_overlay(
                enabled=True,
                pos_norm=self.overlay_pointer_pos_norm,
                radius_px=float(self.pointer_size),
                color="#ff3b30",
            )
        elif self.tool_mode == "spotlight" and self.overlay_pointer_pos_norm is not None:
            active_view.set_spotlight_overlay(
                enabled=True,
                pos_norm=self.overlay_pointer_pos_norm,
                radius_px=float(self.spotlight_size),
            )

        if self.selection_rect_norm is not None:
            active_view.set_selection_overlay(
                enabled=True,
                rect_norm=self.selection_rect_norm,
            )

        if self.show_pnote:
            pnotes = self.pdf_loader.get_pnotes(self.current_page_index)
            if pnotes:
                self.pnote_bar.setText("pnote: " + " | ".join(pnotes))
            else:
                self.pnote_bar.setText("pnote: (sin notas)")

        self._update_panel_role_labels()
        self._update_current_slide_indicators()
        self._update_tool_preview()

    def _update_current_slide_indicators(self) -> None:
        for panel_key in PANEL_KEYS:
            self._get_panel_widget(panel_key).set_status_indicators([])

        indicators: list[tuple[str, str]] = []

        if self.is_frozen:
            indicators.append(("FREEZE", "#3b82f6"))

        if self.is_black:
            indicators.append(("BLACK", "#6b7280"))

        if self.tool_mode == "pen":
            indicators.append(("PEN", "#ef4444"))
        elif self.tool_mode == "eraser":
            indicators.append(("ERASER", "#111111"))
        elif self.tool_mode == "pointer":
            indicators.append(("POINTER", "#ef4444"))
        elif self.tool_mode == "spotlight":
            indicators.append(("SPOTLIGHT", "#a855f7"))

        if self.selection_rect_norm is not None or self.is_selecting:
            indicators.append(("SELECTION", "#00e5ff"))

        if self.control_zoom_viewport_norm is not None:
            indicators.append(("ZOOM", "#22c55e"))

        self._get_active_slide_view().set_status_indicators(indicators)

    def _update_tool_preview(self) -> None:
        for panel_key in PANEL_KEYS:
            self._get_panel_widget(panel_key).set_tool_preview(False)

        active_view = self._get_active_slide_view()

        if self.tool_mode == "pen":
            active_view.set_tool_preview(
                enabled=True,
                color="#ff3b30",
                radius_px=max(3.0, self.pen_size / 2),
                pos_norm=self.overlay_pointer_pos_norm,
            )
        elif self.tool_mode == "eraser":
            active_view.set_tool_preview(
                enabled=True,
                color="#111111",
                radius_px=max(4.0, float(self.eraser_size)),
                pos_norm=self.overlay_pointer_pos_norm,
            )

    def _update_projector(self) -> None:
        if self.projector_window is None:
            return

        drawings = self._get_page_drawings(self.projector_page_index) if self.drawings_visible else []

        pointer_enabled = False
        pointer_pos = None
        pointer_radius = float(self.pointer_size)

        spotlight_enabled = False
        spotlight_pos = None
        spotlight_radius = float(self.spotlight_size)

        zoom_viewport = self.projector_zoom_viewport_norm

        if not self.is_frozen:
            if self.tool_mode == "pointer" and self.overlay_pointer_pos_norm is not None:
                pointer_enabled = True
                pointer_pos = self.overlay_pointer_pos_norm
            elif self.tool_mode == "spotlight" and self.overlay_pointer_pos_norm is not None:
                spotlight_enabled = True
                spotlight_pos = self.overlay_pointer_pos_norm
        else:
            pointer_enabled = False
            spotlight_enabled = False

        self.projector_window.display_page(
            self.projector_page_index,
            black=self.is_black,
            drawings=drawings,
            drawings_visible=self.drawings_visible,
            pointer_enabled=pointer_enabled,
            pointer_pos_norm=pointer_pos,
            pointer_radius_px=pointer_radius,
            spotlight_enabled=spotlight_enabled,
            spotlight_pos_norm=spotlight_pos,
            spotlight_radius_px=spotlight_radius,
            zoom_viewport_norm=zoom_viewport,
        )

    def _render(self, view: SlideView, page_index: int, region: str, apply_zoom: bool = False) -> None:
        w = max(view.width(), 100)
        h = max(view.height(), 100)

        viewport = self.control_zoom_viewport_norm if apply_zoom else None

        scale_factor = 1.0
        if viewport is not None:
            _, _, vw, vh = viewport
            if vw > 0.0 and vh > 0.0:
                scale_factor = min(3.0, max(1.0 / vw, 1.0 / vh))

        render_w = int(w * scale_factor)
        render_h = int(h * scale_factor)

        screen = self.windowHandle().screen() if self.windowHandle() else None
        dpr = screen.devicePixelRatio() if screen else 1.0

        rendered = self.pdf_loader.render_page_region(
            page_index=page_index,
            region=region,
            target_width=max(render_w, 100),
            target_height=max(render_h, 100),
            device_pixel_ratio=dpr,
        )
        view.set_slide_pixmap(rendered.pixmap)

    def _update_current_tool_cursor(self) -> None:
        for panel_key in PANEL_KEYS:
            self._get_panel_widget(panel_key).unsetCursor()