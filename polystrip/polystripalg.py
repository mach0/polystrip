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
    type_string = QMetaType.Type.QString
except (ImportError, AttributeError):
    from qgis.PyQt.QtCore import QVariant
    type_int = QVariant.Int
    type_double = QVariant.Double
    type_string = QVariant.String

# Standard ISO Paper Formats in millimeters: (width_mm, height_mm)
PAPER_FORMATS = {
    'Custom': None,
    'ISO A0 (Landscape - 1189 x 841 mm)': (1189.0, 841.0),
    'ISO A0 (Portrait - 841 x 1189 mm)': (841.0, 1189.0),
    'ISO A1 (Landscape - 841 x 594 mm)': (841.0, 594.0),
    'ISO A1 (Portrait - 594 x 841 mm)': (594.0, 841.0),
    'ISO A2 (Landscape - 594 x 420 mm)': (594.0, 420.0),
    'ISO A2 (Portrait - 420 x 594 mm)': (420.0, 594.0),
    'ISO A3 (Landscape - 420 x 297 mm)': (420.0, 297.0),
    'ISO A3 (Portrait - 297 x 420 mm)': (297.0, 420.0),
    'ISO A4 (Landscape - 297 x 210 mm)': (297.0, 210.0),
    'ISO A4 (Portrait - 210 x 297 mm)': (210.0, 297.0),
    'ISO A5 (Landscape - 210 x 148 mm)': (210.0, 148.0),
    'ISO A5 (Portrait - 148 x 210 mm)': (148.0, 210.0),
}


def calculate_ground_dimensions(
    paper_width_mm: float,
    paper_height_mm: float,
    scale_denominator: float,
    margin_mm: float = 0.0
) -> tuple:
    """
    Calculate ground dimensions (width, height) in meters from paper dimensions (mm), scale, and margin.
    Margin is subtracted from both sides: effective = max(1.0, paper_dim - 2 * margin).
    Example: A4 Landscape (297x210 mm) with 10 mm margin at 1:8000 -> (2216.0 m, 1520.0 m)
    """
    effective_w_mm = max(1.0, float(paper_width_mm) - 2.0 * float(margin_mm))
    effective_h_mm = max(1.0, float(paper_height_mm) - 2.0 * float(margin_mm))
    ground_width_m = (effective_w_mm / 1000.0) * float(scale_denominator)
    ground_height_m = (effective_h_mm / 1000.0) * float(scale_denominator)
    return ground_width_m, ground_height_m

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
    follow_line_direction: bool = True,
    paper_format: str = "Custom",
    scale: int = 0,
    margin_mm: float = 0.0
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
        paper_format: Name of the paper format preset (e.g. 'A4 Landscape') or 'Custom'
        scale: Scale denominator (e.g. 8000 for 1:8000)
        margin_mm: Page margin in mm subtracted from paper dimensions
    
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
            QgsField("atlas", type_double, len=10, prec=2),
            QgsField("paper", type_string, len=50),
            QgsField("scale", type_int, len=10),
            QgsField("margin_mm", type_double, len=10, prec=1)
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

        # Attach paper format, scale, and margin_mm attributes to all generated features
        for feat in page_features:
            attrs = list(feat.attributes())
            if len(attrs) == 3:
                attrs.extend([paper_format, scale, margin_mm])
                feat.setAttributes(attrs)

        # Transform geometries if destination CRS differs from layer CRS
        if transform:
            for feat in page_features:
                try:
                    fg = feat.geometry()
                    fg.transform(transform)
                    feat.setGeometry(fg)
                except Exception as e:
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
