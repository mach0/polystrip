# -*- coding: utf-8 -*-
"""
Unit tests for the PolyStrip plugin.
"""

import os
import sys
import unittest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from test.qgis_mock import install_mock_qgis
except ImportError:
    from qgis_mock import install_mock_qgis
install_mock_qgis()

from polystrip import polystrip_line_following, polystrip_north_up
from polystrip.polystripalg import extract_linestrings
from qgis.core import QgsGeometry, QgsPointXY, QgsRectangle


class TestPolyStripAlgorithms(unittest.TestCase):

    def test_azimuth_and_rotation_math(self):
        """Test the rotation angle and atlas angle formulas."""
        p1 = QgsPointXY(0.0, 0.0)
        p_east = QgsPointXY(100.0, 0.0)
        p_north = QgsPointXY(0.0, 100.0)
        p_south = QgsPointXY(0.0, -100.0)

        # Azimuth from p1 to East is 90 deg
        az_east = p1.azimuth(p_east)
        self.assertAlmostEqual(az_east, 90.0, places=2)
        angle_east = (az_east + 270.0) % 360.0
        self.assertAlmostEqual(angle_east, 0.0, places=2)
        atlas_east = (360.0 - angle_east) % 360.0
        self.assertAlmostEqual(atlas_east, 0.0, places=2)

        # Azimuth to South is 180 deg
        az_south = p1.azimuth(p_south)
        self.assertAlmostEqual(az_south, 180.0, places=2)
        angle_south = (az_south + 270.0) % 360.0
        self.assertAlmostEqual(angle_south, 90.0, places=2)
        atlas_south = (360.0 - angle_south) % 360.0
        self.assertAlmostEqual(atlas_south, 270.0, places=2)

    def test_line_following_polygons_generation(self):
        """Test creating line-following polygons along a mock line."""
        geom = QgsGeometry()
        page_features = []
        count = polystrip_line_following.create_line_following_polygons(
            extended_geom=geom,
            geom=geom,
            geomlength=1000.0,
            extended_geomlength=1000.0,
            width=200.0,
            height=100.0,
            coverage=10.0,
            covstart=0.0,
            page_features=page_features,
            r=1
        )
        self.assertGreater(count, 0)
        self.assertEqual(len(page_features), count)

        # Check attributes of created pages: [page, angle, atlas]
        for idx, feat in enumerate(page_features, start=1):
            attrs = feat.attributes()
            self.assertEqual(attrs[0], idx)  # page number
            self.assertIsInstance(attrs[1], (int, float))  # angle
            self.assertIsInstance(attrs[2], (int, float))  # atlas

    def test_north_up_polygons_generation(self):
        """Test creating north-up polygons along a mock line."""
        geom = QgsGeometry()
        page_features = []
        count = polystrip_north_up.create_north_up_polygons(
            extended_geom=geom,
            geom=geom,
            geomlength=1000.0,
            extended_geomlength=1000.0,
            width=200.0,
            height=100.0,
            coverage=10.0,
            covstart=0.0,
            page_features=page_features,
            r=1
        )
        self.assertGreater(count, 0)
        self.assertEqual(len(page_features), count)

        # In north-up mode, angle and atlas should be 0.0
        for feat in page_features:
            attrs = feat.attributes()
            self.assertEqual(attrs[1], 0.0)
            self.assertEqual(attrs[2], 0.0)

    def test_metadata_structure(self):
        """Validate metadata.txt conformity with QGIS standards."""
        metadata_path = os.path.join(REPO_ROOT, 'polystrip', 'metadata.txt')
        self.assertTrue(os.path.isfile(metadata_path))

        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()

        mandatory_keys = [
            'name=', 'qgisMinimumVersion=', 'description=', 'about=',
            'version=', 'author=', 'email=', 'tracker=', 'repository='
        ]
        for key in mandatory_keys:
            self.assertIn(key, content, f"Missing required metadata key: {key}")

        self.assertIn('supportsQt6=yes', content)

    def test_extract_linestrings(self):
        """Test line extraction from single and multipart geometries."""
        # Empty geometry
        empty_geom = QgsGeometry()
        empty_geom.isEmpty = lambda: True
        self.assertEqual(extract_linestrings(empty_geom), [])

        # Single LineString
        single_geom = QgsGeometry()
        single_geom.isEmpty = lambda: False
        single_geom.isMultipart = lambda: False
        single_geom._length = 150.0
        parts = extract_linestrings(single_geom)
        self.assertEqual(len(parts), 1)

        # MultiLineString
        multi_geom = QgsGeometry()
        multi_geom.isEmpty = lambda: False
        multi_geom.isMultipart = lambda: True
        part1 = QgsGeometry()
        part1._length = 50.0
        part2 = QgsGeometry()
        part2._length = 60.0
        multi_geom.asGeometryCollection = lambda: [part1, part2]
        multi_parts = extract_linestrings(multi_geom)
        self.assertEqual(len(multi_parts), 2)

    def test_processing_algorithm_and_provider(self):
        """Test processing algorithm metadata and provider initialization."""
        from polystrip.polystrip_algorithm import PolyStripAlgorithm
        from polystrip.polystrip_provider import PolyStripProvider

        alg = PolyStripAlgorithm()
        self.assertEqual(alg.name(), 'polystrip')
        self.assertEqual(alg.groupId(), 'vectorgeometry')
        self.assertIn('PolyStrip', alg.displayName())
        self.assertIn('Atlas', alg.shortHelpString())

        prov = PolyStripProvider()
        self.assertEqual(prov.id(), 'polystrip')
        self.assertEqual(prov.name(), 'PolyStrip')
        self.assertIn('PolyStrip', prov.longName())

    def test_translation_files_exist_and_compiled(self):
        """Ensure all translation files exist and are compiled."""
        i18n_dir = os.path.join(REPO_ROOT, 'polystrip', 'i18n')
        for lang in ['de', 'pl']:
            ts = os.path.join(i18n_dir, f'polystrip_{lang}.ts')
            qm = os.path.join(i18n_dir, f'polystrip_{lang}.qm')
            self.assertTrue(os.path.isfile(ts), f"Missing {ts}")
            self.assertTrue(os.path.isfile(qm), f"Missing {qm}")
            self.assertGreater(os.path.getsize(qm), 0, f"Empty QM file: {qm}")


if __name__ == '__main__':
    unittest.main()
