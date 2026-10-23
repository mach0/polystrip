# -*- coding: utf-8 -*-
"""
Mock implementation of essential QGIS classes for standalone unit testing
when QGIS is not installed in the host Python environment.
"""

import math
import sys
from unittest.mock import MagicMock


class MockPointXY:
    def __init__(self, x=0.0, y=0.0):
        self._x = float(x)
        self._y = float(y)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def azimuth(self, other):
        dx = other.x() - self._x
        dy = other.y() - self._y
        angle = math.degrees(math.atan2(dx, dy))
        return (angle + 360.0) % 360.0

    def __eq__(self, other):
        if not isinstance(other, MockPointXY):
            return False
        return math.isclose(self._x, other.x(), abs_tol=1e-7) and math.isclose(self._y, other.y(), abs_tol=1e-7)


class MockRectangle:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = min(xmin, xmax)
        self.ymin = min(ymin, ymax)
        self.xmax = max(xmin, xmax)
        self.ymax = max(ymin, ymax)

    def contains(self, point_or_rect):
        if hasattr(point_or_rect, 'x'):
            return self.xmin <= point_or_rect.x() <= self.xmax and self.ymin <= point_or_rect.y() <= self.ymax
        return (self.xmin <= point_or_rect.xmin and point_or_rect.xmax <= self.xmax and
                self.ymin <= point_or_rect.ymin and point_or_rect.ymax <= self.ymax)


class MockGeometry:
    def __init__(self, wkt=""):
        self._wkt = wkt
        self._length = 1000.0
        self._bbox = MockRectangle(0, 0, 1000, 1000)

    @classmethod
    def fromRect(cls, rect):
        g = cls(f"POLYGON(({rect.xmin} {rect.ymin}, {rect.xmax} {rect.ymin}, ...))")
        g._bbox = rect
        return g

    @classmethod
    def fromPolylineXY(cls, points):
        g = cls("LINESTRING(...)")
        if points:
            xs = [p.x() for p in points]
            ys = [p.y() for p in points]
            g._bbox = MockRectangle(min(xs), min(ys), max(xs), max(ys))
        return g

    def isEmpty(self):
        return False

    def isMultipart(self):
        return False

    def type(self):
        return 1  # LineGeometry

    def length(self):
        return self._length

    def extendLine(self, start_dist, end_dist):
        g = MockGeometry(self._wkt)
        g._length = self._length + start_dist + end_dist
        return g

    def interpolate(self, dist):
        pt_geom = MockGeometry()
        pt_geom.asPoint = lambda: MockPointXY(dist, 0.0)
        return pt_geom

    def boundingBox(self):
        return self._bbox

    def rotate(self, angle, center):
        pass

    def translate(self, dx, dy):
        self._bbox = MockRectangle(
            self._bbox.xmin + dx, self._bbox.ymin + dy,
            self._bbox.xmax + dx, self._bbox.ymax + dy
        )

    def intersects(self, other):
        return True


class MockFeature:
    def __init__(self, fid=1):
        self._fid = fid
        self._geom = None
        self._attrs = []

    def id(self):
        return self._fid

    def setGeometry(self, geom):
        self._geom = geom

    def geometry(self):
        return self._geom

    def setAttributes(self, attrs):
        self._attrs = attrs

    def attributes(self):
        return self._attrs


class MockProcessingAlgorithm:
    pass


class MockProcessingProvider:
    pass


def install_mock_qgis():
    """Install mock modules if qgis is not present."""
    if 'qgis' in sys.modules:
        return

    qgis = MagicMock()
    qgis_core = MagicMock()
    qgis_core.QgsGeometry = MockGeometry
    qgis_core.QgsFeature = MockFeature
    qgis_core.QgsPointXY = MockPointXY
    qgis_core.QgsRectangle = MockRectangle
    qgis_core.QgsProcessingAlgorithm = MockProcessingAlgorithm
    qgis_core.QgsProcessingProvider = MockProcessingProvider
    qgis_core.QgsWkbTypes.LineGeometry = 1
    qgis_core.QgsWkbTypes.Polygon = 2
    qgis.core = qgis_core
    sys.modules['qgis'] = qgis
    sys.modules['qgis.core'] = qgis_core
    sys.modules['qgis.gui'] = MagicMock()
    
    qt_core = MagicMock()
    qt_core.QCoreApplication.translate = lambda ctx, text, *args: text
    sys.modules['qgis.PyQt'] = MagicMock()
    sys.modules['qgis.PyQt.QtCore'] = qt_core
    sys.modules['qgis.PyQt.QtGui'] = MagicMock()
    sys.modules['qgis.PyQt.QtWidgets'] = MagicMock()
