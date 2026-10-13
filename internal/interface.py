from PySide6.QtCore import (
    QEvent,
    QObject,
    QThread,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QFontDatabase,
    QIcon,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import subprocess
import sys

import internal.resources_rc
from internal.lang import gt
import internal.config
from internal.downloading import text_game, DownloadGameRunner, local_component_directory
from internal.paths import game_command, normalize_game_directory, remember_game_directory
from internal.processes import external_program_environment

def init_fonts():
    fonts = {}
    for name in [
        ":/font/title.ttf",
        ":/font/body.ttf",
    ]:
        fonts[name] = QFontDatabase.addApplicationFont(name)
        if fonts[name] != -1:
            print(f"Loaded font \"{name}\" with names {QFontDatabase.applicationFontFamilies(fonts[name])}")
        else:
            print(f"Could not find font \"{name}\"!")

class GameRunner(QThread):
    failed = Signal(str)

    def __init__(self, parent, args, visible, game_directory):
        super().__init__(parent)
        self.args = args
        self.visible = visible
        self.game_directory = str(game_directory)

    def run(self):
        kwargs = {"cwd": self.game_directory, "env": external_program_environment()}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE if self.visible else subprocess.CREATE_NO_WINDOW
        try:
            subprocess.run(self.args, **kwargs)
        except OSError as error:
            self.failed.emit(str(error))


class GameStatusRunner(QThread):
    result = Signal(str, list, str)

    def __init__(self, parent, game_directory):
        super().__init__(parent)
        self.game_directory = str(game_directory)

    def run(self):
        try:
            message, arguments = text_game(self.game_directory)
        except Exception as error:
            message, arguments = "Cannot check game components: {0}", [str(error)]
        self.result.emit(message, arguments, self.game_directory)

class StatusController(QObject):
    def __init__(self, label: QLabel):
        super().__init__()
        self.label = label

    @Slot(str, list)
    def set_label_text(self, fmt, args):
        self.label.setStyleSheet("""
            QLabel { font-size: 20px; color: #ff0; }
        """)
        self.label.setText(gt(fmt).format(*args))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._busy = False
        self._status_thread = None
        self._status_again = False
        self._close_requested = False
        self._install_error = None

        self.setWindowTitle(gt("Tiny Bunny Mod Manager"))
        self.setWindowIcon(QIcon(":/img/icon.ico"))
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #dcdcdc; font-family: "Kazmann Sans"; font-size: 24px; }

            QPushButton { background-color: rgba(255,255,255,0.05); border: 4px outset rgba(32,32,32,1.0); padding: 8px 32px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.15); border: 4px outset rgba(32,32,32,1.0); }
            QPushButton:pressed { background-color: rgba(255,255,255,0.05); border: 4px inset rgba(32,32,32,1.0); }
            QPushButton:disabled { color: #333; border: 4px inset rgba(16,16,16,1.0); }

            QCheckBox:hover { color: #999; }
            QCheckBox:pressed { color: #888; }
            QCheckBox:disabled { color: #333; }

            QCheckBox::indicator { width: 12px; height: 12px; border: 1px solid #333; background: #666; }
            QCheckBox::indicator:hover { background: #333; }
            QCheckBox::indicator:pressed { background: #555; }
            QCheckBox::indicator:checked { image: url(:/img/check.png); }
        """)

        # Main Layout and Logo
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setContentsMargins(64,32,64,32)
        self.main_layout.setSpacing(8)

        lbl = QLabel(self)
        lbl.setStyleSheet("""
            QLabel { font-size: 48px; }
        """)
        lbl.setText(gt("Tiny Bunny Mod Manager"))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(lbl)

        game_layout = QHBoxLayout()
        self.lbl_game_path = QLabel()
        self.lbl_game_path.setMaximumWidth(620)
        self.lbl_game_path.setStyleSheet("QLabel { font-size: 20px; }")
        self.btn_select_game = QPushButton(gt("Choose game folder"))
        self.btn_select_game.clicked.connect(self._select_game)
        game_layout.addWidget(self.lbl_game_path)
        game_layout.addWidget(self.btn_select_game)
        self.main_layout.addLayout(game_layout)
        self._update_game_path()

        # CheckBoxes
        layout_cb = QHBoxLayout()
        layout_cb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cb_developer = QCheckBox()
        self.cb_console = QCheckBox()
        self.cb_extconsole = QCheckBox()
        for var, text, tt in [
            (self.cb_developer,     "Developer mode",   "Game will have developer mode enabled (config.developer)."),
            (self.cb_console,       "In-game console",  "Game will have in-game console enabled (config.console)."),
            (self.cb_extconsole,    "External console", "Game will launch with external console enabled, allowing easier debugging of mods."),
        ]:
            var.setText(gt(text))
            var.setToolTip(gt(tt))
            layout_cb.addWidget(var)
        self.main_layout.addLayout(layout_cb)
        self.main_layout.addSpacing(8)

        # Buttons
        layout_btn = QHBoxLayout()
        layout_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_game = QPushButton()
        self.btn_install = QPushButton()
        for var, func, text, tt in [
            (self.btn_game,     self._start_game,      "Launch the game!",         "Will start the game with selected features."),
            (self.btn_install,  self._start_install,   "Install game components",  "Will install game components of the manager."),
        ]:
            var.setText(gt(text))
            var.setToolTip(gt(tt))
            var.clicked.connect(func)
            layout_btn.addWidget(var)
        self.main_layout.addLayout(layout_btn)

        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet("""
            QLabel { font-size: 20px; }
        """)
        self.lbl_status.setText("\n")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumHeight(64)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.lbl_status)

        self.setFixedSize(self.layout().sizeHint())

        self.update_status()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_game_options()

    def _load_game_options(self):
        config_values = internal.config.load()

        self.cb_developer.setChecked(config_values[0])
        self.cb_console.setChecked(config_values[1])
        self.cb_extconsole.setChecked(config_values[2])

    def update_status(self):
        if self._busy:
            return
        if self._status_thread is not None:
            self._status_again = True
            return
        self._status_thread = GameStatusRunner(self, internal.config.working_path)
        self._status_thread.result.connect(self._set_game_status)
        self._status_thread.finished.connect(self._status_finished)
        self._status_thread.finished.connect(self._status_thread.deleteLater)
        self._status_thread.start()

    @Slot(str, list, str)
    def _set_game_status(self, message, arguments, game_directory):
        if self._busy or game_directory != str(internal.config.working_path):
            return
        self.lbl_status.setStyleSheet(f"""
            QLabel {{ font-size: 20px; color: {"#c33" if arguments == [None] else "#dcdcdc"}; }}
        """)
        self.lbl_status.setText(gt(message).format(*arguments))

    @Slot()
    def _status_finished(self):
        self._status_thread = None
        if self._close_requested and not self._busy:
            self.close()
        elif self._status_again:
            self._status_again = False
            self.update_status()

    def _update_game_path(self):
        path = str(internal.config.working_path)
        self.lbl_game_path.setText(self.lbl_game_path.fontMetrics().elidedText(path, Qt.TextElideMode.ElideMiddle, 620))
        self.lbl_game_path.setToolTip(path)

    def _select_game(self):
        selected = QFileDialog.getExistingDirectory(self, gt("Choose Tiny Bunny folder"), str(internal.config.working_path))
        if not selected:
            return
        root = normalize_game_directory(selected)
        try:
            if root is None:
                raise ValueError(gt("The program could not find Tiny Bunny game folder!"))
            game_command(root)
            internal.config.save(self.cb_developer.isChecked(), self.cb_console.isChecked(), self.cb_extconsole.isChecked())
            remember_game_directory(root)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, gt("Error!"), str(error))
            return
        internal.config.working_path = str(root)
        self._update_game_path()
        self._load_game_options()
        try:
            if local_component_directory(root) is not None:
                self._start_install()
                return
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, gt("Error!"), str(error))
        self.update_status()

    def _start_game(self):

        try:
            internal.config.save(self.cb_developer.isChecked(), self.cb_console.isChecked(), self.cb_extconsole.isChecked())
            args = game_command(internal.config.working_path, self.cb_extconsole.isChecked())
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, gt("Error!"), str(error))
            return
        self.process = GameRunner(self, args, self.cb_extconsole.isChecked(), internal.config.working_path)
        self.process.failed.connect(self._game_failed)
        self.process.finished.connect(self._on_finish_game)
        self.hide()
        self.process.start()

    @Slot(str)
    def _game_failed(self, error):
        self.show()
        QMessageBox.critical(self, gt("Error!"), gt("Game launch failed: {0}").format(error))

    def _on_finish_game(self):
        self.process.deleteLater()
        self.process = None
        if self._close_requested:
            self.close()
        else:
            self.show()

    def _start_install(self):

        if self._busy:
            return
        self._busy = True
        self._install_error = None
        self._set_controls_enabled(False)

        self.thread = QThread()
        self.worker = DownloadGameRunner(internal.config.working_path)
        self.status_controller = StatusController(self.lbl_status)
        self.worker.moveToThread(self.thread)

        self.worker.status.connect(self.status_controller.set_label_text)
        self.worker.finished.connect(self._install_worker_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._on_finish_install)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    @Slot()
    def _install_worker_finished(self):
        self._install_error = self.worker.error

    @Slot()
    def _on_finish_install(self):
        self._busy = False
        self._set_controls_enabled(True)
        if self._close_requested:
            self.close()
        elif self._install_error is None:
            self.update_status()

    def _set_controls_enabled(self, enabled):
        for control in (self.cb_console, self.cb_developer, self.cb_extconsole,
                        self.btn_game, self.btn_install, self.btn_select_game):
            control.setEnabled(enabled)

    def closeEvent(self, event: QEvent):
        if self._busy or self._status_thread is not None or getattr(self, "process", None) is not None:
            self._close_requested = True
            event.ignore()
            return
        try:
            internal.config.save(self.cb_developer.isChecked(), self.cb_console.isChecked(), self.cb_extconsole.isChecked())
        except OSError as error:
            QMessageBox.critical(self, gt("Error!"), str(error))
            event.ignore()
            return
        event.accept()
