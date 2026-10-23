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
from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import (
    QgsUnitTypes,
    QgsVectorLayer,
    QgsMapLayer,
    QgsCoordinateReferenceSystem
)
from qgis.gui import QgisInterface
from .polystripalg import get_all_pages, PAPER_FORMATS, calculate_ground_dimensions


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'polystripdialog.ui'))


class PolyStripDialog(QDialog, FORM_CLASS):
    def __init__(self, parent: Optional[QDialog] = None, iface: Optional[QgisInterface] = None):
        """Constructor."""
        super(PolyStripDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.current_layer_unit = None
        self.selected_crs = QgsCoordinateReferenceSystem()
        self._updating_dimensions = False
        
        # Set dialog icon explicitly
        icon_path = os.path.join(os.path.dirname(__file__), 'img', 'polystrip.svg')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Populate unit comboboxes with all QGIS distance units
        self.populate_unit_comboboxes()
        
        # Populate paper format presets
        self.populate_paper_formats()
        
        # Connect to layer changes and CRS selection if iface is available
        if self.iface:
            self.iface.currentLayerChanged.connect(self.on_active_layer_changed)
            self.update_unit_display()

        self.crsBoxSelect.toggled.connect(self.on_crs_box_toggled)

        # Connect paper format and scale sync
        self.paperFormatComboBox.currentIndexChanged.connect(self.on_paper_format_or_scale_changed)
        self.scaleSpinBox.valueChanged.connect(self.on_paper_format_or_scale_changed)
        self.marginSpinBox.valueChanged.connect(self.on_paper_format_or_scale_changed)
        self.widthSpinBox.valueChanged.connect(self.on_dimension_manually_changed)
        self.heightSpinBox.valueChanged.connect(self.on_dimension_manually_changed)
        self.widthUnitComboBox.currentIndexChanged.connect(self.on_paper_format_or_scale_changed)
        self.heightUnitComboBox.currentIndexChanged.connect(self.on_paper_format_or_scale_changed)

    def populate_paper_formats(self) -> None:
        """Populate paper format presets combobox."""
        self.paperFormatComboBox.clear()
        for name in PAPER_FORMATS.keys():
            self.paperFormatComboBox.addItem(name)
        # Default to Custom or A4 Landscape
        self.paperFormatComboBox.setCurrentIndex(0)
    
    def populate_unit_comboboxes(self) -> None:
        """Populate all unit comboboxes with available distance units."""
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
        
        for combo in [self.widthUnitComboBox, self.heightUnitComboBox, self.offsetUnitComboBox]:
            combo.clear()
            for unit in distance_units:
                unit_name = QgsUnitTypes.toString(unit)
                combo.addItem(unit_name, unit)
            
            # Default to meters
            combo.setCurrentIndex(0)

    def on_crs_box_toggled(self, checked: bool) -> None:
        """Handle toggling of source CRS checkbox."""
        if checked:
            layer = self.iface.activeLayer() if self.iface else None
            if layer and layer.crs().isValid():
                self.selected_crs = layer.crs()
            crs_name = self.selected_crs.userFriendlyIdentifier() if self.selected_crs.isValid() else ""
            self.label_crs_info.setText(self.tr("Output CRS: {0}").format(crs_name))
        else:
            from qgis.gui import QgsProjectionSelectionDialog
            dlg = QgsProjectionSelectionDialog(self)
            if self.selected_crs.isValid():
                dlg.setCrs(self.selected_crs)
            if dlg.exec():
                self.selected_crs = dlg.crs()
                self.label_crs_info.setText(
                    self.tr("Output CRS: {0}").format(self.selected_crs.userFriendlyIdentifier())
                )
            else:
                # User cancelled selection dialog, revert checkbox to checked
                self.crsBoxSelect.setChecked(True)

    def on_paper_format_or_scale_changed(self) -> None:
        """Handle changes to paper format preset, scale, margin, or unit comboboxes."""
        preset_name = self.paperFormatComboBox.currentText()
        dims = PAPER_FORMATS.get(preset_name)
        if not dims:
            return
        
        self._updating_dimensions = True
        try:
            scale = self.scaleSpinBox.value()
            margin_mm = self.marginSpinBox.value()
            ground_w_m, ground_h_m = calculate_ground_dimensions(dims[0], dims[1], scale, margin_mm=margin_mm)
            
            w_unit = self.widthUnitComboBox.currentData() or QgsUnitTypes.DistanceMeters
            h_unit = self.heightUnitComboBox.currentData() or QgsUnitTypes.DistanceMeters
            
            factor_w = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, w_unit)
            factor_h = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, h_unit)
            
            self.widthSpinBox.setValue(ground_w_m * factor_w)
            self.heightSpinBox.setValue(ground_h_m * factor_h)
        finally:
            self._updating_dimensions = False

    def on_dimension_manually_changed(self) -> None:
        """Switch preset to Custom when the user manually alters width or height."""
        if not self._updating_dimensions:
            if self.paperFormatComboBox.currentIndex() != 0:
                self.paperFormatComboBox.blockSignals(True)
                self.paperFormatComboBox.setCurrentIndex(0)
                self.paperFormatComboBox.blockSignals(False)

    def polystrip(self, layer: QgsVectorLayer) -> int:
        """Execute the polystrip algorithm with current dialog settings."""
        if not layer or not layer.isValid():
            return -1

        # Synchronize current layer unit and CRS
        if layer.crs().isValid():
            self.current_layer_unit = layer.crs().mapUnits()
            if self.crsBoxSelect.isChecked():
                self.selected_crs = layer.crs()

        srid = layer.crs() if self.crsBoxSelect.isChecked() else self.selected_crs
        
        # Get parameters from UI and convert to layer units
        width = self.get_converted_value(
            self.widthSpinBox.value(),
            self.widthUnitComboBox.currentData()
        )
        height = self.get_converted_value(
            self.heightSpinBox.value(),
            self.heightUnitComboBox.currentData()
        )
        coverage = min(float(self.coverSpinBox.value()), 95.0)
        covstart = self.get_converted_value(
            self.coverSpinBoxStart.value(),
            self.offsetUnitComboBox.currentData()
        )
        follow_line_direction = self.followLineCheckBox.isChecked()
        paper_format = self.paperFormatComboBox.currentText()
        scale = self.scaleSpinBox.value()
        margin_mm = self.marginSpinBox.value()
        
        return get_all_pages(
            layer, width, height, srid, coverage, covstart, follow_line_direction,
            paper_format=paper_format, scale=scale, margin_mm=margin_mm
        )

    def labelwriter(self, unitstr: str) -> None:
        """Update the unit label in the dialog."""
        self.label_unit.setText(unitstr)
    
    def get_converted_value(self, value: float, from_unit: QgsUnitTypes.DistanceUnit) -> float:
        """Convert input value from specified unit to layer unit."""
        if self.current_layer_unit is None or from_unit is None:
            return value
        
        # Convert using QGIS unit conversion
        factor = QgsUnitTypes.fromUnitToUnitFactor(from_unit, self.current_layer_unit)
        return factor * value

    def on_active_layer_changed(self, layer: Optional[QgsMapLayer]) -> None:
        """Handle active layer changes and update unit display."""
        self.update_unit_display()
    
    def update_unit_display(self) -> None:
        """Update the unit display based on the current active layer."""
        if not self.iface:
            return
            
        active_layer = self.iface.activeLayer()
        if active_layer and active_layer.crs().isValid():
            layer_crs = active_layer.crs()
            unit = layer_crs.mapUnits()
            unit_strg = QgsUnitTypes.toString(unit)
            self.selected_crs = layer_crs
            self.label_crs_info.setText(
                self.tr("Output CRS: {0}").format(layer_crs.userFriendlyIdentifier())
            )
        else:
            unit = self.iface.mapCanvas().mapUnits()
            unit_strg = QgsUnitTypes.toString(unit)
        
        self.labelwriter(unit_strg)
        self.current_layer_unit = unit
        
        # Set the unit comboboxes to match layer unit by default
        for combo in [self.widthUnitComboBox, self.heightUnitComboBox, self.offsetUnitComboBox]:
            index = combo.findData(unit)
            if index >= 0:
                combo.setCurrentIndex(index)

    def done(self, r: int) -> None:
        """Disconnect signals when dialog finishes (accept, reject, or close)."""
        if self.iface:
            try:
                self.iface.currentLayerChanged.disconnect(self.on_active_layer_changed)
            except (TypeError, RuntimeError):
                pass
        super().done(r)
