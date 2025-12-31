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
from qgis.core import QgsGeometry, QgsFeature, QgsPointXY


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
    Create polygons that follow the line direction
    
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
    # Calculate step size and coverage
    extension_ratio = covstart / extended_geomlength if extended_geomlength > 0 else 0
    numpages = geomlength / width
    step = (geomlength / extended_geomlength) / numpages
    stepnudge = (1.0 - (coverage / 100)) * step
    
    # Start half a step before the original line start to center it in the first polygon
    cursor_position = max(0, extension_ratio - step / 2)
    
    # Calculate end position on extended geometry
    end_ratio = (covstart + geomlength) / extended_geomlength if extended_geomlength > 0 else 1
    
    # Calculate exact end point of the original line for coverage check
    original_end_dist = covstart + geomlength
    original_end_geom = extended_geom.interpolate(original_end_dist)
    
    page_number = r
    
    while cursor_position <= end_ratio:
        # Optimization: Check if the end of the line is already covered by the previous polygon
        if len(page_features) > 0 and original_end_geom and not original_end_geom.isEmpty():
            # If the last added polygon contains the end point, we don't need another one
            if page_features[-1].geometry().contains(original_end_geom):
                break
                
        # Get start and end points for this polygon segment
        startpoint = extended_geom.interpolate(cursor_position * extended_geomlength)
        forward = min(cursor_position + step, end_ratio)
        endpoint = extended_geom.interpolate(forward * extended_geomlength)
        
        if not startpoint or not endpoint:
            break
            
        x_start = startpoint.asPoint().x()
        y_start = startpoint.asPoint().y()
        
        # Create polygon
        currpoly = QgsGeometry().fromWkt(
            f'POLYGON((0 0, 0 {height}, {width} {height}, {width} 0, 0 0))')
        currpoly.translate(0, -height / 2)
        
        # Calculate rotation using azimuth
        azimuth = startpoint.asPoint().azimuth(endpoint.asPoint())
        currangle = (azimuth + 270) % 360
        curratlas = 360 - currangle
        
        # Rotate and translate to final position
        currpoly.rotate(currangle, QgsPointXY(0, 0))
        currpoly.translate(x_start, y_start)
        
        # Create feature
        feat = QgsFeature()
        feat.setAttributes([page_number, currangle, curratlas])
        feat.setGeometry(currpoly)
        page_features.append(feat)
        
        page_number += 1
        cursor_position += stepnudge
    
    return len(page_features) - (r - 1)
