#!python
# coding: utf-8

# https://gis.stackexchange.com/questions/173127/generating-equal-sized-polygons-along-line-with-pyqgis
from qgis.core import QgsMapLayerRegistry, QgsGeometry, QgsField, QgsFeature, QgsPoint, QGis, QgsVectorLayer
from PyQt4.QtCore import QVariant


def getAllPages(layer, width, height, srid, overlap):
    for feature in layer.selectedFeatures():
        geom = feature.geometry()
        if geom.type() != QGis.Line:
            print "Geometry type should be a LineString"
            return 2
        pages = QgsVectorLayer("Polygon?crs=epsg:"+str(srid),
                               layer.name()+'_id_'+str(feature.id())+'_pages',
                               "memory")
        fid = QgsField("fid", QVariant.Int, "int")
        angle = QgsField("angle", QVariant.Double, "double")
        attributes = [fid, angle]
        pages.startEditing()
        pagesProvider = pages.dataProvider()
        pagesProvider.addAttributes(attributes)
        curs = 0
        numpages = geom.length()/width
        step = 1.0/numpages
        stepnudge = (1.0-overlap) * step
        pageFeatures = []
        r = 1
        # currangle = 0
        while curs <= 1:
            startpoint = geom.interpolate(curs*geom.length())
            endpoint = geom.interpolate((curs+step)*geom.length())
            x_start = startpoint.asPoint().x()
            y_start = startpoint.asPoint().y()
            x_end = endpoint.asPoint().x()
            y_end = endpoint.asPoint().y()
            currpoly = QgsGeometry().fromWkt(
                'POLYGON((0 0, 0 {height},{width} {height}, {width} 0, 0 0))'.format(height=height, width=width))
            currpoly.translate(0,-height/2)
            azimuth = startpoint.asPoint().azimuth(endpoint.asPoint())
            currangle = (azimuth+270) % 360
            currpoly.rotate(currangle, QgsPoint(0,0))
            currpoly.translate(x_start, y_start)
            currpoly.asPolygon()
            page = currpoly
            curs = curs + stepnudge
            feat = QgsFeature()
            feat.setAttributes([r, currangle])
            feat.setGeometry(page)
            pageFeatures.append(feat)
            r = r + 1
        pagesProvider.addFeatures(pageFeatures)
        pages.commitChanges()
        QgsMapLayerRegistry.instance().addMapLayer(pages)
    return 0
