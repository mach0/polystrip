# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PolyStrip
                                 A QGIS plugin
 Polygons along lines 
                             -------------------
        begin                : 2017-07-29
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PolyStrip class from file PolyStrip.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .poly_strip import PolyStrip
    return PolyStrip(iface)
