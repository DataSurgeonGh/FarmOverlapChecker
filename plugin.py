
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

import os
import traceback

from qgis.PyQt.QtGui import QAction, QIcon

from qgis.core import (
    QgsApplication,
    QgsMessageLog,
    Qgis,
)

from .dialog import OverlapCheckerDialog
from .processing.provider import FarmOverlapProvider


class FarmOverlapCheckerPlugin:

    PLUGIN_NAME = "Farm Overlap Checker"

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.action = None
        self.dialog = None
        self.provider = None

    # --------------------------------------------------
    # LOGGING
    # --------------------------------------------------

    def log_message(self, message, level=Qgis.MessageLevel.Info):

        QgsMessageLog.logMessage(
            message,
            self.PLUGIN_NAME,
            level
        )

    # --------------------------------------------------
    # INITIALISE PLUGIN
    # --------------------------------------------------

    def initGui(self):

        # Register Processing Toolbox provider

        try:

            self.provider = FarmOverlapProvider()

            registered = (
                QgsApplication.processingRegistry().addProvider(
                    self.provider
                )
            )

            if registered:

                self.log_message(
                    "Processing provider registered successfully."
                )

            else:

                self.provider = None

                self.log_message(
                    "Processing provider registration failed.",
                    Qgis.MessageLevel.Warning
                )

        except Exception as error:

            self.provider = None

            self.log_message(
                "Processing provider registration error: {}".format(
                    error
                ),
                Qgis.MessageLevel.Critical
            )

            self.log_message(
                traceback.format_exc(),
                Qgis.MessageLevel.Critical
            )

        # Create standalone interface action

        icon_path = os.path.join(
            self.plugin_dir,
            "icons",
            "icon.svg"
        )

        self.action = QAction(
            QIcon(icon_path),
            self.PLUGIN_NAME,
            self.iface.mainWindow()
        )

        self.action.setWhatsThis(
            "Identify overlapping farm polygons "
            "using configurable overlap thresholds."
        )

        self.action.triggered.connect(self.run)

        self.iface.addPluginToMenu(
            "&Farm Overlap Checker",
            self.action
        )

        self.iface.addToolBarIcon(self.action)

    # --------------------------------------------------
    # OPEN STANDALONE PLUGIN DIALOG
    # --------------------------------------------------

    def run(self):

        if self.dialog is None:

            self.dialog = OverlapCheckerDialog(
                self.iface,
                self.iface.mainWindow()
            )

        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    # --------------------------------------------------
    # UNLOAD PLUGIN
    # --------------------------------------------------

    def unload(self):

        # Remove standalone interface

        if self.action is not None:

            self.iface.removePluginMenu(
                "&Farm Overlap Checker",
                self.action
            )

            self.iface.removeToolBarIcon(
                self.action
            )

            self.action.deleteLater()
            self.action = None

        # Close standalone dialog

        if self.dialog is not None:

            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None

        # Unregister Processing provider

        if self.provider is not None:

            QgsApplication.processingRegistry().removeProvider(
                self.provider
            )

            self.provider = None

            self.log_message(
                "Processing provider removed successfully."
            )
