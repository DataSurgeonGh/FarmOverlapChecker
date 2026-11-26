
import os
import csv

from qgis.PyQt.QtCore import QVariant

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
    QApplication
)

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsField,
    QgsFeature
)

from .core.analysis import run_overlap_analysis


# ==================================================
# SUPPORT QGIS 3 (PyQt5) AND QGIS 4 (PyQt6)
# ==================================================

try:
    YES_BUTTON = QMessageBox.StandardButton.Yes
    NO_BUTTON = QMessageBox.StandardButton.No

except AttributeError:
    YES_BUTTON = QMessageBox.Yes
    NO_BUTTON = QMessageBox.No


# ==================================================
# MAIN DIALOG CLASS
# ==================================================

class OverlapCheckerDialog(QDialog):

    def __init__(self, iface, parent=None):

        super().__init__(parent)

        self.iface = iface
        self.project = QgsProject.instance()

        self.cancel_requested = False
        self.analysis_running = False

        self.setWindowTitle("Farm Overlap Checker")
        self.setMinimumWidth(520)

        self.setup_ui()
        self.connect_project_signals()
        self.refresh_layers()


    # --------------------------------------------------
    # BUILD THE INTERFACE
    # --------------------------------------------------

    def setup_ui(self):

        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Farm Overlap Checker")

        title.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        main_layout.addWidget(title)

        form_layout = QFormLayout()

        # ----------------------------------------------
        # POLYGON LAYER SELECTOR
        # ----------------------------------------------

        self.layer_combo = QComboBox()

        # Keep the dropdown clickable
        self.layer_combo.setEnabled(True)

        # Add a refresh button beside the dropdown
        self.refresh_button = QPushButton("Refresh")

        self.refresh_button.setToolTip(
            "Reload polygon layers from the current QGIS project"
        )

        self.refresh_button.clicked.connect(
            self.refresh_layers
        )

        layer_layout = QHBoxLayout()

        layer_layout.addWidget(self.layer_combo)
        layer_layout.addWidget(self.refresh_button)

        form_layout.addRow(
            "Polygon layer:",
            layer_layout
        )

        # ----------------------------------------------
        # FARM 1 THRESHOLD
        # ----------------------------------------------

        self.threshold1_spin = QDoubleSpinBox()

        self.threshold1_spin.setRange(0, 100)
        self.threshold1_spin.setDecimals(2)
        self.threshold1_spin.setValue(10)
        self.threshold1_spin.setSuffix(" %")

        form_layout.addRow(
            "Farm 1 overlap threshold:",
            self.threshold1_spin
        )

        # ----------------------------------------------
        # FARM 2 THRESHOLD
        # ----------------------------------------------

        self.threshold2_spin = QDoubleSpinBox()

        self.threshold2_spin.setRange(0, 100)
        self.threshold2_spin.setDecimals(2)
        self.threshold2_spin.setValue(5)
        self.threshold2_spin.setSuffix(" %")

        form_layout.addRow(
            "Farm 2 overlap threshold:",
            self.threshold2_spin
        )

        # ----------------------------------------------
        # CSV OUTPUT PATH
        # ----------------------------------------------

        self.output_edit = QLineEdit()

        self.output_edit.setPlaceholderText(
            "Select where to save the CSV results"
        )

        self.browse_button = QPushButton("Browse...")

        self.browse_button.clicked.connect(
            self.browse_output
        )

        output_layout = QHBoxLayout()

        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.browse_button)

        form_layout.addRow(
            "Output CSV:",
            output_layout
        )

        main_layout.addLayout(form_layout)

        # ----------------------------------------------
        # EXPLANATION
        # ----------------------------------------------

        explanation = QLabel(
            "A pair is reported when either farm's overlap "
            "percentage exceeds its respective threshold."
        )

        explanation.setWordWrap(True)

        explanation.setStyleSheet(
            "color: gray; font-size: 10px;"
        )

        main_layout.addWidget(explanation)

        # ----------------------------------------------
        # PROGRESS BAR
        # ----------------------------------------------

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        main_layout.addWidget(self.progress_bar)

        # ----------------------------------------------
        # STATUS LABEL
        # ----------------------------------------------

        self.status_label = QLabel("Ready.")

        main_layout.addWidget(self.status_label)

        # ----------------------------------------------
        # RUN AND CANCEL BUTTONS
        # ----------------------------------------------

        button_layout = QHBoxLayout()

        self.run_button = QPushButton(
            "Run Overlap Analysis"
        )

        self.cancel_button = QPushButton("Cancel")

        self.cancel_button.setEnabled(False)

        self.run_button.clicked.connect(
            self.run_analysis
        )

        self.cancel_button.clicked.connect(
            self.cancel_analysis
        )

        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)


    # --------------------------------------------------
    # CONNECT TO QGIS PROJECT SIGNALS
    # --------------------------------------------------

    def connect_project_signals(self):

        # Refresh when layers are added
        self.project.layersAdded.connect(
            self.refresh_layers
        )

        # Refresh when layers are removed
        self.project.layersRemoved.connect(
            self.refresh_layers
        )

        # Refresh when the active QGIS layer changes
        try:
            self.iface.currentLayerChanged.connect(
                self.on_active_layer_changed
            )
        except (AttributeError, TypeError):
            pass


    # --------------------------------------------------
    # HANDLE ACTIVE LAYER CHANGES
    # --------------------------------------------------

    def on_active_layer_changed(self, layer):

        if self.analysis_running:
            return

        # If the active layer is a polygon layer,
        # select it in the dropdown.
        if (
            layer is not None
            and isinstance(layer, QgsVectorLayer)
            and layer.isValid()
            and QgsWkbTypes.geometryType(
                layer.wkbType()
            ) == QgsWkbTypes.PolygonGeometry
        ):

            index = self.layer_combo.findData(
                layer.id()
            )

            if index >= 0:
                self.layer_combo.setCurrentIndex(index)


    # --------------------------------------------------
    # REFRESH AVAILABLE POLYGON LAYERS
    # --------------------------------------------------

    def refresh_layers(self, *args):

        if self.analysis_running:
            return

        # Remember the previous selection
        previous_layer_id = self.layer_combo.currentData()

        # Block signals while rebuilding the dropdown
        self.layer_combo.blockSignals(True)

        try:

            self.layer_combo.clear()

            polygon_layers = []

            # Retrieve all layers in the current project
            for layer in self.project.mapLayers().values():

                # Only vector layers
                if not isinstance(layer, QgsVectorLayer):
                    continue

                # Ignore invalid layers
                if not layer.isValid():
                    continue

                # Determine geometry type
                geometry_type = QgsWkbTypes.geometryType(
                    layer.wkbType()
                )

                # Keep polygon layers only
                if geometry_type != QgsWkbTypes.PolygonGeometry:
                    continue

                polygon_layers.append(layer)

            # Populate dropdown
            for layer in polygon_layers:

                self.layer_combo.addItem(
                    layer.name(),
                    layer.id()
                )

            # Restore previous selection
            selected_index = self.layer_combo.findData(
                previous_layer_id
            )

            if selected_index >= 0:

                self.layer_combo.setCurrentIndex(
                    selected_index
                )

            else:

                # Otherwise, select active polygon layer
                active_layer = self.iface.activeLayer()

                active_index = -1

                if (
                    active_layer is not None
                    and isinstance(active_layer, QgsVectorLayer)
                ):

                    active_index = self.layer_combo.findData(
                        active_layer.id()
                    )

                if active_index >= 0:

                    self.layer_combo.setCurrentIndex(
                        active_index
                    )

                elif self.layer_combo.count() > 0:

                    # Select the first available polygon layer
                    self.layer_combo.setCurrentIndex(0)

            # If no polygon layers exist, show a placeholder
            if not polygon_layers:

                self.layer_combo.addItem(
                    "No polygon layers found",
                    None
                )

        finally:

            self.layer_combo.blockSignals(False)

        # IMPORTANT:
        # Keep the dropdown enabled even when it is empty.
        # It should only be disabled during analysis.
        self.layer_combo.setEnabled(
            not self.analysis_running
        )

        self.refresh_button.setEnabled(
            not self.analysis_running
        )

        # Update status
        if not polygon_layers:

            self.status_label.setText(
                "No polygon layers found. Add a polygon layer "
                "or click Refresh."
            )

        else:

            self.status_label.setText(
                f"{len(polygon_layers)} polygon layer(s) available."
            )


    # --------------------------------------------------
    # SELECT CSV OUTPUT LOCATION
    # --------------------------------------------------

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

            self.output_edit.setText(output_path)


    # --------------------------------------------------
    # LOAD CSV RESULTS INTO A TEMPORARY QGIS MEMORY TABLE
    # --------------------------------------------------

    def load_results_as_temporary_layer(self, csv_path):

        layer_name = (
            "Farm Overlap Results - "
            + os.path.basename(csv_path)
        )

        # Create a non-spatial memory table
        results_layer = QgsVectorLayer(
            "None",
            layer_name,
            "memory"
        )

        if not results_layer.isValid():

            raise Exception(
                "Could not create the temporary QGIS results table."
            )

        provider = results_layer.dataProvider()

        # Define fields
        fields = [
            QgsField("farm_id_1", QVariant.String),
            QgsField("farm_id_2", QVariant.String),
            QgsField("overlap_percentage_1", QVariant.Double),
            QgsField("overlap_percentage_2", QVariant.Double)
        ]

        provider.addAttributes(fields)

        results_layer.updateFields()

        batch = []
        batch_size = 1000

        # Read CSV results
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
                "overlap_percentage_2"
            }

            actual_columns = set(reader.fieldnames or [])

            if not required_columns.issubset(actual_columns):

                raise Exception(
                    "The CSV file does not contain the expected "
                    "overlap result columns."
                )

            for row in reader:

                feature = QgsFeature(
                    results_layer.fields()
                )

                feature.setAttributes([
                    row["farm_id_1"],
                    row["farm_id_2"],
                    float(row["overlap_percentage_1"]),
                    float(row["overlap_percentage_2"])
                ])

                batch.append(feature)

                # Insert records in batches
                if len(batch) >= batch_size:

                    provider.addFeatures(batch)

                    batch.clear()

        # Insert remaining records
        if batch:

            provider.addFeatures(batch)

        results_layer.updateExtents()

        # Add results table to QGIS Layers panel
        self.project.addMapLayer(results_layer)

        return results_layer


    # --------------------------------------------------
    # CANCEL ANALYSIS
    # --------------------------------------------------

    def cancel_analysis(self):

        if not self.analysis_running:
            return

        self.cancel_requested = True

        self.status_label.setText(
            "Cancellation requested..."
        )


    # --------------------------------------------------
    # UPDATE PROGRESS
    # --------------------------------------------------

    def update_progress(self, percentage):

        self.progress_bar.setValue(
            int(percentage)
        )

        self.status_label.setText(
            f"Processing: {int(percentage)}%"
        )

        QApplication.processEvents()


    # --------------------------------------------------
    # CHECK WHETHER ANALYSIS SHOULD STOP
    # --------------------------------------------------

    def should_cancel(self):

        QApplication.processEvents()

        return self.cancel_requested


    # --------------------------------------------------
    # ENABLE / DISABLE CONTROLS
    # --------------------------------------------------

    def set_processing_state(self, running):

        self.analysis_running = running

        # Disable layer controls only during analysis
        self.layer_combo.setEnabled(not running)

        self.refresh_button.setEnabled(not running)

        self.threshold1_spin.setEnabled(not running)
        self.threshold2_spin.setEnabled(not running)

        self.output_edit.setEnabled(not running)
        self.browse_button.setEnabled(not running)

        self.run_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)


    # --------------------------------------------------
    # RUN OVERLAP ANALYSIS
    # --------------------------------------------------

    def run_analysis(self):

        # Get selected layer
        layer_id = self.layer_combo.currentData()

        if not layer_id:

            QMessageBox.warning(
                self,
                "No Layer Selected",
                "Please select a valid polygon layer."
            )

            return

        layer = self.project.mapLayer(layer_id)

        if layer is None or not layer.isValid():

            QMessageBox.warning(
                self,
                "Invalid Layer",
                "The selected layer is no longer available."
            )

            self.refresh_layers()

            return

        # Confirm it is still a polygon layer
        if QgsWkbTypes.geometryType(
            layer.wkbType()
        ) != QgsWkbTypes.PolygonGeometry:

            QMessageBox.warning(
                self,
                "Invalid Geometry",
                "The selected layer is not a polygon layer."
            )

            self.refresh_layers()

            return

        # Get thresholds
        threshold1 = self.threshold1_spin.value()
        threshold2 = self.threshold2_spin.value()

        # Get output path
        output_csv = self.output_edit.text().strip()

        if not output_csv:

            QMessageBox.warning(
                self,
                "Missing Output",
                "Please select an output CSV file."
            )

            return

        if not output_csv.lower().endswith(".csv"):

            output_csv += ".csv"

            self.output_edit.setText(output_csv)

        # Confirm overwriting existing output
        if os.path.exists(output_csv):

            answer = QMessageBox.question(
                self,
                "Overwrite Existing File",
                "The selected CSV file already exists. "
                "Do you want to overwrite it?",
                YES_BUTTON | NO_BUTTON,
                NO_BUTTON
            )

            if answer != YES_BUTTON:
                return

        # Prepare interface
        self.cancel_requested = False

        self.progress_bar.setValue(0)

        self.set_processing_state(True)

        self.status_label.setText(
            "Preparing overlap analysis..."
        )

        QApplication.processEvents()

        try:

            # Execute overlap analysis
            results = run_overlap_analysis(
                layer=layer,
                threshold1=threshold1,
                threshold2=threshold2,
                output_csv=output_csv,
                progress_callback=self.update_progress,
                cancel_callback=self.should_cancel
            )

            self.progress_bar.setValue(100)

            # Load CSV into QGIS as a temporary memory table
            try:

                results_layer = self.load_results_as_temporary_layer(
                    results["output_file"]
                )

                temporary_layer_message = (
                    "\n\nTemporary QGIS table: "
                    f"{results_layer.name()}"
                    "\nThe results have also been added "
                    "to the Layers panel."
                )

                self.status_label.setText(
                    "Analysis completed. Results loaded into QGIS."
                )

            except Exception as load_error:

                temporary_layer_message = (
                    "\n\nCSV was saved successfully, but the "
                    "temporary QGIS table could not be created:"
                    f"\n{str(load_error)}"
                )

                self.status_label.setText(
                    "Analysis completed. CSV saved; table loading failed."
                )

            # Display results
            QMessageBox.information(
                self,
                "Analysis Completed",
                (
                    f"Total farms processed: "
                    f"{results['total_farms']}\n\n"

                    f"Overlapping pairs found: "
                    f"{results['overlapping_pairs']}\n\n"

                    f"Features skipped: "
                    f"{results['skipped_features']}\n\n"

                    f"Geometry errors: "
                    f"{results['geometry_errors']}\n\n"

                    f"ID field used: "
                    f"{results['id_field']}\n\n"

                    f"CSV saved to:\n"
                    f"{results['output_file']}"

                    f"{temporary_layer_message}"
                )
            )

        except InterruptedError:

            self.status_label.setText(
                "Analysis cancelled."
            )

            QMessageBox.information(
                self,
                "Analysis Cancelled",
                "The overlap analysis was cancelled."
            )

        except Exception as error:

            self.status_label.setText(
                "Analysis failed."
            )

            QMessageBox.critical(
                self,
                "Analysis Error",
                str(error)
            )

        finally:

            self.set_processing_state(False)

            # Refresh layers after processing
            self.refresh_layers()


    # --------------------------------------------------
    # CLEAN UP PROJECT SIGNALS
    # --------------------------------------------------

    def closeEvent(self, event):

        try:
            self.project.layersAdded.disconnect(
                self.refresh_layers
            )
        except (TypeError, RuntimeError):
            pass

        try:
            self.project.layersRemoved.disconnect(
                self.refresh_layers
            )
        except (TypeError, RuntimeError):
            pass

        try:
            self.iface.currentLayerChanged.disconnect(
                self.on_active_layer_changed
            )
        except (AttributeError, TypeError, RuntimeError):
            pass

        super().closeEvent(event)
