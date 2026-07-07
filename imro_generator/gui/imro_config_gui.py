import sys
import os
import json
from pathlib import Path
from typing import Optional, List, Tuple

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QCheckBox, QRadioButton, QPushButton, QButtonGroup,
    QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QGraphicsRectItem,
    QMenu, QAction
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIntValidator, QDesktopServices

import pyqtgraph as pg
import numpy as np

from imro_generator.core.imro_generator import ImroGenerator


class ImroConfigGUI(QMainWindow):
    """NP1.0 probe channel configuration GUI."""

    CONFIG_FILE = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
        'imro_config.json'
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Npx Channels Configuration")
        self.setGeometry(100, 100, 400, 700)

        # Initialize probe settings
        self.imro_gen = ImroGenerator('npx1.0-nhp')
        self.max_depth_mm = self.imro_gen.max_depth / 1000.0

        # Load saved config
        self.config = self._load_config()
        self.last_directory = self.config.get('last_directory', os.path.expanduser('~'))

        # Current channel configuration
        self.current_channels: List[int] = []

        # Setup UI
        self._setup_ui()

        # Apply styling
        self._apply_styling()

        # Show full probe initially
        self._show_full_probe()

    def _load_config(self) -> dict:
        """Load configuration from file."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def _apply_styling(self) -> None:
        """Apply white background and dark green font styling."""
        stylesheet = """
        QMainWindow {
            background-color: white;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QWidget {
            background-color: white;
            color: #1a5c1a;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QLabel {
            color: #1a5c1a;
        }
        QGroupBox {
            color: #1a5c1a;
            border: 1px solid #1a5c1a;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-family: "Helvetica", monospace;
            font-size: 13px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QComboBox {
            color: #1a5c1a;
            background-color: white;
            border: 1px solid #1a5c1a;
            padding: 2px;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            color: #1a5c1a;
            selection-background-color: #90EE90;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QSpinBox, QDoubleSpinBox {
            color: #1a5c1a;
            background-color: white;
            border: 1px solid #1a5c1a;
            padding: 2px;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QPushButton {
            color: #1a5c1a;
            background-color: #F0F0F0;
            border: 1px solid #1a5c1a;
            padding: 5px;
            border-radius: 3px;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #E0E0E0;
        }
        QPushButton:pressed {
            background-color: #D0D0D0;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QRadioButton, QCheckBox {
            color: #1a5c1a;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QRadioButton::indicator, QCheckBox::indicator {
            width: 13px;
            height: 13px;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QMenu {
            background-color: white;
            color: #1a5c1a;
            border: 1px solid #1a5c1a;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QMenu::item:selected {
            background-color: #90EE90;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QMessageBox {
            background-color: white;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QMessageBox QLabel {
            color: #1a5c1a;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        QFileDialog {
            background-color: white;
            font-family: "Helvetica", monospace;
            font-size: 11px;
        }
        """
        self.setStyleSheet(stylesheet)

    def _setup_ui(self) -> None:
        """Setup main UI."""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create menu bar
        self._create_menu_bar()

        # Content area (split: left settings, right visualization)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Left side: settings + channel selection (stacked, constrained width)
        left_container = QWidget()
        left_container.setMaximumWidth(350)
        left_layout_internal = QVBoxLayout(left_container)
        self._create_settings_group(left_layout_internal)
        self._create_channel_selection_group(left_layout_internal)
        left_layout_internal.addStretch()
        content_layout.addWidget(left_container, stretch=0)

        # Right side: probe visualization (full height)
        self._create_probe_canvas(content_layout)

        main_layout.addLayout(content_layout, stretch=1)

        self.setCentralWidget(main_widget)

    def _create_menu_bar(self) -> None:
        """Create main menu bar."""
        menubar = self.menuBar()

        # Probe menu
        probe_menu = menubar.addMenu("Probe")
        change_probe_menu = probe_menu.addMenu("Change Probe")

        # Get available probes
        probes_dir = Path(__file__).parent.parent / 'settings' / 'probes'
        if probes_dir.exists():
            for probe_folder in sorted(probes_dir.iterdir()):
                if probe_folder.is_dir() and (probe_folder / 'probe.json').exists():
                    probe_name = probe_folder.name
                    action = QAction(probe_name, self)
                    action.triggered.connect(lambda checked, pn=probe_name: self._switch_probe(pn))
                    change_probe_menu.addAction(action)

        # Map menu
        map_menu = menubar.addMenu("Map")

        load_imro_action = QAction("Load IMRO", self)
        load_imro_action.triggered.connect(self.load_imro)
        map_menu.addAction(load_imro_action)

        save_imro_action = QAction("Save IMRO", self)
        save_imro_action.triggered.connect(self.save_imro)
        map_menu.addAction(save_imro_action)

        save_json_action = QAction("Save Kilosort Probe", self)
        save_json_action.triggered.connect(self.save_kilosort_probe)
        map_menu.addAction(save_json_action)

        map_menu.addSeparator()

        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self.reset_to_defaults)
        map_menu.addAction(reset_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        # Documentation links
        ephys_action = QAction("OpenEphys Neuropixels Plugin", self)
        ephys_action.triggered.connect(lambda: self._open_url("https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Neuropixels-PXI.html"))
        help_menu.addAction(ephys_action)

        imro_action = QAction("IMRO Format Documentation", self)
        imro_action.triggered.connect(lambda: self._open_url("https://billkarsh.github.io/SpikeGLX/help/imroTables/"))
        help_menu.addAction(imro_action)

        kilosort_action = QAction("Kilosort Probe Dictionary", self)
        kilosort_action.triggered.connect(lambda: self._open_url("https://kilosort.readthedocs.io/en/latest/tutorials/make_probe.html"))
        help_menu.addAction(kilosort_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _switch_probe(self, probe_name: str) -> None:
        """Switch to a different probe."""
        try:
            self.imro_gen = ImroGenerator(probe_name)
            self.max_depth_mm = self.imro_gen.max_depth / 1000.0
            self.config['current_probe'] = probe_name
            self._save_config()

            # Reset display
            self._show_full_probe()
            self.current_channels = []

            QMessageBox.information(self, "Probe Changed", f"Switched to probe: {probe_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch probe: {str(e)}")

    def _open_url(self, url: str) -> None:
        """Open URL in default browser."""
        QDesktopServices.openUrl(QUrl(url))

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.information(
            self,
            "About Npx Channels Configuration",
            "IMRO Channel Configuration Tool\nVersion 0.1.0\n\nFor Neuropixels probes"
        )

    def _create_settings_group(self, layout: QVBoxLayout) -> None:
        """Create global settings group."""
        group = QGroupBox("Global Settings")
        group_layout = QVBoxLayout()

        # AP Gain
        group_layout.addWidget(QLabel("AP Gain:"))
        self.ap_gain_combo = QComboBox()
        gains = [50, 125, 250, 500, 1000, 1500, 2000, 3000]
        self.ap_gain_combo.addItems([str(g) for g in gains])
        self.ap_gain_combo.setCurrentText("500")
        group_layout.addWidget(self.ap_gain_combo)

        # LF Gain
        group_layout.addWidget(QLabel("LF Gain:"))
        self.lf_gain_combo = QComboBox()
        self.lf_gain_combo.addItems([str(g) for g in gains])
        self.lf_gain_combo.setCurrentText("250")
        group_layout.addWidget(self.lf_gain_combo)

        # Reference type
        group_layout.addWidget(QLabel("Reference:"))
        self.ref_type_group = QButtonGroup()
        self.ref_external_radio = QRadioButton("External")
        self.ref_tip_radio = QRadioButton("Tip (on-probe)")
        self.ref_external_radio.setChecked(False)
        self.ref_tip_radio.setChecked(True)
        self.ref_type_group.addButton(self.ref_external_radio, 0)
        self.ref_type_group.addButton(self.ref_tip_radio, 1)
        group_layout.addWidget(self.ref_external_radio)
        group_layout.addWidget(self.ref_tip_radio)
        self.ref_tip_radio.toggled.connect(self._on_ref_type_changed)

        # Reference mode (if tip selected)
        self.ref_mode_group = QButtonGroup()
        ref_mode_layout = QVBoxLayout()
        ref_mode_layout.addWidget(QLabel("Ref mode:"))
        self.ref_own_radio = QRadioButton("Each bank own ref")
        self.ref_same_radio = QRadioButton("All same, bank:")
        self.ref_own_radio.setChecked(True)
        self.ref_mode_group.addButton(self.ref_own_radio, 0)
        self.ref_mode_group.addButton(self.ref_same_radio, 1)
        ref_mode_layout.addWidget(self.ref_own_radio)
        ref_mode_layout.addWidget(self.ref_same_radio)

        # Reference bank selector
        ref_bank_layout = QHBoxLayout()
        ref_bank_layout.addWidget(QLabel("Bank:"))
        self.ref_bank_combo = QComboBox()
        self.ref_bank_combo.addItems([str(i) for i in range(self.imro_gen.total_banks)])
        self.ref_bank_combo.setCurrentText("0")
        self.ref_bank_combo.setEnabled(False)
        self.ref_same_radio.toggled.connect(lambda: self.ref_bank_combo.setEnabled(self.ref_same_radio.isChecked()))
        ref_bank_layout.addWidget(self.ref_bank_combo)
        ref_mode_layout.addLayout(ref_bank_layout)

        self.ref_mode_container = QWidget()
        self.ref_mode_container.setLayout(ref_mode_layout)
        self.ref_mode_container.setVisible(False)
        group_layout.addWidget(self.ref_mode_container)

        # AP Filter
        self.ap_filter_check = QCheckBox("AP Filter (ON)")
        self.ap_filter_check.setChecked(True)
        group_layout.addWidget(self.ap_filter_check)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def _create_channel_selection_group(self, layout: QVBoxLayout) -> None:
        """Create channel selection group with depth range in mm."""
        group = QGroupBox("Channel Selection")
        group_layout = QVBoxLayout()

        # Depth range in mm
        group_layout.addWidget(QLabel("Depth Range (mm):"))

        depth_min_layout = QHBoxLayout()
        depth_min_layout.addWidget(QLabel("Min:"))
        self.depth_min_spin = QDoubleSpinBox()
        self.depth_min_spin.setMinimum(-999999.0)
        self.depth_min_spin.setMaximum(999999.0)
        self.depth_min_spin.setValue(0.0)
        self.depth_min_spin.setSingleStep(0.1)
        self.depth_min_spin.setDecimals(2)
        self.depth_min_spin.valueChanged.connect(self._on_depth_changed)
        depth_min_layout.addWidget(self.depth_min_spin)
        group_layout.addLayout(depth_min_layout)

        depth_max_layout = QHBoxLayout()
        depth_max_layout.addWidget(QLabel("Max:"))
        self.depth_max_spin = QDoubleSpinBox()
        self.depth_max_spin.setMinimum(-999999.0)
        self.depth_max_spin.setMaximum(999999.0)
        self.depth_max_spin.setValue(self.max_depth_mm)
        self.depth_max_spin.setSingleStep(0.1)
        self.depth_max_spin.setDecimals(2)
        self.depth_max_spin.valueChanged.connect(self._on_depth_changed)
        depth_max_layout.addWidget(self.depth_max_spin)
        group_layout.addLayout(depth_max_layout)

        # Assignment mode
        group_layout.addWidget(QLabel("Assignment Mode:"))
        self.assignment_group = QButtonGroup()
        self.assignment_striped_radio = QRadioButton("Striped")
        self.assignment_mixed_radio = QRadioButton("Mixed")
        self.assignment_striped_radio.setChecked(False)
        self.assignment_mixed_radio.setChecked(True)
        self.assignment_group.addButton(self.assignment_striped_radio, 0)
        self.assignment_group.addButton(self.assignment_mixed_radio, 1)
        group_layout.addWidget(self.assignment_striped_radio)
        group_layout.addWidget(self.assignment_mixed_radio)

        # Generate button
        self.generate_btn = QPushButton("Generate Channels")
        self.generate_btn.clicked.connect(self.generate_channels)
        group_layout.addWidget(self.generate_btn)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def _create_probe_canvas(self, layout: QHBoxLayout) -> None:
        """Create PyQtGraph probe visualization showing all 4416 electrodes."""
        # Create container widget (sized to match left panel)
        container = QWidget()
        container.setMinimumWidth(200)
        container.setMinimumHeight(600)
        container.setMaximumWidth(200)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        
        self.plot_widget.setLabel('left', 'Depth (µm)', units='')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.showGrid(False, False)
        self.plot_widget.setBackground(pg.mkColor(255,255,255))  # Match window color

        # Disable auto-ranging and x-axis interactions
        self.plot_widget.enableAutoRange(False)
        self.plot_widget.getViewBox().setMouseEnabled(x=False, y=True)

        # Set axis limits to show full probe using actual dimensions from CSV
        max_y = self.imro_gen.max_depth
        self.plot_widget.setXRange(-60, 160, padding=0)
        self.plot_widget.setYRange(0, max_y + 1000, padding=0)

        # Add draggable depth cursors (mm -> µm conversion)
        depth_min_um = self.depth_min_spin.value() * 1000
        depth_max_um = self.depth_max_spin.value() * 1000

        self.depth_min_cursor = pg.InfiniteLine(
            pos=depth_min_um, angle=0, movable=True,
            pen=pg.mkPen(color='red', width=2, style=Qt.SolidLine)
        )
        self.depth_max_cursor = pg.InfiniteLine(
            pos=depth_max_um, angle=0, movable=True,
            pen=pg.mkPen(color='blue', width=2, style=Qt.SolidLine)
        )

        self.depth_min_cursor.setCursor(pg.QtGui.QCursor(pg.QtCore.Qt.OpenHandCursor))
        self.depth_max_cursor.setCursor(pg.QtGui.QCursor(pg.QtCore.Qt.OpenHandCursor))

        self.depth_min_cursor.sigPositionChanged.connect(self._on_cursor_min_moved)
        self.depth_max_cursor.sigPositionChanged.connect(self._on_cursor_max_moved)

        self.plot_widget.addItem(self.depth_min_cursor)
        self.plot_widget.addItem(self.depth_max_cursor)

        container_layout.addWidget(self.plot_widget)

        # Reset view button
        self.reset_view_btn = QPushButton("Reset View")
        self.reset_view_btn.clicked.connect(self._reset_view)
        container_layout.addWidget(self.reset_view_btn)

        layout.addWidget(container, stretch=0)

    def _on_ref_type_changed(self) -> None:
        """Handle reference type change (ref_mode_container always hidden)."""
        pass

    def _on_depth_changed(self) -> None:
        """Handle depth range change from spinboxes."""
        depth_min_mm = self.depth_min_spin.value()
        depth_max_mm = self.depth_max_spin.value()

        # Update cursor positions (convert mm to µm)
        depth_min_um = depth_min_mm * 1000
        depth_max_um = depth_max_mm * 1000
        self.depth_min_cursor.setPos(depth_min_um)
        self.depth_max_cursor.setPos(depth_max_um)

    def _on_cursor_min_moved(self) -> None:
        """Handle min depth cursor movement."""
        depth_min_um = self.depth_min_cursor.pos().y()
        depth_min_mm = depth_min_um / 1000.0
        # Update spinbox without triggering recursion
        self.depth_min_spin.blockSignals(True)
        self.depth_min_spin.setValue(depth_min_mm)
        self.depth_min_spin.blockSignals(False)

    def _on_cursor_max_moved(self) -> None:
        """Handle max depth cursor movement."""
        depth_max_um = self.depth_max_cursor.pos().y()
        depth_max_mm = depth_max_um / 1000.0
        # Update spinbox without triggering recursion
        self.depth_max_spin.blockSignals(True)
        self.depth_max_spin.setValue(depth_max_mm)
        self.depth_max_spin.blockSignals(False)

    def _reset_view(self) -> None:
        """Reset probe visualization to full view."""
        max_y = self.imro_gen.max_depth
        self.plot_widget.setXRange(-10, 250, padding=0)
        self.plot_widget.setYRange(-100, max_y + 1000, padding=0)

    def _show_full_probe(self) -> None:
        """Show all electrodes on probe in grey (no selection yet)."""
        self.plot_widget.clear()

        rect_size = 10   # µm

        # Draw all electrode sites using CSV coordinates
        for _, row in self.imro_gen.df.iterrows():
            x_center = float(row['x'])
            y_center = float(row['y'])

            x_left = x_center - rect_size / 2
            y_top = y_center - rect_size / 2

            rect = QGraphicsRectItem(x_left, y_top, rect_size, rect_size)
            rect.setPen(pg.mkPen(color=(220, 220, 220), width=0.5))
            rect.setBrush(pg.mkBrush(color=(220, 220, 220)))
            self.plot_widget.addItem(rect)

        # Draw horizontal lines marking bank borders
        for bank in range(1, self.imro_gen.total_banks):
            bank_prev = self.imro_gen.df[self.imro_gen.df['bank'] == bank - 1]
            bank_curr = self.imro_gen.df[self.imro_gen.df['bank'] == bank]

            if len(bank_prev) > 0 and len(bank_curr) > 0:
                y_end_prev = float(bank_prev['y'].max())
                y_start_curr = float(bank_curr['y'].min())
                y_pos = (y_end_prev + y_start_curr) / 2
                line = pg.InfiniteLine(pos=y_pos, angle=0, pen=pg.mkPen(color=(150, 150, 150), width=1, style=Qt.DashLine))
                self.plot_widget.addItem(line)

        # Add bank labels between boundary lines
        for bank in range(self.imro_gen.total_banks):
            bank_data = self.imro_gen.df[self.imro_gen.df['bank'] == bank]
            if len(bank_data) > 0:
                y_start = float(bank_data['y'].min())
                y_end = float(bank_data['y'].max())
                y_mid = (y_start + y_end) / 2
                text = pg.TextItem(f"Bank {bank}", anchor=(0.5, 0.5), color=(100, 100, 100))
                text.setPos(50, y_mid)
                self.plot_widget.addItem(text)

        # Set tight view range using actual probe dimensions from CSV
        max_y = self.imro_gen.max_depth
        self.plot_widget.setXRange(-10, 250, padding=0)
        self.plot_widget.setYRange(-100, max_y + 1000, padding=0)
        self.plot_widget.setTitle("NP1.0 Probe - All 4416 channels available")
        #self.plot_widget.setTit

    def generate_channels(self) -> None:
        """Generate channel configuration using depth-range algorithm."""
        try:
            depth_min_mm = self.depth_min_spin.value()
            depth_max_mm = self.depth_max_spin.value()

            # Convert to micrometers
            depth_min_um = int(depth_min_mm * 1000)
            depth_max_um = int(depth_max_mm * 1000)

            # Get assignment mode
            assignment_mode = 'mixed' if self.assignment_mixed_radio.isChecked() else 'striped'

            # Generate electrode list
            self.current_channels = self.imro_gen.generate_electrode_list(depth_min_um, depth_max_um, assignment_mode)

            self.update_visualization()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate channels: {e}")

    def update_visualization(self) -> None:
        """Update probe visualization showing selected channels."""
        self.plot_widget.clear()

        # Build set of selected electrode IDs
        selected_electrodes = set(self.current_channels)

        # Draw all electrodes using CSV coordinates
        rect_size = 10  # µm

        for _, row in self.imro_gen.df.iterrows():
            electrode_id = int(row['electrode'])
            x_center = float(row['x'])
            y_center = float(row['y'])
            is_ref = bool(row['ref'])

            # Rectangle bounds
            x_left = x_center - rect_size / 2
            y_top = y_center - rect_size / 2

            # Determine color
            if is_ref:
                color = (100, 100, 100)  # Dark grey for reference
            elif electrode_id in selected_electrodes:
                color = (0, 200, 0)  # Green for selected
            else:
                color = (220, 220, 220)  # Light grey for unselected

            # Create and add rectangle
            rect = QGraphicsRectItem(x_left, y_top, rect_size, rect_size)
            rect.setPen(pg.mkPen(color=color, width=0.5))
            rect.setBrush(pg.mkBrush(color=color))
            self.plot_widget.addItem(rect)

        # Draw bank boundary lines
        for bank in range(1, self.imro_gen.total_banks):
            # Get depth range for each bank from CSV
            bank_prev = self.imro_gen.df[self.imro_gen.df['bank'] == bank - 1]
            bank_curr = self.imro_gen.df[self.imro_gen.df['bank'] == bank]

            if len(bank_prev) > 0 and len(bank_curr) > 0:
                y_end_prev = float(bank_prev['y'].max())
                y_start_curr = float(bank_curr['y'].min())
                y_pos = (y_end_prev + y_start_curr) / 2
                line = pg.InfiniteLine(pos=y_pos, angle=0,
                                       pen=pg.mkPen(color=(150, 150, 150), width=1, style=Qt.DashLine))
                self.plot_widget.addItem(line)

        # Add bank labels
        for bank in range(self.imro_gen.total_banks):
            bank_data = self.imro_gen.df[self.imro_gen.df['bank'] == bank]
            if len(bank_data) > 0:
                y_start = float(bank_data['y'].min())
                y_end = float(bank_data['y'].max())
                y_mid = (y_start + y_end) / 2
                text = pg.TextItem(f"Bank {bank}", anchor=(0.5, 0.5), color=(100, 100, 100))
                text.setPos(50, y_mid)
                self.plot_widget.addItem(text)

        # Set view range using actual probe dimensions from CSV
        max_y = float(self.imro_gen.df['y'].max())
        self.plot_widget.setXRange(-10, 250, padding=0)
        self.plot_widget.setYRange(-100, max_y + 1000, padding=0)

        # Add title with info
        if self.current_channels:
            info_text = f"NP1.0: {len(self.current_channels)} channels"
            self.plot_widget.setTitle(info_text)

    def save_imro(self) -> None:
        """Save IMRO file."""
        if not self.current_channels:
            QMessageBox.warning(self, "Warning", "Generate channels first")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save IMRO File", self.last_directory, "IMRO Files (*.imro);;All Files (*)"
        )

        if file_path:
            try:
                self.last_directory = os.path.dirname(file_path)
                self.config['last_directory'] = self.last_directory
                self._save_config()

                # Get settings from GUI
                ap_gain = int(self.ap_gain_combo.currentText())
                lf_gain = int(self.lf_gain_combo.currentText())
                ap_filter = self.ap_filter_check.isChecked()
                ref_type = 'tip' if self.ref_tip_radio.isChecked() else 'external'

                # Generate and save IMRO content
                content = self.imro_gen.generate_imro_content(
                    self.current_channels,
                    ap_gain=ap_gain,
                    lf_gain=lf_gain,
                    ap_filter=ap_filter,
                    ref_type=ref_type
                )

                with open(file_path, 'w') as f:
                    f.write(content)

                QMessageBox.information(self, "Success", f"Saved IMRO to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def save_kilosort_probe(self) -> None:
        """Save Kilosort probe configuration file (.json)."""
        if not self.current_channels:
            QMessageBox.warning(self, "No Channels", "Generate channels first before saving Kilosort probe")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Kilosort Probe", self.last_directory,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                self.last_directory = os.path.dirname(file_path)
                self.config['last_directory'] = self.last_directory
                self._save_config()

                # Generate Kilosort probe dictionary
                probe_dict = self.imro_gen.generate_kilosort_probe(self.current_channels)

                # Save as JSON
                with open(file_path, 'w') as f:
                    json.dump(probe_dict, f, indent=2)

                QMessageBox.information(self, "Success", f"Kilosort probe saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save Kilosort probe: {e}")

    def load_imro(self) -> None:
        """Load IMRO file and update GUI."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load IMRO File", self.last_directory, "IMRO Files (*.imro);;All Files (*)"
        )

        if file_path:
            try:
                self.last_directory = os.path.dirname(file_path)
                self.config['last_directory'] = self.last_directory
                self._save_config()

                with open(file_path, 'r') as f:
                    content = f.read()

                # Parse IMRO file
                imro_data = self.imro_gen.parse_imro_file(content)

                # Update GUI with loaded configuration
                self.current_channels = imro_data['electrode_ids']

                # Update depth spinboxes
                depth_min_mm = imro_data['depth_min_um'] / 1000.0
                depth_max_mm = imro_data['depth_max_um'] / 1000.0
                self.depth_min_spin.setValue(depth_min_mm)
                self.depth_max_spin.setValue(depth_max_mm)

                # Update gains and filter
                self.ap_gain_combo.setCurrentText(str(imro_data['ap_gain']))
                self.lf_gain_combo.setCurrentText(str(imro_data['lf_gain']))
                self.ap_filter_check.setChecked(imro_data['ap_filter'])

                # Update assignment mode
                if imro_data['assignment_mode'] == 'mixed':
                    self.assignment_mixed_radio.setChecked(True)
                else:
                    self.assignment_striped_radio.setChecked(True)

                # Update visualization
                self._show_full_probe()
                self.update_visualization()

                QMessageBox.information(
                    self, "Success",
                    f"Loaded {len(self.current_channels)} channels\n"
                    f"Depth: {depth_min_mm:.2f} - {depth_max_mm:.2f} mm\n"
                    f"Mode: {imro_data['assignment_mode']}\n"
                    f"AP Gain: {imro_data['ap_gain']}, LF Gain: {imro_data['lf_gain']}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {e}")

    def reset_to_defaults(self) -> None:
        """Reset to default values."""
        self.ap_gain_combo.setCurrentText("500")
        self.lf_gain_combo.setCurrentText("250")
        self.ap_filter_check.setChecked(True)
        self.ref_external_radio.setChecked(False)
        self.ref_tip_radio.setChecked(True)
        self.ref_own_radio.setChecked(True)
        self.depth_min_spin.setValue(0.0)
        self.depth_max_spin.setValue(self.max_depth_mm)
        self.current_channels = []
        self._show_full_probe()


def main():
    """Main entry point for the IMRO Config GUI."""
    app = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication(sys.argv)
    window = ImroConfigGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
