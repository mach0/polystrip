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
"""
from typing import Optional, List
import os.path

from qgis.PyQt.QtCore import (
    QObject,
    QSettings,
    QTranslator,
    QFileInfo,
    QLocale,
    QCoreApplication
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget
from qgis.core import Qgis, QgsMapLayer, QgsWkbTypes
from qgis.gui import QgisInterface

# Import the code for the dialog
from .polystripdialog import PolyStripDialog


class PolyStrip(QObject):
    """QGIS Plugin Implementation."""

    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        super().__init__()
        # Save reference to the QGIS interface
        self.iface = iface
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Safe locale detection
        user_locale = QSettings().value('locale/userLocale', '')
        if not user_locale:
            user_locale = QLocale().name()
        locale = str(user_locale)[0:2]

        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'polystrip_{locale}.qm'
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&PolyStrip')
        self.toolbar = self.iface.addToolBar(u'PolyStrip')
        self.toolbar.setObjectName(u'PolyStrip')
        self.dlg = None
        self.provider = None

    def show_warning(self, message: str) -> None:
        """Display a warning banner in the QGIS message bar."""
        warning_level = getattr(getattr(Qgis, 'MessageLevel', Qgis), 'Warning', Qgis.Warning)
        self.iface.messageBar().pushMessage(self.tr('PolyStrip'), message, warning_level, 5)

    def show_info(self, message: str) -> None:
        """Display an info banner in the QGIS message bar."""
        info_level = getattr(getattr(Qgis, 'MessageLevel', Qgis), 'Info', Qgis.Info)
        self.iface.messageBar().pushMessage(self.tr('PolyStrip'), message, info_level, 5)

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('PolyStrip', message)

    def add_action(
            self,
            icon_path: str,
            text: str,
            callback,
            enabled_flag: bool = True,
            add_to_menu: bool = True,
            add_to_toolbar: bool = True,
            status_tip: Optional[str] = None,
            whats_this: Optional[str] = None,
            parent: Optional[QWidget] = None) -> QAction:
        """Add a toolbar icon to the toolbar."""
        icon = QIcon(icon_path)
        action_parent = parent or self.iface.mainWindow()
        action = QAction(icon, text, action_parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar and self.toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initProcessing(self) -> None:
        """Register the processing provider if Processing is available."""
        try:
            from qgis.core import QgsApplication
            from .polystrip_provider import PolyStripProvider
            self.provider = PolyStripProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)
        except Exception:
            self.provider = None

    def unloadProcessing(self) -> None:
        """Remove the processing provider from the registry."""
        if hasattr(self, 'provider') and self.provider is not None:
            try:
                from qgis.core import QgsApplication
                QgsApplication.processingRegistry().removeProvider(self.provider)
            except Exception:
                pass
            self.provider = None

    def initGui(self) -> None:
        """Create the menu entries, toolbar icons, and processing algorithms."""
        icon_path = os.path.join(QFileInfo(__file__).absolutePath(), 'img', 'polystrip.svg')
        self.add_action(
            icon_path,
            text=self.tr(u'PolyStrip'),
            callback=self.run)
        self.initProcessing()

    def unload(self) -> None:
        """Removes the plugin menu item, icon, and processing provider from QGIS."""
        self.unloadProcessing()
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if hasattr(self, 'toolbar') and self.toolbar is not None:
            self.toolbar.clear()
            del self.toolbar

    def run(self) -> None:
        """Run method that performs input validation and launches the dialog."""
        # Check if there are any line layers in the project
        has_line_layers = any(
            layer.type() == QgsMapLayer.VectorLayer and 
            layer.geometryType() == QgsWkbTypes.LineGeometry
            for layer in self.iface.mapCanvas().layers()
        )
        
        if not has_line_layers:
            self.show_warning(self.tr(u'No layers with line features - polystrip needs a selected line feature!'))
            return
        
        # Validate active layer
        active_layer = self.iface.activeLayer()
        
        if not active_layer or active_layer.type() != QgsMapLayer.VectorLayer:
            self.show_warning(self.tr(u'Select a Feature in a Vectorlayer'))
            return
            
        if active_layer.geometryType() != QgsWkbTypes.LineGeometry:
            self.show_warning(self.tr(u'Select a Feature in a Linelayer'))
            return
            
        if active_layer.selectedFeatureCount() == 0:
            self.show_warning(self.tr(u'No feature in active Layer selected!'))
            return

        # Create and display modal dialog
        self.dlg = PolyStripDialog(parent=self.iface.mainWindow(), iface=self.iface)
        result = self.dlg.exec()

        if result:
            layer = self.iface.activeLayer()
            if layer and layer.selectedFeatureCount() > 0:
                count = self.dlg.polystrip(layer)
                if count > 0:
                    self.show_info(self.tr(u'Successfully created {0} strip polygon(s).').format(count))
                elif count == 0:
                    self.show_warning(self.tr(u'No polygons could be generated.'))
            else:
                self.show_warning(self.tr(u'No feature in active Layer selected!'))

