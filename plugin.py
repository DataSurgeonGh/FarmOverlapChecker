
import os

from qgis.PyQt.QtGui import QIcon

# QAction moved from QtWidgets to QtGui in Qt 6.
# This fallback supports both Qt 5 and Qt 6.
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from .dialog import OverlapCheckerDialog


class FarmOverlapCheckerPlugin:

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.action = None
        self.dialog = None

    # --------------------------------------------------
    # INITIALISE PLUGIN
    # --------------------------------------------------

    def initGui(self):

        icon_path = os.path.join(
            self.plugin_dir,
            "icons",
            "icon.svg"
        )

        self.action = QAction(
            QIcon(icon_path),
            "Farm Overlap Checker",
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
    # OPEN PLUGIN DIALOG
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

        if self.action is not None:

            self.iface.removePluginMenu(
                "&Farm Overlap Checker",
                self.action
            )

            self.iface.removeToolBarIcon(self.action)

            self.action.deleteLater()
            self.action = None

        if self.dialog is not None:

            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
