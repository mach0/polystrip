# PolyStrip

[![QGIS 3.x / 4.x](https://img.shields.io/badge/QGIS-3.0%2B%20%7C%204.x-brightgreen.svg)](https://qgis.org)
[![License: GPL v2+](https://img.shields.io/badge/License-GPL%20v2%2B-blue.svg)](LICENSE)
[![Translations](https://img.shields.io/badge/Languages-EN%20%7C%20DE%20%7C%20PL-orange.svg)](polystrip/i18n/)

**PolyStrip** is a QGIS plugin that automatically creates a series of consecutive, overlapping rectangular polygon sheets (strip maps) along linear vector features (such as rivers, roads, pipelines, hiking trails, and railways).

The generated polygon features serve as ready-to-use coverage layers for the **QGIS Print Layout Atlas** tool, enabling map books and strip map atlases to be generated with uniform scale and orientation.

---

## Key Features

- **Paper Format Presets, Scale & Margin Synchronization**:
  - Select standard ISO paper sizes (**A0, A1, A2, A3, A4, A5** in both **Landscape** and **Portrait** orientations) and specify map scale (e.g. `1 : 8000`).
  - Optional **Page Margin (mm)** setting to subtract margins for borders, title blocks, and printer margins.
  - Automatically calculates real-world ground corridor dimensions ($\text{Dimension}_{\text{ground}} = \frac{\text{Dimension}_{\text{paper mm}} - 2 \cdot \text{Margin}_{\text{mm}}}{1000} \times \text{Scale}$).
  - Live two-way synchronization: selecting paper format + scale + margin updates width/height in layer units; custom overrides switch back to `Custom`.
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
  - `paper`: Name of paper format preset (e.g. `"A4 Landscape"` or `"Custom"`).
  - `scale`: Map scale denominator (e.g. `8000`).
  - `margin_mm`: Page margin in mm subtracted from paper dimensions (`0.0, 5.0, 10.0...`).
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
    'PRESET_FORMAT': 9,    # 9 = 'ISO A4 (Landscape - 297 x 210 mm)', or 0 for 'Custom'
    'SCALE': 8000,         # Scale 1:8000
    'MARGIN': 10.0,        # 10 mm border margin inside paper edges
    'COVERAGE': 10.0,      # Overlap percentage (0-95%)
    'START_OFFSET': 0.0,   # Start offset distance
    'FOLLOW_LINE': True,   # True = follow line, False = North-up
    'OUTPUT': 'memory:strip_polygons'
})

output_layer = result['OUTPUT']
```

---

## Understanding Margins: QGIS Atlas vs. PolyStrip

When working with strip maps in QGIS Print Layouts, users often encounter unexpected margins or scaling behavior. Here is how QGIS and PolyStrip work together:

### 1. Where Does the Margin in QGIS Atlas Come From?

In QGIS Print Layout, when you add a Map item and enable **Controlled by Atlas**, QGIS defaults to:
> **Margin around feature: `10%`**

**Why this creates unexpected whitespace and alters your scale:**
- QGIS calculates an axis-aligned bounding box around each polygon feature and expands it outward by 10% on all four sides.
- Because line-following strip polygons are rotated at arbitrary angles, the axis-aligned bounding box is significantly larger than the polygon itself.
- QGIS then dynamically fits this enlarged bounding box to your map frame, **distorting the intended 1:8000 scale** and showing unwanted empty margins around the polygon.

### 2. How to Configure QGIS Atlas for Exact 1:X Strip Maps

To eliminate unwanted margins and achieve exact 1:X scale strip maps:

1. In your **Print Layout**, select the **Map item**.
2. In the **Item Properties** tab on the right, find **Controlled by Atlas**:
   - Check **Controlled by Atlas**.
   - Change the dropdown mode from *Margin around feature* to **Fixed scale**.
   - Enter your target scale (e.g. `8000`), or click the data-defined override button next to the scale box and select the attribute field **`"scale"`**.
3. Under **Map rotation**, click the data-defined override button (epsilon icon) > **Field type: double** > choose **`"atlas"`**.
4. Set the Map item's frame size to match your printable map viewport.

Now each Atlas page centers on the polygon, rotates along the corridor bearing, and renders at the exact cartographic scale without any automatic padding.

### 3. What Does PolyStrip's "Page Margin (mm)" Setting Do?

Most physical prints or atlas layouts require margins for:
- Printer hardware margins (unprintable edge zones, typically 5–10 mm).
- Layout design margins (title banners, page numbers, coordinates, neatline borders).

If an A4 landscape sheet ($297 \times 210$ mm) has a 10 mm margin around the map frame, the actual viewport on paper is:
$$\text{Width}_{\text{printable}} = 297\text{ mm} - (2 \times 10\text{ mm}) = 277\text{ mm}$$
$$\text{Height}_{\text{printable}} = 210\text{ mm} - (2 \times 10\text{ mm}) = 190\text{ mm}$$

When you specify **Page Margin (mm)** in PolyStrip:
- PolyStrip subtracts $2 \times \text{margin}$ from both paper dimensions.
- At scale 1:8000, the generated corridor rectangle will be exactly:
  $$277\text{ mm} \times \frac{8000}{1000} = 2216.0\text{ m wide}$$
  $$190\text{ mm} \times \frac{8000}{1000} = 1520.0\text{ m high}$$
- Matching your layout map frame dimensions to the effective printable area guarantees a seamless 1:1 fit between the GIS polygon and your paper map frame.

---

## Step-by-Step: Using PolyStrip with QGIS Print Layout Atlas

1. **Generate Strip Polygons**:
   - In QGIS, select your line feature (e.g. river or road).
   - Open **PolyStrip**, choose your paper preset (e.g. `ISO A4 Landscape`), scale (e.g. `8000`), and page margin (e.g. `10 mm`).
   - Click **OK** to generate the polygon coverage layer.
2. **Create Print Layout**:
   - Go to **Project > New Print Layout**.
   - Set page size to match your preset (e.g. `A4`, Landscape).
3. **Add Map Item**:
   - Draw a Map item inside your page margins (e.g. left: 10 mm, top: 10 mm, width: 277 mm, height: 190 mm).
4. **Enable Atlas**:
   - In the **Atlas** panel on the right, check **Generate an atlas**.
   - Set **Coverage layer** to your PolyStrip output layer (`..._strip`).
5. **Lock Scale and Rotation on Map Item**:
   - Select the Map item, go to **Item Properties**.
   - Check **Controlled by Atlas**, select **Fixed scale**, set scale to `8000` (or link to field `"scale"`).
   - Under **Map rotation**, click data-defined override > select field **`"atlas"`**.
6. **Export Atlas**:
   - Choose **Atlas > Export Atlas as PDF...** or **Export Atlas as Images...**. Every page will be exported at uniform scale with proper rotation.

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
