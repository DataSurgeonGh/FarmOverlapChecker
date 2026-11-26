
from qgis.core import QgsProcessingProvider

from .algorithms import FarmOverlapAlgorithm


class FarmOverlapProvider(QgsProcessingProvider):

    def loadAlgorithms(self):

        self.addAlgorithm(
            FarmOverlapAlgorithm()
        )

    def id(self):
        return "farmoverlapchecker"

    def name(self):
        return "Farm Overlap Checker"

    def longName(self):
        return "Farm Overlap Checker Processing Provider"
