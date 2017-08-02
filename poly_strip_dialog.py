# -*- coding: utf-8 -*-
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

import os

from PyQt4 import QtGui, uic
from poly_strip_alg import getAllPages

from qgis.gui import QgsGenericProjectionSelector

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'poly_strip_dialog_base.ui'))


class PolyStripDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PolyStripDialog, self).__init__(parent)
        self.setupUi(self)

    def polystrip(self, layer):
        if self.crsBoxSelect.isChecked():
            srid = PolyStripDialog().crsselectauto(layer)
        else:
            srid = PolyStripDialog().crsselect()
        width = self.widthSpinBox.value()
        height = self.heightSpinBox.value()
        coverage = self.coverSpinBox.value() / 100.0
        getAllPages(layer, width, height, srid, coverage)

    def crsselect(self):
        projSelector = QgsGenericProjectionSelector()
        projSelector.exec_()
        srid = projSelector.selectedAuthId()
        return srid

    def crsselectauto(self, layer):
        srid = layer.crs().authid()
        return srid

