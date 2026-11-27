
# Farm Overlap Checker
# Copyright (C) 2026 KA Chanik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the LICENSE file for details.

import csv
import os

from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QApplication,
)

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsField,
    QgsFeature,
    Qgis,
)

from .core.analysis import run_overlap_analysis


YES_BUTTON = QMessageBox.StandardButton.Yes
NO_BUTTON = QMessageBox.StandardButton.No


class OverlapCheckerDialog(QDialog):

    def __init__(self, iface, parent=None):

        super().__init__(parent)

        self.iface = iface
        self.project = QgsProject.instance()

        self.cancel_requested = False
        self.analysis_running = False

        self.setWindowTitle("Farm Overlap Checker")
        self.setMinimumWidth(520)

        self._build_ui()
        self._connect_signals()

        self.refresh_layers()

    # ================================================================
    # USER INTERFACE
    # ================================================================

    def _build_ui(self):

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Polygon layer selection
        self.layer_combo = QComboBox()

        self.refresh_button = QPushButton("Refresh")

        layer_layout = QHBoxLayout()
        layer_layout.addWidget(self.layer_combo)
        layer_layout.addWidget(self.refresh_button)

        form_layout.addRow(
            "Farm polygon layer:",
            layer_layout
        )

        # First overlap threshold
        self.threshold1_spin = QDoubleSpinBox()
        self.threshold1_spin.setRange(0.0, 100.0)
        self.threshold1_spin.setDecimals(2)
        self.threshold1_spin.setSingleStep(1.0)
        self.threshold1_spin.setValue(10.0)
        self.threshold1_spin.setSuffix(" %")

        form_layout.addRow(
            "Farm 1 overlap threshold:",
            self.threshold1_spin
        )

        # Second overlap threshold
        self.threshold2_spin = QDoubleSpinBox()
        self.threshold2_spin.setRange(0.0, 100.0)
        self.threshold2_spin.setDecimals(2)
        self.threshold2_spin.setSingleStep(1.0)
        self.threshold2_spin.setValue(5.0)
        self.threshold2_spin.setSuffix(" %")

        form_layout.addRow(
            "Farm 2 overlap threshold:",
            self.threshold2_spin
        )

        # CSV output path
        self.output_line = QLineEdit()
        self.output_line.setPlaceholderText(
            "Select the output CSV file..."
        )

        self.browse_button = QPushButton("Browse")

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(self.browse_button)

        form_layout.addRow(
            "Output CSV:",
            output_layout
        )

        main_layout.addLayout(form_layout)

        # Explanation
        self.info_label = QLabel(
            "An overlapping pair is included when either farm's "
            "overlap percentage exceeds its corresponding threshold."
        )

        self.info_label.setWordWrap(True)
        main_layout.addWidget(self.info_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        main_layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Ready.")
        main_layout.addWidget(self.status_label)

        # Action buttons
        button_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Analysis")
        self.cancel_button = QPushButton("Cancel")

        self.cancel_button.setEnabled(False)

        button_layout.addStretch()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    # ================================================================
    # SIGNAL CONNECTIONS
    # ================================================================

    def _connect_signals(self):

        self.refresh_button.clicked.connect(
            self.refresh_layers
        )

        self.browse_button.clicked.connect(
            self.browse_output
        )

        self.run_button.clicked.connect(
            self.run_analysis
        )

        self.cancel_button.clicked.connect(
            self.request_cancel
        )

        self.project.layersAdded.connect(
            self.refresh_layers
        )

        self.project.layersRemoved.connect(
            self.refresh_layers
        )

        self.iface.currentLayerChanged.connect(
            self._on_current_layer_changed
        )

    # ================================================================
    # LAYER MANAGEMENT
    # ================================================================

    def refresh_layers(self, *args):

        previous_layer_id = self.layer_combo.currentData()

        self.layer_combo.clear()

        for layer in self.project.mapLayers().values():

            if not isinstance(layer, QgsVectorLayer):
                continue

            if not layer.isValid():
                continue

            if (
                QgsWkbTypes.geometryType(layer.wkbType())
                == Qgis.GeometryType.Polygon
            ):

                self.layer_combo.addItem(
                    layer.name(),
                    layer.id()
                )

        # Restore previous selection where possible
        if previous_layer_id:

            index = self.layer_combo.findData(
                previous_layer_id
            )

            if index >= 0:
                self.layer_combo.setCurrentIndex(index)

        # Otherwise, use the current QGIS layer
        if self.layer_combo.currentIndex() < 0:

            self._on_current_layer_changed(
                self.iface.activeLayer()
            )

        if self.layer_combo.count() == 0:

            self.status_label.setText(
                "No polygon layers are currently available."
            )

        elif not self.analysis_running:

            self.status_label.setText(
                "{} polygon layer(s) available.".format(
                    self.layer_combo.count()
                )
            )

    def _on_current_layer_changed(self, layer):

        if not isinstance(layer, QgsVectorLayer):
            return

        if not layer.isValid():
            return

        if (
            QgsWkbTypes.geometryType(layer.wkbType())
            != Qgis.GeometryType.Polygon
        ):
            return

        index = self.layer_combo.findData(layer.id())

        if index >= 0:
            self.layer_combo.setCurrentIndex(index)

    def _get_selected_layer(self):

        layer_id = self.layer_combo.currentData()

        if not layer_id:
            return None

        layer = self.project.mapLayer(layer_id)

        if layer is None or not layer.isValid():
            return None

        return layer

    # ================================================================
    # OUTPUT FILE
    # ================================================================

    def browse_output(self):

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Overlap Results",
            "",
            "CSV Files (*.csv)"
        )

        if output_path:

            if not output_path.lower().endswith(".csv"):
                output_path += ".csv"

            self.output_line.setText(output_path)

    # ================================================================
    # PROGRESS AND CANCELLATION
    # ================================================================

    def _update_progress(self, value):

        try:
            value = int(value)
        except (TypeError, ValueError):
            return

        value = max(0, min(100, value))

        self.progress_bar.setValue(value)

        QApplication.processEvents()

    def request_cancel(self):

        if not self.analysis_running:
            return

        self.cancel_requested = True

        self.cancel_button.setEnabled(False)

        self.status_label.setText(
            "Cancellation requested. Waiting for the current operation..."
        )

        QApplication.processEvents()

    def _is_cancelled(self):

        QApplication.processEvents()

        return self.cancel_requested

    # ================================================================
    # LOAD CSV INTO TEMPORARY QGIS MEMORY TABLE
    # ================================================================

    def load_results_as_temporary_layer(self, csv_path):

        memory_layer = QgsVectorLayer(
            "None",
            "Farm Overlap Results",
            "memory"
        )

        if not memory_layer.isValid():

            raise RuntimeError(
                "Could not create the temporary results table."
            )

        fields = [
            QgsField(
                "farm_id_1",
                QMetaType.Type.QString
            ),
            QgsField(
                "farm_id_2",
                QMetaType.Type.QString
            ),
            QgsField(
                "overlap_percentage_1",
                QMetaType.Type.Double
            ),
            QgsField(
                "overlap_percentage_2",
                QMetaType.Type.Double
            ),
        ]

        provider = memory_layer.dataProvider()

        provider.addAttributes(fields)
        memory_layer.updateFields()

        features = []

        with open(
            csv_path,
            mode="r",
            newline="",
            encoding="utf-8-sig"
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            required_columns = {
                "farm_id_1",
                "farm_id_2",
                "overlap_percentage_1",
                "overlap_percentage_2",
            }

            available_columns = set(
                reader.fieldnames or []
            )

            missing_columns = (
                required_columns - available_columns
            )

            if missing_columns:

                raise ValueError(
                    "The CSV file is missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )

            for row in reader:

                feature = QgsFeature(
                    memory_layer.fields()
                )

                feature.setAttributes([
                    str(row["farm_id_1"]),
                    str(row["farm_id_2"]),
                    float(row["overlap_percentage_1"]),
                    float(row["overlap_percentage_2"]),
                ])

                features.append(feature)

        if features:

            success, _ = provider.addFeatures(features)

            if not success:

                raise RuntimeError(
                    "Could not add the CSV results to "
                    "the temporary QGIS table."
                )

        memory_layer.updateExtents()

        self.project.addMapLayer(memory_layer)

        return memory_layer, len(features)

    # ================================================================
    # ENABLE / DISABLE CONTROLS
    # ================================================================

    def _set_controls_enabled(self, enabled):

        self.layer_combo.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)

        self.threshold1_spin.setEnabled(enabled)
        self.threshold2_spin.setEnabled(enabled)

        self.output_line.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)

        self.run_button.setEnabled(enabled)

        self.cancel_button.setEnabled(
            not enabled
        )

    # ================================================================
    # RUN ANALYSIS
    # ================================================================

    def run_analysis(self):

        if self.analysis_running:
            return

        layer = self._get_selected_layer()

        if layer is None:

            QMessageBox.warning(
                self,
                "Missing Polygon Layer",
                "Please select a valid polygon layer."
            )

            return

        output_csv = self.output_line.text().strip()

        if not output_csv:

            QMessageBox.warning(
                self,
                "Missing Output File",
                "Please specify an output CSV file."
            )

            return

        output_csv = os.path.abspath(output_csv)

        output_directory = os.path.dirname(output_csv)

        if not os.path.isdir(output_directory):

            QMessageBox.warning(
                self,
                "Invalid Output Directory",
                "The selected output directory does not exist."
            )

            return

        if os.path.isdir(output_csv):

            QMessageBox.warning(
                self,
                "Invalid Output File",
                "The selected output path is a directory."
            )

            return

        # Confirm before overwriting an existing CSV
        if os.path.exists(output_csv):

            response = QMessageBox.question(
                self,
                "Confirm Overwrite",
                "The selected CSV file already exists.\n\n"
                "Do you want to overwrite it?",
                YES_BUTTON | NO_BUTTON,
                NO_BUTTON
            )

            if response != YES_BUTTON:
                return

        threshold1 = self.threshold1_spin.value()
        threshold2 = self.threshold2_spin.value()

        self.cancel_requested = False
        self.analysis_running = True

        self.progress_bar.setValue(0)

        self.status_label.setText(
            "Starting overlap analysis..."
        )

        self._set_controls_enabled(False)

        QApplication.processEvents()

        try:

            # Execute overlap analysis
            summary = run_overlap_analysis(
                layer=layer,
                threshold1=threshold1,
                threshold2=threshold2,
                output_csv=output_csv,
                progress_callback=self._update_progress,
                cancel_callback=self._is_cancelled
            )

            # Load results into a temporary QGIS memory table
            memory_layer, result_count = (
                self.load_results_as_temporary_layer(
                    output_csv
                )
            )

            self.progress_bar.setValue(100)

            self.status_label.setText(
                "Analysis completed. {} overlapping pair(s) found."
                .format(result_count)
            )

            total_farms = summary.get(
                "total_farms",
                layer.featureCount()
            )

            skipped_features = summary.get(
                "skipped_features",
                0
            )

            geometry_errors = summary.get(
                "geometry_errors",
                0
            )

            QMessageBox.information(
                self,
                "Analysis Completed",
                "Farm overlap analysis completed successfully.\n\n"
                "Total farms processed: {}\n"
                "Overlapping pairs: {}\n"
                "Skipped features: {}\n"
                "Geometry errors: {}\n\n"
                "CSV output:\n{}".format(
                    total_farms,
                    result_count,
                    skipped_features,
                    geometry_errors,
                    output_csv
                )
            )

        except InterruptedError:

            self.status_label.setText(
                "Analysis cancelled."
            )

            QMessageBox.information(
                self,
                "Analysis Cancelled",
                "The overlap analysis was cancelled.\n\n"
                "The incomplete temporary CSV was discarded. "
                "The previous output file, if any, was not replaced."
            )

        except Exception as error:

            self.status_label.setText(
                "Analysis failed."
            )

            QMessageBox.critical(
                self,
                "Analysis Error",
                "An error occurred during overlap analysis:\n\n"
                "{}".format(error)
            )

        finally:

            self.analysis_running = False
            self.cancel_requested = False

            self._set_controls_enabled(True)

            QApplication.processEvents()
