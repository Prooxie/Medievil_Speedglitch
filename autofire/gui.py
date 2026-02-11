from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .autostart import is_enabled as autostart_is_enabled, set_enabled as autostart_set_enabled
from .config import AutofireConfig
from .profile_store import ProfileStore
from .requirements import check_all
from .service import AutofireService
from .theme import apply_dark_theme, apply_light_theme
from .update_checker import fetch_latest_github_release


APP_VERSION = "1.1.4"  # keep in sync with your release tag
GITHUB_OWNER = "Prooxie"
GITHUB_REPO = "Autofire"


class NavButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)


class ProfileNameDialog(QDialog):
    def __init__(self, title: str, default: str = ""):
        super().__init__()
        self.setWindowTitle(title)
        layout = QVBoxLayout()

        self.edit = QLineEdit()
        self.edit.setText(default)
        layout.addWidget(QLabel("Profile name:"))
        layout.addWidget(self.edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def value(self) -> str:
        return self.edit.text().strip()


class UpdateDialog(QDialog):
    def __init__(self, current_version: str, latest_version: str, download_url: str, notes: str):
        super().__init__()
        self.setWindowTitle("Update available")
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Current: {current_version}"))
        layout.addWidget(QLabel(f"Latest: {latest_version}"))

        if notes:
            box = QTextEdit()
            box.setReadOnly(True)
            box.setPlainText(notes)
            box.setMinimumHeight(160)
            layout.addWidget(box)

        btn = QPushButton("Open download page")
        btn.clicked.connect(lambda: QDesktopServices.openUrl(download_url))  # type: ignore[arg-type]
        layout.addWidget(btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)


class OptionsView(QWidget):
    def __init__(self, store: ProfileStore, on_change):
        super().__init__()
        self.store = store
        self.on_change = on_change

        self.chk_start_min = QCheckBox("Start minimized to tray")
        self.chk_autostart = QCheckBox("Auto-start with Windows")
        self.chk_dark = QCheckBox("Dark theme")

        # initialize from settings
        s = self.store.load_settings()
        self.chk_start_min.setChecked(bool(s.get("start_minimized", False)))
        self.chk_dark.setChecked(bool(s.get("dark_theme", True)))
        # Windows only
        self.chk_autostart.setChecked(autostart_is_enabled())

        self.chk_autostart.setEnabled(os.name == "nt")

        form = QFormLayout()
        form.addRow(self.chk_start_min)
        form.addRow(self.chk_autostart)
        form.addRow(self.chk_dark)

        layout = QVBoxLayout()
        title = QLabel("Options")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addStretch(1)
        self.setLayout(layout)

        self.chk_start_min.toggled.connect(self._save)
        self.chk_dark.toggled.connect(self._save)
        self.chk_autostart.toggled.connect(self._save)

    @Slot()
    def _save(self) -> None:
        s = self.store.load_settings()
        s["start_minimized"] = bool(self.chk_start_min.isChecked())
        s["dark_theme"] = bool(self.chk_dark.isChecked())
        self.store.save_settings(s)

        if os.name == "nt":
            try:
                autostart_set_enabled(bool(self.chk_autostart.isChecked()))
            except Exception as e:
                QMessageBox.warning(self, "Autostart", f"Failed to change autostart: {e}")
                self.chk_autostart.setChecked(autostart_is_enabled())

        self.on_change()


class RunView(QWidget):
    def __init__(self, service: AutofireService, store: ProfileStore):
        super().__init__()
        self.service = service
        self.store = store

        title = QLabel("Autofire — Run")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        # Profile UI
        self.cmb_profiles = QComboBox()
        self.btn_new = QPushButton("New")
        self.btn_save = QPushButton("Save")
        self.btn_delete = QPushButton("Delete")

        pbar = QHBoxLayout()
        pbar.addWidget(QLabel("Profile:"))
        pbar.addWidget(self.cmb_profiles, 1)
        pbar.addWidget(self.btn_new)
        pbar.addWidget(self.btn_save)
        pbar.addWidget(self.btn_delete)

        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)

        self.lbl_axis = QLabel("axis: (0.000, 0.000)")
        self.lbl_desired = QLabel("desired: []")
        self.lbl_phase = QLabel("phase: OFF")

        # config widgets
        self.hold = QDoubleSpinBox(); self.hold.setRange(0.001, 1.000); self.hold.setSingleStep(0.005); self.hold.setDecimals(3)
        self.release = QDoubleSpinBox(); self.release.setRange(0.001, 1.000); self.release.setSingleStep(0.001); self.release.setDecimals(3)
        self.deadzone = QDoubleSpinBox(); self.deadzone.setRange(0.0, 0.95); self.deadzone.setSingleStep(0.01); self.deadzone.setDecimals(2)
        self.diag = QDoubleSpinBox(); self.diag.setRange(0.0, 1.0); self.diag.setSingleStep(0.01); self.diag.setDecimals(2)

        self.settle = QDoubleSpinBox(); self.settle.setRange(0.0, 0.25); self.settle.setSingleStep(0.005); self.settle.setDecimals(3)
        self.pause = QDoubleSpinBox(); self.pause.setRange(0.0, 0.50); self.pause.setSingleStep(0.01); self.pause.setDecimals(3)

        self.joy = QSpinBox(); self.joy.setRange(0, 16)
        self.ax_x = QSpinBox(); self.ax_x.setRange(0, 32)
        self.ax_y = QSpinBox(); self.ax_y.setRange(0, 32)

        form = QFormLayout()
        form.addRow("Hold time (s)", self.hold)
        form.addRow("Release time (s)", self.release)
        form.addRow("Deadzone", self.deadzone)
        form.addRow("Diagonal threshold", self.diag)
        form.addRow("Settle time (s)", self.settle)
        form.addRow("Pause after release (s)", self.pause)
        form.addRow("Joystick index", self.joy)
        form.addRow("Axis X index", self.ax_x)
        form.addRow("Axis Y index", self.ax_y)

        controls = QHBoxLayout()
        controls.addWidget(self.btn_start)
        controls.addWidget(self.btn_stop)
        controls.addStretch(1)

        left = QVBoxLayout()
        left.addWidget(title)
        left.addLayout(pbar)
        left.addLayout(controls)
        left.addSpacing(10)
        left.addWidget(self.lbl_axis)
        left.addWidget(self.lbl_desired)
        left.addWidget(self.lbl_phase)
        left.addStretch(1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Configuration"))
        right.addLayout(form)
        right.addStretch(1)

        layout = QHBoxLayout()
        layout.addLayout(left, 2)
        layout.addSpacing(18)
        layout.addLayout(right, 3)
        self.setLayout(layout)

        self.btn_start.clicked.connect(self.service.start)
        self.btn_stop.clicked.connect(self.service.stop)

        for w in (self.hold, self.release, self.deadzone, self.diag, self.settle, self.pause, self.joy, self.ax_x, self.ax_y):
            w.valueChanged.connect(self._push_config)

        self.service.telemetry.connect(self._on_telemetry)
        self.service.running_changed.connect(self._on_running)

        # Profile interactions
        self.btn_new.clicked.connect(self._new_profile)
        self.btn_save.clicked.connect(self._save_profile)
        self.btn_delete.clicked.connect(self._delete_profile)
        self.cmb_profiles.currentTextChanged.connect(self._load_selected_profile)

        self._reload_profiles()
        self._load_selected_profile(self.cmb_profiles.currentText())

    def _reload_profiles(self) -> None:
        names = self.store.list_profiles()
        active = self.store.get_active_profile() or (names[0] if names else "")
        self.cmb_profiles.blockSignals(True)
        self.cmb_profiles.clear()
        self.cmb_profiles.addItems(names)
        if active in names:
            self.cmb_profiles.setCurrentText(active)
        self.cmb_profiles.blockSignals(False)

    @Slot()
    def _new_profile(self) -> None:
        dlg = ProfileNameDialog("Create profile")
        if dlg.exec() != QDialog.Accepted:
            return
        name = dlg.value()
        if not name:
            return
        if name in self.store.list_profiles():
            QMessageBox.warning(self, "Profile", "Profile already exists.")
            return
        cfg = self._read_cfg_from_widgets()
        self.store.save_profile(name, cfg)
        self.store.set_active_profile(name)
        self._reload_profiles()
        self.cmb_profiles.setCurrentText(name)

    @Slot()
    def _save_profile(self) -> None:
        name = self.cmb_profiles.currentText().strip()
        if not name:
            return
        cfg = self._read_cfg_from_widgets()
        self.store.save_profile(name, cfg)
        self.store.set_active_profile(name)

    @Slot()
    def _delete_profile(self) -> None:
        name = self.cmb_profiles.currentText().strip()
        if not name or name == "default":
            QMessageBox.information(self, "Profile", "Default profile cannot be deleted.")
            return
        if QMessageBox.question(self, "Delete", f"Delete profile '{name}'?") != QMessageBox.Yes:
            return
        self.store.delete_profile(name)
        # fall back to default
        self.store.set_active_profile("default")
        self._reload_profiles()
        self.cmb_profiles.setCurrentText(self.store.get_active_profile() or "default")

    @Slot(str)
    def _load_selected_profile(self, name: str) -> None:
        if not name:
            return
        cfg = self.store.load_profile(name)
        self.store.set_active_profile(name)
        self._apply_cfg_to_widgets(cfg)
        self.service.set_config(**asdict(cfg))

    def _apply_cfg_to_widgets(self, cfg: AutofireConfig) -> None:
        for w in (self.hold, self.release, self.deadzone, self.diag, self.settle, self.pause, self.joy, self.ax_x, self.ax_y):
            w.blockSignals(True)

        self.hold.setValue(cfg.hold_time)
        self.release.setValue(cfg.release_time)
        self.deadzone.setValue(cfg.deadzone)
        self.diag.setValue(cfg.diagonal_threshold)
        self.settle.setValue(cfg.settle_time)
        self.pause.setValue(cfg.pause_after_release)
        self.joy.setValue(cfg.joystick_index)
        self.ax_x.setValue(cfg.axis_x_index)
        self.ax_y.setValue(cfg.axis_y_index)

        for w in (self.hold, self.release, self.deadzone, self.diag, self.settle, self.pause, self.joy, self.ax_x, self.ax_y):
            w.blockSignals(False)

    def _read_cfg_from_widgets(self) -> AutofireConfig:
        return AutofireConfig(
            hold_time=float(self.hold.value()),
            release_time=float(self.release.value()),
            deadzone=float(self.deadzone.value()),
            diagonal_threshold=float(self.diag.value()),
            settle_time=float(self.settle.value()),
            pause_after_release=float(self.pause.value()),
            joystick_index=int(self.joy.value()),
            axis_x_index=int(self.ax_x.value()),
            axis_y_index=int(self.ax_y.value()),
        )

    @Slot(bool)
    def _on_running(self, running: bool) -> None:
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    @Slot(dict)
    def _on_telemetry(self, t: Dict[str, Any]) -> None:
        x = float(t.get("axis_x", 0.0))
        y = float(t.get("axis_y", 0.0))
        self.lbl_axis.setText(f"axis: ({x:+.3f}, {y:+.3f})")
        self.lbl_desired.setText(f"desired: {t.get('desired', [])}")
        self.lbl_phase.setText(f"phase: {t.get('phase', 'OFF')}")

    @Slot()
    def _push_config(self) -> None:
        cfg = self._read_cfg_from_widgets()
        self.service.set_config(**asdict(cfg))


class PlaceholderView(QWidget):
    def __init__(self, title: str, subtitle: str):
        super().__init__()
        layout = QVBoxLayout()
        h = QLabel(title); h.setStyleSheet("font-size: 18px; font-weight: 600;")
        s = QLabel(subtitle); s.setStyleSheet("color: #666;")
        layout.addWidget(h)
        layout.addWidget(s)
        layout.addStretch(1)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self, store: ProfileStore):
        super().__init__()
        self.store = store
        self.setWindowTitle("Autofire (PySide6)")
        self.resize(1000, 600)

        # service initialized from active profile
        active = self.store.get_active_profile() or "default"
        cfg = self.store.load_profile(active)
        self.service = AutofireService(cfg)

        nav = QVBoxLayout()
        nav.setContentsMargins(10, 10, 10, 10)
        nav.setSpacing(8)

        self.btn_run = NavButton("Run")
        self.btn_options = NavButton("Options")
        self.btn_config = NavButton("Configuration")
        self.btn_stream = NavButton("Streamer mode")

        nav.addWidget(self.btn_run)
        nav.addWidget(self.btn_options)
        nav.addWidget(self.btn_config)
        nav.addWidget(self.btn_stream)
        nav.addStretch(1)

        nav_frame = QFrame()
        nav_frame.setFrameShape(QFrame.StyledPanel)
        nav_frame.setLayout(nav)
        nav_frame.setFixedWidth(190)

        self.pages = QStackedWidget()
        self.pages.addWidget(RunView(self.service, self.store))
        self.pages.addWidget(OptionsView(self.store, self._apply_options))
        self.pages.addWidget(PlaceholderView("Configuration", "Planned: advanced policies + device diagnostics"))
        self.pages.addWidget(PlaceholderView("Streamer mode", "Planned: overlay + minimal UI"))

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(160)
        self.service.log.connect(self.log.append)

        main = QWidget()
        root = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(nav_frame)
        top.addWidget(self.pages, 1)
        root.addLayout(top, 1)
        root.addWidget(self.log)
        main.setLayout(root)
        self.setCentralWidget(main)

        self.btn_run.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_options.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_config.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_stream.clicked.connect(lambda: self.pages.setCurrentIndex(3))

        self._setup_tray()
        self._apply_options()
        self._startup_checks()

        self.log.append("Ready. (Close = hide to tray)")

    # ---------- Tray ----------
    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        from pathlib import Path
        icon_path = Path(__file__).parent / "icon.png"
        self.tray.setIcon(QIcon(str(icon_path)))

        menu = QMenu()
        act_show = QAction("Show", self)
        act_hide = QAction("Hide", self)
        act_start = QAction("Start", self)
        act_stop = QAction("Stop", self)
        act_quit = QAction("Quit", self)

        act_show.triggered.connect(self.show_normal)
        act_hide.triggered.connect(self.hide_to_tray)
        act_start.triggered.connect(self.service.start)
        act_stop.triggered.connect(self.service.stop)
        act_quit.triggered.connect(self._quit_app)

        menu.addAction(act_show)
        menu.addAction(act_hide)
        menu.addSeparator()
        menu.addAction(act_start)
        menu.addAction(act_stop)
        menu.addSeparator()
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    @Slot()
    def show_normal(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    @Slot()
    def hide_to_tray(self) -> None:
        self.hide()
        try:
            self.tray.showMessage("Autofire", "Running in system tray.", QSystemTrayIcon.Information, 1500)
        except Exception:
            pass

    @Slot()
    def _quit_app(self) -> None:
        try:
            self.service.shutdown()
        finally:
            QApplication.instance().quit()  # type: ignore[call-arg]

    @Slot(QSystemTrayIcon.ActivationReason)
    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_normal()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        event.ignore()
        self.hide_to_tray()

    # ---------- Options ----------
    def _apply_options(self) -> None:
        s = self.store.load_settings()
        dark = bool(s.get("dark_theme", True))
        app = QApplication.instance()
        if app:
            if dark:
                apply_dark_theme(app)
            else:
                apply_light_theme(app)

    # ---------- Startup checks ----------
    def _startup_checks(self) -> None:
        # requirements
        statuses = check_all()
        bad = [r for r in statuses if not r.ok]
        if bad:
            msg = "\n".join([f"- {r.title}: {r.detail}" for r in bad])
            QMessageBox.warning(self, "Missing requirements", msg)

        # update check (best effort; can fail offline)
        s = self.store.load_settings()
        if bool(s.get("check_updates", True)):
            info = fetch_latest_github_release(GITHUB_OWNER, GITHUB_REPO)
            if info and info.latest_version and info.latest_version != APP_VERSION:
                dlg = UpdateDialog(APP_VERSION, info.latest_version, info.download_url, info.notes)
                dlg.exec()


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    store = ProfileStore()

    # Apply theme before window
    s = store.load_settings()
    if bool(s.get("dark_theme", True)):
        apply_dark_theme(app)
    else:
        apply_light_theme(app)

    w = MainWindow(store)

    # Start minimized?
    if bool(s.get("start_minimized", False)):
        w.hide_to_tray()
    else:
        w.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
