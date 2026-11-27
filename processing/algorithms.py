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

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFileDestination,
    QgsProcessingOutputNumber,
)

from ..core.analysis import run_overlap_analysis


class FarmOverlapAlgorithm(QgsProcessingAlgorithm):
    """
    Farm Overlap Checker Processing Toolbox algorithm.

    Uses the same analysis engine as the standalone plugin.
    """

    INPUT = "INPUT"
    THRESHOLD1 = "THRESHOLD1"
    THRESHOLD2 = "THRESHOLD2"
    OUTPUT = "OUTPUT"

    TOTAL_FARMS = "TOTAL_FARMS"
    OVERLAPPING_PAIRS = "OVERLAPPING_PAIRS"
    SKIPPED_FEATURES = "SKIPPED_FEATURES"
    GEOMETRY_ERRORS = "GEOMETRY_ERRORS"

    def createInstance(self):
        return FarmOverlapAlgorithm()

    def name(self):
        return "check_farm_overlaps"

    def displayName(self):
        return "Check Farm Overlaps"

    def group(self):
        return "Farm Overlap Analysis"

    def groupId(self):
        return "farm_overlap_analysis"

    def shortHelpString(self):
        return (
            "Identifies overlapping farm polygons using two configurable "
            "overlap percentage thresholds.\n\n"
            "A pair is included when either farm's overlap percentage "
            "exceeds its corresponding threshold:\n\n"
            "Farm 1 percentage > Farm 1 threshold OR "
            "Farm 2 percentage > Farm 2 threshold.\n\n"
            "Results are exported to a CSV file."
        )

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                "Input farm polygon layer",
                types=[QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD1,
                "Farm 1 minimum overlap percentage",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=100.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD2,
                "Farm 2 minimum overlap percentage",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=100.0,
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                "Overlap results CSV",
                fileFilter="CSV files (*.csv)",
            )
        )

        self.addOutput(
            QgsProcessingOutputNumber(
                self.TOTAL_FARMS,
                "Total farms processed",
            )
        )

        self.addOutput(
            QgsProcessingOutputNumber(
                self.OVERLAPPING_PAIRS,
                "Overlapping farm pairs",
            )
        )

        self.addOutput(
            QgsProcessingOutputNumber(
                self.SKIPPED_FEATURES,
                "Skipped features",
            )
        )

        self.addOutput(
            QgsProcessingOutputNumber(
                self.GEOMETRY_ERRORS,
                "Geometry errors",
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        layer = self.parameterAsVectorLayer(
            parameters,
            self.INPUT,
            context,
        )

        threshold1 = self.parameterAsDouble(
            parameters,
            self.THRESHOLD1,
            context,
        )

        threshold2 = self.parameterAsDouble(
            parameters,
            self.THRESHOLD2,
            context,
        )

        output_csv = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context,
        )

        if layer is None or not layer.isValid():
            raise QgsProcessingException(
                "The selected input layer is invalid."
            )

        if not output_csv:
            raise QgsProcessingException(
                "An output CSV destination is required."
            )

        feedback.pushInfo(
            "Starting Farm Overlap Analysis."
        )

        feedback.pushInfo(
            "Input layer: {}".format(layer.name())
        )

        feedback.pushInfo(
            "Farm 1 threshold: {}%".format(threshold1)
        )

        feedback.pushInfo(
            "Farm 2 threshold: {}%".format(threshold2)
        )

        try:

            results = run_overlap_analysis(
                layer=layer,
                threshold1=threshold1,
                threshold2=threshold2,
                output_csv=output_csv,
                progress_callback=feedback.setProgress,
                cancel_callback=feedback.isCanceled,
            )

        except InterruptedError:

            feedback.pushInfo(
                "Farm overlap analysis was cancelled."
            )

            return {}

        except Exception as error:

            raise QgsProcessingException(
                "Farm overlap analysis failed: {}".format(error)
            )

        feedback.pushInfo(
            "Farm overlap analysis completed successfully."
        )

        feedback.pushInfo(
            "Total farms processed: {}".format(
                results["total_farms"]
            )
        )

        feedback.pushInfo(
            "Overlapping pairs found: {}".format(
                results["overlapping_pairs"]
            )
        )

        feedback.pushInfo(
            "Skipped features: {}".format(
                results["skipped_features"]
            )
        )

        feedback.pushInfo(
            "Geometry errors: {}".format(
                results["geometry_errors"]
            )
        )

        feedback.pushInfo(
            "Farm ID field used: {}".format(
                results["id_field"]
            )
        )

        feedback.pushInfo(
            "CSV output: {}".format(
                results["output_file"]
            )
        )

        return {
            self.OUTPUT: results["output_file"],
            self.TOTAL_FARMS: results["total_farms"],
            self.OVERLAPPING_PAIRS: results["overlapping_pairs"],
            self.SKIPPED_FEATURES: results["skipped_features"],
            self.GEOMETRY_ERRORS: results["geometry_errors"],
        }
