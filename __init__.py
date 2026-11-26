
def classFactory(iface):
    """
    QGIS plugin entry point.

    iface provides access to the running QGIS application.
    """
    from .plugin import FarmOverlapCheckerPlugin

    return FarmOverlapCheckerPlugin(iface)
