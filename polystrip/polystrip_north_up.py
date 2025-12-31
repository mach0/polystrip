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
from qgis.core import QgsGeometry, QgsFeature, QgsPointXY


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
    Create polygons with north-up orientation along the line
    
    For north-up polygons, we need to calculate the step distance based on
    the line's direction at each point, since the polygon's projection onto
    the line varies with the line's bearing.
    
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
    # Start at the beginning of the original line (accounting for extension)
    current_distance = covstart
    
    # End at the end of the original line
    end_distance = covstart + geomlength
    
    page_number = r
    
    # Keep track of previous polygon center
    prev_x = None
    prev_y = None
    
    # Calculate end point of the original line for coverage check
    end_point_geom = extended_geom.interpolate(end_distance)
    
    # Create north-up polygons along the line
    # Loop until we are past the end AND the end is covered
    while True:
        # Get the center point for this polygon on the extended geometry
        center_point = extended_geom.interpolate(current_distance)
        
        if not center_point:
            break
        
        x_center = center_point.asPoint().x()
        y_center = center_point.asPoint().y()
        
        # Check connectivity with previous polygon
        if prev_x is not None:
            dx = abs(x_center - prev_x)
            dy = abs(y_center - prev_y)
            
            limit_x = width * (100.0 - coverage) / 100.0
            limit_y = height * (100.0 - coverage) / 100.0
            
            if dx > limit_x or dy > limit_y:
                step_reduction = step_distance * 0.2
                current_distance -= step_reduction
                step_distance *= 0.8
                continue
        
        # Calculate step distance for next iteration
        lookahead_distance = min(current_distance + 1.0, end_distance)
        lookahead_point = extended_geom.interpolate(lookahead_distance)
        
        if lookahead_point:
            azimuth = center_point.asPoint().azimuth(lookahead_point.asPoint())
            angle_rad = math.radians(azimuth)
            
            height_projection = abs(height * math.cos(angle_rad))
            width_projection = abs(width * math.sin(angle_rad))
            
            projection = max(height_projection, width_projection)
            projection = max(projection, min(height, width) * 0.25)
            
            step_distance = projection * (100.0 - coverage) / 100.0
        else:
            step_distance = min(height, width) * 0.5
            
        # Create polygon
        currpoly = QgsGeometry().fromWkt(
            f'POLYGON((0 0, 0 {height}, {width} {height}, {width} 0, 0 0))')
        currpoly.translate(-width / 2, -height / 2)
        currangle = 0.0
        curratlas = 360.0 - currangle
        currpoly.translate(x_center, y_center)
        
        feat = QgsFeature()
        feat.setAttributes([page_number, currangle, curratlas])
        feat.setGeometry(currpoly)
        page_features.append(feat)
        
        # Update state
        prev_x = x_center
        prev_y = y_center
        page_number += 1
        current_distance += step_distance
        
        # Check termination condition:
        # If we passed the end distance...
        if current_distance > end_distance:
            # Check if the end point is covered by the polygon we just created
            if end_point_geom and feat.geometry().contains(end_point_geom):
                break
            
            # Safety break: if we are way past the end (more than one max-dimension)
            # This handles cases where contains() fails or geometry is weird
            if current_distance > end_distance + max(width, height):
                break
            
            # Otherwise, loop continues to add one more polygon to cover the end
    
    return len(page_features) - (r - 1)
