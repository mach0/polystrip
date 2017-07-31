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

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'poly_strip_dialog_base.ui'))


class PolyStripDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PolyStripDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use auto connect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def polystrip(self, layer):
        width = self.widthSpinBox.value()
        height = self.heightSpinBox.value()
        getAllPages(layer, width, height, 31255, 0.4)
