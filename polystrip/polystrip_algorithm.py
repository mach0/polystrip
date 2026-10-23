# -*- coding: utf-8 -*-
"""
PolyStrip Processing Algorithm

Allows PolyStrip to run from the QGIS Processing Toolbox, Graphical Modeler,
and Python scripts (processing.run).
"""

import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    Qgis,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterDistance,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingOutputNumber,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsGeometry,
    QgsWkbTypes,
    QgsUnitTypes,
    QgsProcessingParameterEnum
)

from . import polystrip_line_following
from . import polystrip_north_up
from .polystripalg import (
    extract_linestrings,
    type_int,
    type_double,
    type_string,
    PAPER_FORMATS,
    calculate_ground_dimensions
)


class PolyStripAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    PRESET_FORMAT = 'PRESET_FORMAT'
    SCALE = 'SCALE'
    MARGIN = 'MARGIN'
    WIDTH = 'WIDTH'
    HEIGHT = 'HEIGHT'
    COVERAGE = 'COVERAGE'
    START_OFFSET = 'START_OFFSET'
    FOLLOW_LINE = 'FOLLOW_LINE'
    OUTPUT = 'OUTPUT'
    OUTPUT_COUNT = 'OUTPUT_COUNT'

    PRESET_OPTIONS = list(PAPER_FORMATS.keys())

    def tr(self, string: str) -> str:
        return QCoreApplication.translate('PolyStripAlgorithm', string)

    def createInstance(self):
        return PolyStripAlgorithm()

    def name(self) -> str:
        return 'polystrip'

    def displayName(self) -> str:
        return self.tr('Polygons Along Lines (PolyStrip)')

    def group(self) -> str:
        return self.tr('Vector geometry')

    def groupId(self) -> str:
        return 'vectorgeometry'

    def icon(self) -> QIcon:
        icon_path = os.path.join(os.path.dirname(__file__), 'img', 'polystrip.svg')
        return QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

    def shortHelpString(self) -> str:
        return self.tr(
            "Creates consecutive, overlapping rectangular polygon strip sheets along "
            "linear vector features. Ideal for preparing coverage layers for QGIS "
            "Print Layout Atlas map books.\n\n"
            "Features include line-following rotation, north-up orientation, "
            "start offset, and pre-calculated atlas rotation angles."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input line layer'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PRESET_FORMAT,
                self.tr('Print format preset'),
                options=self.PRESET_OPTIONS,
                defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SCALE,
                self.tr('Map scale denominator (e.g. 8000 for 1:8000)'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=8000,
                minValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MARGIN,
                self.tr('Page margin in mm (subtracted from paper preset edges)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=100.0
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.WIDTH,
                self.tr('Custom polygon width (used when preset is Custom)'),
                defaultValue=100.0,
                parentParameterName=self.INPUT,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.HEIGHT,
                self.tr('Custom polygon height (used when preset is Custom)'),
                defaultValue=100.0,
                parentParameterName=self.INPUT,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.COVERAGE,
                self.tr('Overlap coverage (%)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0,
                maxValue=95.0
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.START_OFFSET,
                self.tr('Start/end line offset distance'),
                defaultValue=0.0,
                parentParameterName=self.INPUT,
                minValue=0.0
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FOLLOW_LINE,
                self.tr('Follow line direction (uncheck for North-Up)'),
                defaultValue=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Strip polygons'),
                type=QgsProcessing.TypeVectorPolygon
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_COUNT,
                self.tr('Number of created polygons')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        preset_idx = self.parameterAsEnum(parameters, self.PRESET_FORMAT, context)
        preset_name = self.PRESET_OPTIONS[preset_idx]
        scale = self.parameterAsInt(parameters, self.SCALE, context)
        margin = self.parameterAsDouble(parameters, self.MARGIN, context)

        if preset_name != 'Custom' and PAPER_FORMATS.get(preset_name):
            dims = PAPER_FORMATS[preset_name]
            ground_w_m, ground_h_m = calculate_ground_dimensions(dims[0], dims[1], scale, margin_mm=margin)
            layer_unit = source.sourceCrs().mapUnits() if (source.sourceCrs() and source.sourceCrs().isValid()) else QgsUnitTypes.DistanceMeters
            factor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, layer_unit)
            width = ground_w_m * factor
            height = ground_h_m * factor
        else:
            width = self.parameterAsDouble(parameters, self.WIDTH, context)
            height = self.parameterAsDouble(parameters, self.HEIGHT, context)

        coverage = min(max(0.0, self.parameterAsDouble(parameters, self.COVERAGE, context)), 95.0)
        covstart = max(0.0, self.parameterAsDouble(parameters, self.START_OFFSET, context))
        follow_line = self.parameterAsBoolean(parameters, self.FOLLOW_LINE, context)

        fields = QgsFields()
        fields.append(QgsField("page", type_int, len=10))
        fields.append(QgsField("angle", type_double, len=10, prec=2))
        fields.append(QgsField("atlas", type_double, len=10, prec=2))
        fields.append(QgsField("paper", type_string, len=50))
        fields.append(QgsField("scale", type_int, len=10))
        fields.append(QgsField("margin_mm", type_double, len=10, prec=1))
        fields.append(QgsField("source_id", type_int, len=10))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Polygon,
            source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total_features = source.featureCount()
        page_number = 1
        total_polygons = 0

        features = source.getFeatures()
        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            geom = feature.geometry()
            if not geom or geom.type() != QgsWkbTypes.LineGeometry or geom.isEmpty():
                continue

            line_parts = extract_linestrings(geom)
            for part in line_parts:
                part_len = part.length()
                if part_len <= 0:
                    continue

                if covstart > 0:
                    extended_part = part.extendLine(covstart, covstart)
                    if not extended_part or extended_part.isEmpty():
                        extended_part = QgsGeometry(part)
                else:
                    extended_part = QgsGeometry(part)

                ext_len = extended_part.length()
                if ext_len <= 0:
                    extended_part = QgsGeometry(part)
                    ext_len = part_len

                part_features = []
                if follow_line:
                    count = polystrip_line_following.create_line_following_polygons(
                        extended_part, part, part_len, ext_len,
                        width, height, coverage, covstart, part_features, page_number
                    )
                else:
                    count = polystrip_north_up.create_north_up_polygons(
                        extended_part, part, part_len, ext_len,
                        width, height, coverage, covstart, part_features, page_number
                    )

                for f in part_features:
                    attrs = list(f.attributes())
                    attrs.extend([preset_name, scale, margin, feature.id()])
                    f.setAttributes(attrs)
                    sink.addFeature(f, QgsFeatureSink.FastInsert)
                    page_number += 1
                    total_polygons += 1

            if total_features > 0:
                feedback.setProgress(int((current + 1) / total_features * 100))

        feedback.pushInfo(self.tr("Successfully created {0} strip polygons.").format(total_polygons))
        return {
            self.OUTPUT: dest_id,
            self.OUTPUT_COUNT: total_polygons
        }
