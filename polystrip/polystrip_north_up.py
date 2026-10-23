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

North-up polygon algorithm for PolyStrip plugin
Polygons maintain north-up orientation regardless of line direction
"""

from typing import List
import math
from qgis.core import QgsGeometry, QgsFeature, QgsRectangle


def create_north_up_polygons(
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
    Create polygons with north-up orientation along the line.
    
    Args:
        extended_geom: Extended line geometry
        geom: Original line geometry
        geomlength: Original geometry length
        extended_geomlength: Extended geometry length
        width: Polygon width (east-west extent)
        height: Polygon height (north-south extent)
        coverage: Coverage percentage for overlap
        covstart: Start offset distance
        page_features: List to append features to
        r: Starting polygon number
        
    Returns:
        Number of polygons created
    """
    if extended_geomlength <= 0 or width <= 0 or height <= 0:
        return 0

    safe_coverage = max(0.0, min(float(coverage), 95.0))
    overlap_factor = (100.0 - safe_coverage) / 100.0

    current_distance = covstart
    end_distance = covstart + geomlength
    page_number = r
    
    prev_x = None
    prev_y = None
    retries = 0
    max_retries = 5
    step_distance = min(width, height) * 0.5 * overlap_factor

    # End point geometry of original line for termination check
    original_end_geom = extended_geom.interpolate(end_distance)
    if original_end_geom is None or original_end_geom.isEmpty():
        original_end_geom = geom.interpolate(geomlength)
    end_pt = original_end_geom.asPoint() if original_end_geom and not original_end_geom.isEmpty() else None

    # Safety limit for iterations
    max_iterations = max(500, int((geomlength + 2 * covstart) / (step_distance or 1.0)) * 3 + 100)
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        center_point = extended_geom.interpolate(current_distance)
        if not center_point or center_point.isEmpty():
            break
        
        x_center = center_point.asPoint().x()
        y_center = center_point.asPoint().y()
        
        # Check connectivity with previous polygon to prevent gaps
        if prev_x is not None and retries < max_retries:
            dx = abs(x_center - prev_x)
            dy = abs(y_center - prev_y)
            
            limit_x = width * overlap_factor
            limit_y = height * overlap_factor
            
            if dx > limit_x or dy > limit_y:
                retries += 1
                step_reduction = step_distance * 0.2
                current_distance -= step_reduction
                step_distance *= 0.8
                continue

        retries = 0
        
        # Calculate step distance for next polygon
        lookahead_distance = min(current_distance + max(1.0, width * 0.1), extended_geomlength)
        lookahead_point = extended_geom.interpolate(lookahead_distance)
        
        if lookahead_point and not lookahead_point.isEmpty() and center_point.asPoint() != lookahead_point.asPoint():
            azimuth = center_point.asPoint().azimuth(lookahead_point.asPoint())
            angle_rad = math.radians(azimuth)
            
            height_projection = abs(height * math.cos(angle_rad))
            width_projection = abs(width * math.sin(angle_rad))
            
            projection = max(height_projection, width_projection)
            projection = max(projection, min(height, width) * 0.25)
            
            step_distance = max(projection * overlap_factor, min(width, height) * 0.05)
        else:
            step_distance = max(min(height, width) * 0.5 * overlap_factor, min(width, height) * 0.05)
            
        # Create north-up rectangle centered on (x_center, y_center)
        currpoly = QgsGeometry.fromRect(QgsRectangle(
            x_center - width / 2.0,
            y_center - height / 2.0,
            x_center + width / 2.0,
            y_center + height / 2.0
        ))
        
        currangle = 0.0
        curratlas = 0.0
        
        feat = QgsFeature()
        feat.setAttributes([page_number, currangle, curratlas])
        feat.setGeometry(currpoly)
        page_features.append(feat)
        
        prev_x = x_center
        prev_y = y_center
        page_number += 1
        current_distance += step_distance
        
        # Check termination condition
        if current_distance >= end_distance:
            if original_end_geom and end_pt is not None:
                poly_geom = feat.geometry()
                if poly_geom.boundingBox().contains(end_pt) and poly_geom.intersects(original_end_geom):
                    break
            if current_distance > end_distance + max(width, height):
                break
    
    return len(page_features) - (r - 1)
