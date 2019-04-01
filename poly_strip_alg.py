#!python
# coding: utf-8
"""
/***************************************************************************
 PolyStripDialog
                                 A QGIS plugin
 Polygons along lines
                             -------------------
        begin                : 2017-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# following code mostly taken from
# https://gis.stackexchange.com/questions/173127/generating-equal-sized-polygons-along-line-with-pyqgis

from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsField,
    QgsFeature,
    QgsPointXY,
    QgsVectorLayer,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import (
    QVariant
)


def get_all_pages(layer, width, height, srid, coverage, covstart):

    for feature in layer.selectedFeatures():
        geom = feature.geometry()
        if geom.type() != QgsWkbTypes.LineGeometry:
            print("Geometry type should be a LineString")
            return 2
        extended_geom = QgsGeometry.extendLine(geom, covstart, coverage)
        pages = QgsVectorLayer("Polygon?crs="+str(srid),
                               layer.name()+'_id_'+str(feature.id())+'_strip',
                               "memory")
        fid = QgsField("fid", QVariant.Int, "int")
        angle = QgsField("angle", QVariant.Double, "double")
        atlas = QgsField("atl_ang", QVariant.Double, "double")
        attributes = [fid, angle, atlas]
        pages.startEditing()
        pages_provider = pages.dataProvider()
        pages_provider.addAttributes(attributes)
        curs = 0
        geomlength = geom.length()
        numpages = geomlength / width
        step = 1.0 / numpages
        stepnudge = (1.0 - (coverage/100)) * step
        page_features = []
        r = 1
        while curs <= 1:
            startpoint = extended_geom.interpolate(curs*geomlength)
            # interpolate returns no geometry when > 1
            forward = (curs+step)
            if forward > 1:
                forward = 1
            endpoint = extended_geom.interpolate(forward*geomlength)
            x_start = startpoint.asPoint().x()
            y_start = startpoint.asPoint().y()
            currpoly = QgsGeometry().fromWkt(
                'POLYGON((0 0, 0 {height},{width} {height}, {width} 0, 0 0))'.format(height=height, width=width))
            currpoly.translate(0, -height/2)
            azimuth = startpoint.asPoint().azimuth(endpoint.asPoint())
            currangle = (azimuth+270) % 360
            curratlas = 360-currangle
            currpoly.rotate(currangle, QgsPointXY(0, 0))
            currpoly.translate(x_start, y_start)
            currpoly.asPolygon()
            page = currpoly
            curs = curs + stepnudge
            feat = QgsFeature()
            feat.setAttributes([r, currangle, curratlas])
            feat.setGeometry(page)
            page_features.append(feat)
            r = r + 1
        pages_provider.addFeatures(page_features)
        pages.commitChanges()
        QgsProject.instance().addMapLayer(pages)
    return 0
