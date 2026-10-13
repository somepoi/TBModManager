from PySide6.QtCore import (
    QEvent,
    QObject,
    QThread,
    QThreadPool,
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
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pathlib import Path
import subprocess

import internal.resources_rc
from internal.lang import gt
import internal.config
from internal.downloading import text_game, DownloadGameRunner

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
    finished = Signal()

    def __init__(self, parent, args, visible):
        super().__init__(parent)
        self.args = args
        self.visible = visible

    def run(self):
        subprocess.run(self.args, creationflags=subprocess.CREATE_NEW_CONSOLE if self.visible else subprocess.CREATE_NO_WINDOW)
        self.finished.emit()

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
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.lbl_status)

        self.setFixedSize(self.layout().sizeHint())

        self.download_thread = QThread()
        self.download_threadpool = QThreadPool()

        self.update_status()

    def showEvent(self, event):

        config_values = internal.config.load()

        self.cb_developer.setChecked(config_values[0])
        self.cb_console.setChecked(config_values[1])
        self.cb_extconsole.setChecked(config_values[2])

    def update_status(self):

        game_version = text_game()
        self.lbl_status.setStyleSheet(f"""
            QLabel {{ font-size: 20px; color: {"#c33" if game_version[1] == [None] else "#dcdcdc"}; }}
        """)
        self.lbl_status.setText(gt(game_version[0]).format(*game_version[1]))

    def _start_game(self):

        internal.config.save(self.cb_developer.isChecked(), self.cb_console.isChecked(), self.cb_extconsole.isChecked())

        args = [str(Path(internal.config.working_path) / "lib" / "py3-windows-x86_64" / ("python.exe" if self.cb_extconsole.isChecked() else "pythonw.exe")), str(Path(internal.config.working_path) / "TinyBunny.py")]

        self.process = GameRunner(self, args, self.cb_extconsole.isChecked())
        self.process.finished.connect(self._on_finish_game)
        self.hide()
        self.process.run()

    def _on_finish_game(self):
        self.show()

    def _start_install(self):

        [obj.setEnabled(False) for obj in [self.cb_console, self.cb_developer, self.cb_extconsole, self.btn_game, self.btn_install]]

        self.thread = QThread()
        self.worker = DownloadGameRunner()
        self.status_controller = StatusController(self.lbl_status)
        self.worker.moveToThread(self.thread)

        self.worker.status.connect(self.status_controller.set_label_text)
        self.worker.finished.connect(self._on_finish_install)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _on_finish_install(self):

        [obj.setEnabled(True) for obj in [self.cb_console, self.cb_developer, self.cb_extconsole, self.btn_game, self.btn_install]]
        if self.worker.error is None:
            self.update_status()

    def closeEvent(self, event: QEvent):
        internal.config.save(self.cb_developer.isChecked(), self.cb_console.isChecked(), self.cb_extconsole.isChecked())
