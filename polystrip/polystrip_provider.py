# -*- coding: utf-8 -*-
"""
PolyStrip Processing Provider

Registers PolyStrip algorithms in the QGIS Processing framework.
"""

import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .polystrip_algorithm import PolyStripAlgorithm


class PolyStripProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(PolyStripAlgorithm())

    def id(self) -> str:
        return 'polystrip'

    def name(self) -> str:
        return self.tr('PolyStrip')

    def longName(self) -> str:
        return self.tr('PolyStrip - Polygons Along Lines')

    def icon(self) -> QIcon:
        icon_path = os.path.join(os.path.dirname(__file__), 'img', 'polystrip.svg')
        return QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

    def tr(self, string: str) -> str:
        return QCoreApplication.translate('PolyStripProvider', string)
