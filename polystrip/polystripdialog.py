# coding: utf-8
"""
 PolyStripDialog
                                 A QGIS plugin
 Polygons along lines 
                             -------------------
        begin                : 2017-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com
"""

import os
from typing import Optional, Dict

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QComboBox
from qgis.core import (
    QgsUnitTypes,
    QgsVectorLayer,
    QgsMapLayer,
    QgsCoordinateReferenceSystem
)
from qgis.gui import QgisInterface
from .polystripalg import get_all_pages


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'polystripdialog.ui'))


class PolyStripDialog(QDialog, FORM_CLASS):
    def __init__(self, parent: Optional[QDialog] = None, iface: Optional[QgisInterface] = None):
        """Constructor."""
        super(PolyStripDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.current_layer_unit = None
        
        # Populate unit comboboxes with all QGIS distance units
        self.populate_unit_comboboxes()
        
        # Connect to layer changes if iface is available
        if self.iface:
            self.iface.currentLayerChanged.connect(self.on_active_layer_changed)
            self.update_unit_display()
    
    def populate_unit_comboboxes(self) -> None:
        """Populate all unit comboboxes with available distance units."""
        # Get all distance units supported by QGIS
        distance_units = [
            QgsUnitTypes.DistanceMeters,
            QgsUnitTypes.DistanceKilometers,
            QgsUnitTypes.DistanceFeet,
            QgsUnitTypes.DistanceNauticalMiles,
            QgsUnitTypes.DistanceYards,
            QgsUnitTypes.DistanceMiles,
            QgsUnitTypes.DistanceDegrees,
            QgsUnitTypes.DistanceCentimeters,
            QgsUnitTypes.DistanceMillimeters
        ]
        
        # Populate each combobox
        for combo in [self.widthUnitComboBox, self.heightUnitComboBox, self.offsetUnitComboBox]:
            combo.clear()
            for unit in distance_units:
                unit_name = QgsUnitTypes.toString(unit)
                combo.addItem(unit_name, unit)
            
            # Set default to meters
            combo.setCurrentIndex(0)

    def polystrip(self, layer: QgsVectorLayer) -> int:
        """Execute the polystrip algorithm with current dialog settings."""
        # Determine CRS
        if self.crsBoxSelect.isChecked():
            srid = layer.crs()
        else:
            srid = layer.crs()
        
        # Get parameters from UI and convert to layer units
        width = self.get_converted_value(
            self.widthSpinBox.value(),
            self.widthUnitComboBox.currentData()
        )
        height = self.get_converted_value(
            self.heightSpinBox.value(),
            self.heightUnitComboBox.currentData()
        )
        coverage = self.coverSpinBox.value()
        covstart = self.get_converted_value(
            self.coverSpinBoxStart.value(),
            self.offsetUnitComboBox.currentData()
        )
        follow_line_direction = self.followLineCheckBox.isChecked()
        
        return get_all_pages(layer, width, height, srid, coverage, covstart, follow_line_direction)

    def labelwriter(self, unitstr: str) -> None:
        """Update the unit label in the dialog."""
        self.label_unit.setText(unitstr)
    
    def get_converted_value(self, value: float, from_unit: QgsUnitTypes.DistanceUnit) -> float:
        """Convert input value from specified unit to layer unit."""
        if self.current_layer_unit is None or from_unit is None:
            return value
        
        # Convert using QGIS unit conversion
        return QgsUnitTypes.fromUnitToUnitFactor(from_unit, self.current_layer_unit) * value

    def on_active_layer_changed(self, layer: Optional[QgsMapLayer]) -> None:
        """Handle active layer changes and update unit display."""
        self.update_unit_display()
    
    def update_unit_display(self) -> None:
        """Update the unit display based on the current active layer."""
        if not self.iface:
            return
            
        active_layer = self.iface.activeLayer()
        if active_layer and active_layer.crs().isValid():
            # Get the units from the layer's CRS
            layer_crs = active_layer.crs()
            unit = layer_crs.mapUnits()
            unit_strg = QgsUnitTypes.toString(unit)
        else:
            # Fallback to canvas units
            unit = self.iface.mapCanvas().mapUnits()
            unit_strg = QgsUnitTypes.toString(unit)
        
        # Update the label
        self.labelwriter(unit_strg)
        self.current_layer_unit = unit
        
        # Set the unit comboboxes to match layer unit by default
        for combo in [self.widthUnitComboBox, self.heightUnitComboBox, self.offsetUnitComboBox]:
            index = combo.findData(unit)
            if index >= 0:
                combo.setCurrentIndex(index)

    def closeEvent(self, event) -> None:
        """Handle dialog close event to disconnect signals."""
        if self.iface:
            try:
                self.iface.currentLayerChanged.disconnect(self.on_active_layer_changed)
            except TypeError:
                # Signal might not be connected
                pass
        super().closeEvent(event)
    
    def reject(self) -> None:
        """Handle dialog rejection (Cancel button)."""
        if self.iface:
            try:
                self.iface.currentLayerChanged.disconnect(self.on_active_layer_changed)
            except TypeError:
                # Signal might not be connected
                pass
        super().reject()
