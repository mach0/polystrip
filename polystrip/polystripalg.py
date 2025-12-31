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

from typing import Optional
from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsField,
    QgsVectorLayer,
    QgsSymbol,
    QgsSingleSymbolRenderer,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsMessageLog,
    Qgis
)
from qgis.PyQt.QtCore import Qt, QVariant
from . import polystrip_line_following
from . import polystrip_north_up


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
    Generate polygon pages along selected line features
    
    Args:
        layer: Vector layer containing line features
        width: Polygon width
        height: Polygon height
        srid: Spatial reference system
        coverage: Coverage percentage for overlap
        covstart: Start offset distance
        follow_line_direction: If True, polygons follow line direction; if False, north-up orientation
    
    Returns:
        0 on success, error code on failure
    """
    selected_features = layer.selectedFeatures()
    
    if not selected_features:
        QgsMessageLog.logMessage("No features selected", "PolyStrip", Qgis.Warning)
        return 1
    
    for feature in selected_features:
        geom = feature.geometry()
        
        if geom.type() != QgsWkbTypes.LineGeometry:
            QgsMessageLog.logMessage(
                f"Feature {feature.id()} is not a LineString", 
                "PolyStrip", 
                Qgis.Warning
            )
            return 2
        
        # Extend line by covstart at both ends
        extended_geom = QgsGeometry.extendLine(geom, covstart, covstart)
        layer_name = f"{layer.name()}_id_{feature.id()}_strip"
        
        # Create the layer with proper CRS
        pages = QgsVectorLayer("Polygon", layer_name, "memory")
        pages.setCrs(srid)
        
        # Create attributes
        attributes = [
            QgsField("page", QVariant.Int, len=10),
            QgsField("angle", QVariant.Double, len=10, prec=2),
            QgsField("atlas", QVariant.Double, len=10, prec=2)
        ]
        
        pages.startEditing()
        pages_provider = pages.dataProvider()
        pages_provider.addAttributes(attributes)
        pages.updateFields()
        
        # Common parameters
        geomlength = geom.length()
        extended_geomlength = extended_geom.length()
        page_features = []
        
        # Choose algorithm based on orientation mode
        if follow_line_direction:
            polystrip_line_following.create_line_following_polygons(
                extended_geom, geom, geomlength, extended_geomlength, 
                width, height, coverage, covstart, page_features, 1)
        else:
            polystrip_north_up.create_north_up_polygons(
                extended_geom, geom, geomlength, extended_geomlength, 
                width, height, coverage, covstart, page_features, 1)
        
        
        pages_provider.addFeatures(page_features)
        pages.commitChanges()
        
        # Set polygon style to outline only (no fill)
        symbol = QgsSymbol.defaultSymbol(pages.geometryType())
        symbol.symbolLayer(0).setBrushStyle(Qt.BrushStyle.NoBrush)
        renderer = QgsSingleSymbolRenderer(symbol)
        pages.setRenderer(renderer)
        
        # Add to project
        QgsProject.instance().addMapLayer(pages)
        
        QgsMessageLog.logMessage(
            f"Created {len(page_features)} polygons for feature {feature.id()}", 
            "PolyStrip", 
            Qgis.Info
        )
    
    return 0
