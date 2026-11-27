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
