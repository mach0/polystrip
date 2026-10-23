# coding: utf-8
"""
 PolyStrip
                                 A QGIS plugin
 Polygons along lines 
                              -------------------
        begin                : 2017-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com

Line-following polygon algorithm for PolyStrip plugin
Polygons are rotated to follow the line direction
"""

from typing import List
from qgis.core import QgsGeometry, QgsFeature, QgsPointXY, QgsRectangle


def create_line_following_polygons(
    extended_geom: QgsGeometry,
    geom: QgsGeometry,
    geomlength: float,
    extended_geomlength: float,
    width: float,
    height: float,
    coverage: float,
    covstart: float,
    page_features: List[QgsFeature],
    r: int
) -> int:
    """
    Create polygons that follow the line direction.
    
    Args:
        extended_geom: Extended line geometry
        geom: Original geometry (for reference)
        geomlength: Original geometry length
        extended_geomlength: Extended geometry length
        width: Polygon width
        height: Polygon height  
        coverage: Coverage percentage for overlap
        covstart: Start offset distance (used in extension)
        page_features: List to append features to
        r: Starting polygon number
        
    Returns:
        Number of polygons created
    """
    if extended_geomlength <= 0 or width <= 0 or height <= 0:
        return 0

    # Ensure coverage is capped below 100% to guarantee forward progress
    safe_coverage = max(0.0, min(float(coverage), 95.0))
    
    # Calculate step size along the extended geometry
    step = width / extended_geomlength
    stepnudge = max((1.0 - (safe_coverage / 100.0)) * step, step * 0.05)
    
    # Extension ratio: position where the original line begins
    extension_ratio = covstart / extended_geomlength
    
    # Start half a step before original line start to center the beginning of the line
    cursor_position = max(0.0, extension_ratio - step / 2.0)
    
    # Calculate end position on extended geometry
    end_ratio = (covstart + geomlength) / extended_geomlength
    
    # Find original end point geometry for termination check
    original_end_dist = covstart + geomlength
    original_end_geom = extended_geom.interpolate(original_end_dist)
    if original_end_geom is None or original_end_geom.isEmpty():
        original_end_geom = geom.interpolate(geomlength)
    
    end_pt = original_end_geom.asPoint() if original_end_geom and not original_end_geom.isEmpty() else None
    page_number = r
    
    # Calculate safety limit for iterations
    max_iterations = max(500, int(extended_geomlength / (stepnudge * extended_geomlength)) * 2 + 100) if stepnudge > 0 else 500
    iteration = 0
    
    while cursor_position <= end_ratio and iteration < max_iterations:
        iteration += 1
        
        # Check if the end of the line is already covered by the previous polygon
        if page_features and end_pt is not None:
            prev_geom = page_features[-1].geometry()
            if prev_geom.boundingBox().contains(end_pt) and prev_geom.intersects(original_end_geom):
                break
                
        # Get start point for this polygon
        start_dist = cursor_position * extended_geomlength
        startpoint = extended_geom.interpolate(start_dist)
        if not startpoint or startpoint.isEmpty():
            break
            
        # Look ahead along extended geometry for line direction (not clamped to end_ratio)
        forward_dist = min(start_dist + width, extended_geomlength)
        endpoint = extended_geom.interpolate(forward_dist)
        
        # If start and end points coincide (e.g. at the extreme end), sample backwards for heading
        if not endpoint or endpoint.isEmpty() or endpoint.asPoint() == startpoint.asPoint():
            sample_back_dist = max(0.0, start_dist - max(1.0, min(width * 0.1, 10.0)))
            back_point = extended_geom.interpolate(sample_back_dist)
            if back_point and not back_point.isEmpty() and back_point.asPoint() != startpoint.asPoint():
                azimuth = back_point.asPoint().azimuth(startpoint.asPoint())
            else:
                azimuth = 90.0  # default heading
        else:
            azimuth = startpoint.asPoint().azimuth(endpoint.asPoint())

        x_start = startpoint.asPoint().x()
        y_start = startpoint.asPoint().y()
        
        # Calculate rotation using azimuth
        currangle = round((azimuth + 270.0) % 360.0, 2)
        curratlas = round((360.0 - currangle) % 360.0, 2)
        
        # Create rectangular polygon using fast fromRect
        currpoly = QgsGeometry.fromRect(QgsRectangle(0.0, -height / 2.0, width, height / 2.0))
        
        # Rotate and translate to final position
        currpoly.rotate(currangle, QgsPointXY(0.0, 0.0))
        currpoly.translate(x_start, y_start)
        
        # Create feature with attributes
        feat = QgsFeature()
        feat.setAttributes([page_number, currangle, curratlas])
        feat.setGeometry(currpoly)
        page_features.append(feat)
        
        page_number += 1
        cursor_position += stepnudge
    
    return len(page_features) - (r - 1)
