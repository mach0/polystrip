# coding: utf-8
"""
 PolyStripDialog
                                 A QGIS plugin
 Polygons along lines
                             -------------------
        begin                : 2017-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com
"""

from typing import List

from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsField,
    QgsVectorLayer,
    QgsSymbol,
    QgsSingleSymbolRenderer,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCsException,
    QgsMessageLog,
    Qgis
)
from qgis.PyQt.QtCore import Qt
try:
    from qgis.PyQt.QtCore import QMetaType
    type_int = QMetaType.Type.Int
    type_double = QMetaType.Type.Double
except (ImportError, AttributeError):
    from qgis.PyQt.QtCore import QVariant
    type_int = QVariant.Int
    type_double = QVariant.Double

from . import polystrip_line_following
from . import polystrip_north_up


def extract_linestrings(geom: QgsGeometry) -> List[QgsGeometry]:
    """
    Extract individual LineString geometries from a Line or MultiLine geometry.
    Ensures that geometric operations like extendLine and interpolate work accurately.
    """
    if not geom or geom.isEmpty():
        return []
    
    if geom.isMultipart():
        lines = []
        try:
            for part in geom.asGeometryCollection():
                if part.type() == QgsWkbTypes.LineGeometry and not part.isEmpty() and part.length() > 0:
                    lines.append(part)
        except Exception:
            pass
        if not lines:
            try:
                for polyline in geom.asMultiPolyline():
                    part = QgsGeometry.fromPolylineXY(polyline)
                    if not part.isEmpty() and part.length() > 0:
                        lines.append(part)
            except Exception:
                pass
        return lines
    else:
        return [QgsGeometry(geom)] if geom.length() > 0 else []


def get_all_pages(
    layer: QgsVectorLayer,
    width: float,
    height: float,
    srid: QgsCoordinateReferenceSystem,
    coverage: float,
    covstart: float,
    follow_line_direction: bool = True
) -> int:
    """
    Generate polygon pages along selected line features.
    
    Args:
        layer: Vector layer containing line features
        width: Polygon width
        height: Polygon height
        srid: Spatial reference system for output layer
        coverage: Coverage percentage for overlap
        covstart: Start offset distance
        follow_line_direction: If True, polygons follow line direction; if False, north-up orientation
    
    Returns:
        Total number of polygons created on success, or negative error code on failure
    """
    selected_features = layer.selectedFeatures()
    
    if not selected_features:
        QgsMessageLog.logMessage("No features selected", "PolyStrip", Qgis.Warning)
        return -1
    
    total_created = 0
    transform = None
    if srid and srid.isValid() and layer.crs().isValid() and srid != layer.crs():
        try:
            transform = QgsCoordinateTransform(layer.crs(), srid, QgsProject.instance())
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to create CRS transform: {e}", "PolyStrip", Qgis.Warning)
            transform = None

    for feature in selected_features:
        geom = feature.geometry()
        
        if not geom or geom.type() != QgsWkbTypes.LineGeometry or geom.isEmpty():
            QgsMessageLog.logMessage(
                f"Feature {feature.id()} is not a valid LineGeometry", 
                "PolyStrip", 
                Qgis.Warning
            )
            continue
        
        line_parts = extract_linestrings(geom)
        if not line_parts:
            QgsMessageLog.logMessage(
                f"Feature {feature.id()} has zero length or empty geometry", 
                "PolyStrip", 
                Qgis.Warning
            )
            continue

        layer_name = f"{layer.name()}_id_{feature.id()}_strip"
        crs_def = srid.authid() if (srid and srid.isValid()) else layer.crs().authid()
        pages = QgsVectorLayer(f"Polygon?crs={crs_def}", layer_name, "memory")
        if srid and srid.isValid():
            pages.setCrs(srid)
        
        # Create attributes compatible with both Qt5 and Qt6
        attributes = [
            QgsField("page", type_int, len=10),
            QgsField("angle", type_double, len=10, prec=2),
            QgsField("atlas", type_double, len=10, prec=2)
        ]
        
        pages_provider = pages.dataProvider()
        pages_provider.addAttributes(attributes)
        pages.updateFields()
        
        page_features = []
        page_start_num = 1
        
        for part in line_parts:
            part_len = part.length()
            if part_len <= 0:
                continue

            # Extend line by covstart at both ends if covstart > 0
            if covstart > 0:
                extended_part = part.extendLine(covstart, covstart)
                if not extended_part or extended_part.isEmpty():
                    extended_part = QgsGeometry(part)
            else:
                extended_part = QgsGeometry(part)

            ext_len = extended_part.length()
            if ext_len <= 0:
                extended_part = QgsGeometry(part)
                ext_len = part_len

            # Choose algorithm based on orientation mode
            if follow_line_direction:
                count = polystrip_line_following.create_line_following_polygons(
                    extended_part, part, part_len, ext_len, 
                    width, height, coverage, covstart, page_features, page_start_num)
            else:
                count = polystrip_north_up.create_north_up_polygons(
                    extended_part, part, part_len, ext_len, 
                    width, height, coverage, covstart, page_features, page_start_num)
            
            page_start_num += count
        
        if not page_features:
            continue

        # Transform geometries if destination CRS differs from layer CRS
        if transform:
            for feat in page_features:
                try:
                    fg = feat.geometry()
                    fg.transform(transform)
                    feat.setGeometry(fg)
                except (QgsCsException, Exception) as e:
                    QgsMessageLog.logMessage(f"CRS transformation error: {e}", "PolyStrip", Qgis.Warning)

        pages_provider.addFeatures(page_features)
        
        # Set polygon style to outline only (no fill)
        symbol = QgsSymbol.defaultSymbol(pages.geometryType())
        if symbol and symbol.symbolLayerCount() > 0:
            no_brush = getattr(Qt, 'NoBrush', getattr(getattr(Qt, 'BrushStyle', None), 'NoBrush', 0))
            symbol.symbolLayer(0).setBrushStyle(no_brush)
            pages.setRenderer(QgsSingleSymbolRenderer(symbol))
        
        # Add to project
        QgsProject.instance().addMapLayer(pages)
        total_created += len(page_features)
        
        QgsMessageLog.logMessage(
            f"Created {len(page_features)} polygons for feature {feature.id()}", 
            "PolyStrip", 
            Qgis.Info
        )
    
    return total_created
