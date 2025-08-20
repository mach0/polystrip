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

from qgis.PyQt import (
    uic
)
from qgis.PyQt.QtWidgets import (
    QDialog
)
from qgis.core import (
    QgsUnitTypes
)
from .polystripalg import get_all_pages


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'polystripdialog.ui'))


class PolyStripDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        """Constructor."""
        super(PolyStripDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        
        # Connect to layer changes if iface is available
        if self.iface:
            # Connect to active layer changed signal
            self.iface.currentLayerChanged.connect(self.on_active_layer_changed)
            # Set initial unit display
            self.update_unit_display()

    def polystrip(self, layer):
        """Execute the polystrip algorithm with current dialog settings."""
        print("=== PolyStrip Debug ===")
        print(f"Layer: {layer.name()}")
        print(f"Layer CRS: {layer.crs().authid()}")
        print(f"Selected features: {layer.selectedFeatureCount()}")
        
        if self.crsBoxSelect.isChecked():
            # Use the layer's CRS object directly
            srid = layer.crs()
        else:
            # For now, always use layer CRS - custom CRS selection can be added later
            srid = layer.crs()
        
        width = self.widthSpinBox.value()
        height = self.heightSpinBox.value()
        coverage = self.coverSpinBox.value()
        covstart = self.coverSpinBoxStart.value()
        
        print(f"Parameters - Width: {width}, Height: {height}, Coverage: {coverage}, Start: {covstart}")
        print(f"CRS object: {srid.authid()}")
        
        result = get_all_pages(layer, width, height, srid, coverage, covstart)
        print(f"Algorithm result: {result}")
        return result

    def labelwriter(self, unitstr):
        """Update the unit label in the dialog."""
        self.label_unit.setText(unitstr)

    def on_active_layer_changed(self, layer):
        """Handle active layer changes and update unit display."""
        self.update_unit_display()
    
    def update_unit_display(self):
        """Update the unit display based on the current active layer."""
        if not self.iface:
            return
            
        active_layer = self.iface.activeLayer()
        if active_layer and active_layer.crs().isValid():
            # Get the units from the layer's CRS
            layer_crs = active_layer.crs()
            unit = layer_crs.mapUnits()
            unit_strg = QgsUnitTypes.encodeUnit(unit)
        else:
            # Fallback to canvas units
            unit = self.iface.mapCanvas().mapUnits()
            unit_strg = QgsUnitTypes.encodeUnit(unit)
        
        self.labelwriter(unit_strg)

    def closeEvent(self, event):
        """Handle dialog close event to disconnect signals."""
        if self.iface:
            try:
                self.iface.currentLayerChanged.disconnect(self.on_active_layer_changed)
            except TypeError:
                # Signal might not be connected
                pass
        super().closeEvent(event)
    
    def reject(self):
        """Handle dialog rejection (Cancel button)."""
        if self.iface:
            try:
                self.iface.currentLayerChanged.disconnect(self.on_active_layer_changed)
            except TypeError:
                # Signal might not be connected
                pass
        super().reject()
