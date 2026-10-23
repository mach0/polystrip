# PolyStrip

[![QGIS 3.x / 4.x](https://img.shields.io/badge/QGIS-3.0%2B%20%7C%204.x-brightgreen.svg)](https://qgis.org)
[![License: GPL v2+](https://img.shields.io/badge/License-GPL%20v2%2B-blue.svg)](LICENSE)
[![Translations](https://img.shields.io/badge/Languages-EN%20%7C%20DE%20%7C%20PL-orange.svg)](polystrip/i18n/)

**PolyStrip** is a QGIS plugin that automatically creates a series of consecutive, overlapping rectangular polygon sheets (strip maps) along linear vector features (such as rivers, roads, pipelines, hiking trails, and railways).

The generated polygon features serve as ready-to-use coverage layers for the **QGIS Print Layout Atlas** tool, enabling map books and strip map atlases to be generated with uniform scale and orientation.

---

## Key Features

- **Interactive GUI & Processing Toolbox**:
  - Run interactively via the **Vector menu** or **toolbar icon**.
  - Run via the **Processing Toolbox** (`PolyStrip > Vector geometry > Polygons Along Lines (PolyStrip)`).
  - Fully compatible with **Graphical Modeler**, **Batch Processing**, and PyQGIS scripts (`processing.run`).
- **Flexible Orientation Modes**:
  - **Line-Following**: Polygons automatically rotate to follow the line's bearing, aligning each map page to the corridor.
  - **North-Up**: Polygons remain oriented strictly North-Up, stepping along the line with overlap.
- **Atlas-Ready Attributes**:
  - `page`: Sequential sheet/page number (`1, 2, 3...`).
  - `angle`: Rotation angle in degrees clockwise from East.
  - `atlas`: Pre-calculated rotation angle (`(360 - angle) % 360`) specifically formatted for QGIS Print Layout Map rotation data-defined override.
  - `source_id`: FID of the originating line feature (in Processing algorithm output).
- **Multipart Geometry Support**: Seamlessly processes both `LineString` and `MultiLineString` features.
- **Unit Support**: Flexible unit selection for width, height, and start offset (meters, kilometers, feet, miles, yards, degrees, etc.) automatically converted to layer units.
- **CRS Handling**: Automatic source layer CRS matching with optional on-the-fly reprojection to any custom CRS.
- **High Performance**: Accelerated with fast bounding-box pre-checks and loop safety guards.
- **Modern Compatibility**: Fully compatible with QGIS 3.x and QGIS 4.x across PyQt5 and PyQt6.
- **Multilingual Support**: Fully localized in English, German (Deutsch), and Polish (Polski).

---

## Installation

### From QGIS Plugin Manager
1. In QGIS, navigate to **Plugins > Manage and Install Plugins...**
2. Search for **PolyStrip**.
3. Click **Install Plugin**.

### Manual Installation
Download `polystrip.zip` from releases and extract the `polystrip` folder into your QGIS plugins directory:
- **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
- **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
- **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

Or deploy directly using make:
```bash
make deploy
```

---

## How It Works

### Option A: Interactive Dialog
1. Select one or more line features in an active line vector layer.
2. Click the **PolyStrip** icon on the toolbar or choose **Vector > PolyStrip > PolyStrip** from the menu.
3. Configure polygon dimensions:
   - **Polygon Width**: Length of each sheet along the line.
   - **Polygon Height**: Corridor extent across the line (centered on the line).
   - **Overlap**: Percentage of overlap between adjacent polygons (e.g. 10%).
   - **Start Offset**: Distance before the line start to begin creating polygons.
   - **Orientation**: Check *Follow line direction* or uncheck for *North-up*.
   - **Coordinate Reference System**: Default source CRS or custom target CRS.
4. Click **OK**. A new memory polygon layer is added to your project, pre-styled with transparent fill and outline only.

### Option B: Processing Toolbox & Python
Open the **Processing Toolbox** panel (`Ctrl+Alt+T`) and expand **PolyStrip > Vector geometry > Polygons Along Lines (PolyStrip)**.

To call PolyStrip in a Python script or console:
```python
import processing

result = processing.run("polystrip:polystrip", {
    'INPUT': '/path/to/lines.gpkg|layername=my_lines',
    'WIDTH': 1000.0,       # Layer units
    'HEIGHT': 500.0,       # Layer units
    'COVERAGE': 10.0,      # Overlap percentage (0-95%)
    'START_OFFSET': 0.0,   # Start offset distance
    'FOLLOW_LINE': True,   # True = follow line, False = North-up
    'OUTPUT': 'memory:strip_polygons'
})

output_layer = result['OUTPUT']
```

---

## Using PolyStrip with QGIS Print Layout Atlas

1. Create or open a **Print Layout** in QGIS (`Project > Layout Manager`).
2. Add a **Map** item to your page.
3. Open the **Atlas** panel on the right and check **Generate an atlas**.
4. Set **Coverage layer** to your PolyStrip output layer (`..._strip`).
5. Select the **Map** item and switch to **Item Properties**:
   - Under **Controlled by Atlas**, check the box and select your margin or predefined scale.
   - Under **Map rotation**, click the data-defined override button (epsilon icon) > **Field type: double** > select **`atlas`** (or enter expression `"atlas"`).
6. Preview the Atlas! Each page automatically pans, zooms, and rotates along your linear corridor.

---

## Development & Build Workflow

The repository includes a standard `Makefile` for compiling translations, running automated tests, and packaging release bundles:

```bash
# Compile translation files (.qm)
make compile

# Update translation source files (.ts) from Python and UI files
make transup

# Run unit tests
make test

# Verify Python syntax across all modules
make check

# Build clean release archive (polystrip.zip)
make package

# Install plugin to your local QGIS profile
make deploy

# Clean temporary files, caches, and build artifacts
make clean
```

---

## Translations

PolyStrip supports multiple languages:
- **English** (default)
- **German** (`polystrip_de.ts` / `polystrip_de.qm`)
- **Polish** (`polystrip_pl.ts` / `polystrip_pl.qm`)

To add a new translation:
1. Add `polystrip_<locale>.ts` to `polystrip/i18n/polystrip.pro`.
2. Run `make transup` to extract all strings into the new `.ts` file.
3. Translate strings in Qt Linguist.
4. Run `make transcompile` to generate `.qm` binary catalogs.

---

## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. See [LICENSE](LICENSE) for details.
