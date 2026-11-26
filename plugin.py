
import os

from qgis.PyQt.QtGui import QIcon

# QAction moved from QtWidgets to QtGui in Qt 6.
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from qgis.core import (
    QgsApplication,
    QgsMessageLog,
)

from .dialog import OverlapCheckerDialog
from .processing.provider import FarmOverlapProvider


class FarmOverlapCheckerPlugin:

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.action = None
        self.dialog = None
        self.provider = None

    # --------------------------------------------------
    # INITIALISE PLUGIN
    # --------------------------------------------------

    def initGui(self):

        # ----------------------------------------------
        # Register Processing Toolbox provider
        # ----------------------------------------------

        try:

            self.provider = FarmOverlapProvider()

            registered = (
                QgsApplication.processingRegistry().addProvider(
                    self.provider
                )
            )

            if registered:

                QgsMessageLog.logMessage(
                    "Farm Overlap Checker Processing provider registered.",
                    "Farm Overlap Checker",
                )

            else:

                QgsMessageLog.logMessage(
                    "Could not register Farm Overlap Checker Processing provider.",
                    "Farm Overlap Checker",
                )

                self.provider = None

        except Exception as error:

            self.provider = None

            QgsMessageLog.logMessage(
                "Processing provider registration failed: {}".format(
                    error
                ),
                "Farm Overlap Checker",
            )

        # ----------------------------------------------
        # Existing standalone plugin interface
        # ----------------------------------------------

        icon_path = os.path.join(
            self.plugin_dir,
            "icons",
            "icon.svg",
        )

        self.action = QAction(
            QIcon(icon_path),
            "Farm Overlap Checker",
            self.iface.mainWindow(),
        )

        self.action.setWhatsThis(
            "Identify overlapping farm polygons "
            "using configurable overlap thresholds."
        )

        self.action.triggered.connect(self.run)

        self.iface.addPluginToMenu(
            "&Farm Overlap Checker",
            self.action,
        )

        self.iface.addToolBarIcon(self.action)

    # --------------------------------------------------
    # OPEN STANDALONE PLUGIN DIALOG
    # --------------------------------------------------

    def run(self):

        if self.dialog is None:

            self.dialog = OverlapCheckerDialog(
                self.iface,
                self.iface.mainWindow(),
            )

        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    # --------------------------------------------------
    # UNLOAD PLUGIN
    # --------------------------------------------------

    def unload(self):

        # ----------------------------------------------
        # Remove standalone interface
        # ----------------------------------------------

        if self.action is not None:

            self.iface.removePluginMenu(
                "&Farm Overlap Checker",
                self.action,
            )

            self.iface.removeToolBarIcon(
                self.action
            )

            self.action.deleteLater()
            self.action = None

        if self.dialog is not None:

            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None

        # ----------------------------------------------
        # Unregister Processing provider
        # ----------------------------------------------

        if self.provider is not None:

            QgsApplication.processingRegistry().removeProvider(
                self.provider
            )

            self.provider = None

            QgsMessageLog.logMessage(
                "Farm Overlap Checker Processing provider removed.",
                "Farm Overlap Checker",
            )
