#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update translation files (.ts) from Python sources and Qt UI files,
and maintain complete German (de) and Polish (pl) translations.
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PLUGIN_DIR = os.path.join(REPO_ROOT, 'polystrip')
I18N_DIR = os.path.join(PLUGIN_DIR, 'i18n')

TRANSLATION_DICTIONARY = {
    'de': {
        # PolyStripAlgorithm
        'Polygons Along Lines (PolyStrip)': 'Polygone entlang von Linien (PolyStrip)',
        'Vector geometry': 'Vektorgeometrie',
        'Creates consecutive, overlapping rectangular polygon strip sheets along linear vector features. Ideal for preparing coverage layers for QGIS Print Layout Atlas map books.\n\nFeatures include line-following rotation, north-up orientation, start offset, and pre-calculated atlas rotation angles.':
            'Erstellt fortlaufende, überlappende rechteckige Polygon-Streifen entlang linearer Vektorobjekte. Ideal zur Vorbereitung von Deckungslayern für QGIS Drucklayout-Atlas-Kartenbände.\n\nEnthält linienfolgende Rotation, Nord-Ausrichtung, Start-Offset und vorausberechnete Atlas-Rotationswinkel.',
        'Input line layer': 'Eingabe-Linienlayer',
        'Polygon width': 'Polygon-Breite',
        'Polygon height': 'Polygon-Höhe',
        'Overlap coverage (%)': 'Überlappung (%)',
        'Start/end line offset distance': 'Start/Ende-Linienversatz',
        'Follow line direction (uncheck for North-Up)': 'Linienrichtung folgen (deaktivieren für Nord-Ausrichtung)',
        'Strip polygons': 'Polygon-Streifen',
        'Number of created polygons': 'Anzahl erstellter Polygone',
        'Successfully created {0} strip polygons.': 'Erfolgreich {0} Polygon-Streifen erstellt.',
        # PolyStripProvider
        'PolyStrip': 'PolyStrip',
        'PolyStrip - Polygons Along Lines': 'PolyStrip - Polygone entlang von Linien',
        # PolyStrip
        '&PolyStrip': '&PolyStrip',
        'No layers with line features - polystrip needs a selected line feature!':
            'Keine Layer mit Linienobjekten vorhanden - PolyStrip benötigt ein ausgewähltes Linienobjekt!',
        'Select a Feature in a Vectorlayer': 'Wählen Sie ein Objekt in einem Vektorlayer aus',
        'Select a Feature in a Linelayer': 'Wählen Sie ein Objekt in einem Linienlayer aus',
        'No feature in active Layer selected!': 'Kein Feature im aktiven Layer ausgewählt!',
        'Successfully created {0} strip polygon(s).': 'Erfolgreich {0} Polygon-Streifen erstellt.',
        'No polygons could be generated.': 'Es konnten keine Polygone erzeugt werden.',
        # PolyStripDialog
        'Output CRS: {0}': 'Ausgabe-KRS: {0}',
        'PolyStrip - Create Polygons along Lines': 'PolyStrip - Polygone entlang von Linien erstellen',
        'Layer Information': 'Layer-Informationen',
        'Layer Unit:': 'Layer-Einheit:',
        'Polygon Parameters': 'Polygon-Parameter',
        'Polygon Width:': 'Polygon-Breite:',
        'Width of each polygon strip along the line': 'Breite jedes Polygon-Streifens entlang der Linie',
        'Unit for width value': 'Einheit für Breitenwert',
        'Polygon Height:': 'Polygon-Höhe:',
        'Height (perpendicular distance) of each polygon from the line':
            'Höhe (senkrechter Abstand) jedes Polygons von der Linie',
        'Unit for height value': 'Einheit für Höhenwert',
        'Coverage Settings': 'Überlappungs-Einstellungen',
        'Overlap:': 'Überlappung:',
        'Percentage of overlap between adjacent polygons': 'Prozentsatz der Überlappung zwischen benachbarten Polygonen',
        ' %': ' %',
        'Start Offset:': 'Start-Versatz:',
        'Distance from line start to begin creating polygons':
            'Abstand vom Linienanfang, ab dem Polygone erstellt werden',
        'Unit for start offset value': 'Einheit für Start-Versatzwert',
        'Polygon Orientation': 'Polygon-Ausrichtung',
        'Follow line direction': 'Linienrichtung folgen',
        'If checked, polygons will be rotated to follow the line direction. If unchecked, polygons will maintain north-up orientation.':
            'Wenn aktiviert, werden Polygone entlang der Linienrichtung gedreht. Wenn deaktiviert, behalten sie die Nord-Ausrichtung.',
        'Coordinate Reference System': 'Koordinatenreferenzsystem',
        'Use CRS from source layer (recommended)': 'KRS aus Quell-Layer verwenden (empfohlen)',
        'Use the same coordinate reference system as the input line layer':
            'Dasselbe Koordinatenbezugssystem wie die Eingangs-Linienebene verwenden',
        'Uncheck to select a different CRS for the output polygons':
            'Deaktivieren, um ein anderes KRS für die Ausgabe-Polygone auszuwählen',
        # Print format & scale
        'Print Format Preset:': 'Druckformat-Vorlage:',
        'Select an ISO paper format preset (calculates dimensions from scale) or Custom':
            'Wählen Sie eine ISO-Papierformat-Vorlage (berechnet Dimensionen aus Maßstab) oder Benutzerdefiniert',
        'Map Scale (1 : X):': 'Kartenmaßstab (1 : X):',
        'Scale denominator for the paper format (e.g. 8000 for 1:8000)':
            'Maßstabszahl für das Papierformat (z. B. 8000 für 1:8000)',
        '1 : ': '1 : ',
        'Page Margin:': 'Seitenrand:',
        'Margin in mm inside paper edges for borders, headers, and printer margins (subtracted from each side)':
            'Rand in mm innerhalb der Papierkanten für Rahmen, Schriftfelder und Druckränder (wird von jeder Seite abgezogen)',
        ' mm': ' mm',
        "Tip: In QGIS Print Layout Atlas, set Map item > Controlled by Atlas to 'Fixed scale'.":
            "Tipp: Im QGIS Drucklayout-Atlas das Kartenelement > Vom Atlas gesteuert auf 'Fester Maßstab' setzen.",
        'Page margin in mm (subtracted from paper preset edges)':
            'Seitenrand in mm (von Papierkanten abgezogen)',
        'Print format preset': 'Druckformat-Vorlage',
        'Map scale denominator (e.g. 8000 for 1:8000)': 'Kartenmaßstabszahl (z. B. 8000 für 1:8000)',
        'Custom polygon width (used when preset is Custom)':
            'Benutzerdefinierte Polygon-Breite (verwendet wenn Vorlage Benutzerdefiniert ist)',
        'Custom polygon height (used when preset is Custom)':
            'Benutzerdefinierte Polygon-Höhe (verwendet wenn Vorlage Benutzerdefiniert ist)'
    },
    'pl': {
        # PolyStripAlgorithm
        'Polygons Along Lines (PolyStrip)': 'Poligony wzdłuż linii (PolyStrip)',
        'Vector geometry': 'Geometria wektorowa',
        'Creates consecutive, overlapping rectangular polygon strip sheets along linear vector features. Ideal for preparing coverage layers for QGIS Print Layout Atlas map books.\n\nFeatures include line-following rotation, north-up orientation, start offset, and pre-calculated atlas rotation angles.':
            'Tworzy kolejne, nakładające się prostokątne pasy poligonowe wzdłuż liniowych obiektów wektorowych. Idealne do przygotowania warstw pokrycia dla atlasu wydruku QGIS.\n\nFunkcje obejmują obrót wzdłuż linii, orientację północną, przesunięcie początkowe oraz wstępnie obliczone kąty obrotu dla atlasu.',
        'Input line layer': 'Wejściowa warstwa liniowa',
        'Polygon width': 'Szerokość poligonu',
        'Polygon height': 'Wysokość poligonu',
        'Overlap coverage (%)': 'Pokrycie nakładania (%)',
        'Start/end line offset distance': 'Odległość przesunięcia początku/końca linii',
        'Follow line direction (uncheck for North-Up)': 'Podążaj za kierunkiem linii (odznacz dla orientacji północnej)',
        'Strip polygons': 'Pasy poligonowe',
        'Number of created polygons': 'Liczba utworzonych poligonów',
        'Successfully created {0} strip polygons.': 'Pomyślnie utworzono {0} poligonów.',
        # PolyStripProvider
        'PolyStrip': 'PolyStrip',
        'PolyStrip - Polygons Along Lines': 'PolyStrip - Poligony wzdłuż linii',
        # PolyStrip
        '&PolyStrip': '&PolyStrip',
        'No layers with line features - polystrip needs a selected line feature!':
            'Brak warstwy liniowej - PolyStrip wymaga zaznaczenia obiektów liniowych!',
        'Select a Feature in a Vectorlayer': 'Zaznacz obiekt na warstwie liniowej',
        'Select a Feature in a Linelayer': 'Zaznacz obiekt na warstwie liniowej',
        'No feature in active Layer selected!': 'Brak zaznaczonych obiektów na aktywnej warstwie!',
        'Successfully created {0} strip polygon(s).': 'Pomyślnie utworzono {0} poligonów.',
        'No polygons could be generated.': 'Nie udało się utworzyć poligonów.',
        # PolyStripDialog
        'Output CRS: {0}': 'Układ wyjściowy: {0}',
        'PolyStrip - Create Polygons along Lines': 'PolyStrip - Tworzenie poligonów wzdłuż linii',
        'Layer Information': 'Informacje o warstwie',
        'Layer Unit:': 'Jednostka warstwy:',
        'Polygon Parameters': 'Parametry poligonów',
        'Polygon Width:': 'Szerokość poligonu:',
        'Width of each polygon strip along the line': 'Szerokość każdego poligonu wzdłuż linii',
        'Unit for width value': 'Jednostka szerokości',
        'Polygon Height:': 'Wysokość poligonu:',
        'Height (perpendicular distance) of each polygon from the line':
            'Wysokość (odległość prostopadła) każdego poligonu od linii',
        'Unit for height value': 'Jednostka wysokości',
        'Coverage Settings': 'Ustawienia pokrycia',
        'Overlap:': 'Nakładanie:',
        'Percentage of overlap between adjacent polygons': 'Procent nakładania się sąsiednich poligonów',
        ' %': ' %',
        'Start Offset:': 'Przesunięcie początkowe:',
        'Distance from line start to begin creating polygons':
            'Odległość od początku linii, od której rozpocznie się tworzenie poligonów',
        'Unit for start offset value': 'Jednostka przesunięcia początkowego',
        'Polygon Orientation': 'Orientacja poligonów',
        'Follow line direction': 'Podążaj za kierunkiem linii',
        'If checked, polygons will be rotated to follow the line direction. If unchecked, polygons will maintain north-up orientation.':
            'Jeśli zaznaczone, poligony zostaną obrócone zgodnie z kierunkiem linii. Jeśli odznaczone, zachowają orientację północną.',
        'Coordinate Reference System': 'Układ współrzędnych',
        'Use CRS from source layer (recommended)': 'Użyj układu z warstwy źródłowej (zalecane)',
        'Use the same coordinate reference system as the input line layer':
            'Użyj tego samego układu współrzędnych co warstwa wejściowa',
        'Uncheck to select a different CRS for the output polygons':
            'Odznacz, aby wybrać inny układ współrzędnych dla poligonów wynikowych',
        # Print format & scale
        'Print Format Preset:': 'Szablon formatu wydruku:',
        'Select an ISO paper format preset (calculates dimensions from scale) or Custom':
            'Wybierz szablon formatu papieru ISO (oblicza wymiary ze skali) lub Własny',
        'Map Scale (1 : X):': 'Skala mapy (1 : X):',
        'Scale denominator for the paper format (e.g. 8000 for 1:8000)':
            'Mianownik skali dla formatu papieru (np. 8000 dla 1:8000)',
        '1 : ': '1 : ',
        'Page Margin:': 'Margines strony:',
        'Margin in mm inside paper edges for borders, headers, and printer margins (subtracted from each side)':
            'Margines w mm od krawędzi papieru na ramki, nagłówki i marginesy drukarki (odejmowany z każdej strony)',
        ' mm': ' mm',
        "Tip: In QGIS Print Layout Atlas, set Map item > Controlled by Atlas to 'Fixed scale'.":
            "Wskazówka: W atlasie wydruku QGIS ustaw element mapy > Kontrolowane przez atlas na 'Stała skala'.",
        'Page margin in mm (subtracted from paper preset edges)':
            'Margines strony w mm (odejmowany od krawędzi papieru)',
        'Print format preset': 'Szablon formatu wydruku',
        'Map scale denominator (e.g. 8000 for 1:8000)': 'Mianownik skali mapy (np. 8000 dla 1:8000)',
        'Custom polygon width (used when preset is Custom)':
            'Własna szerokość poligonu (używana, gdy szablon to Własny)',
        'Custom polygon height (used when preset is Custom)':
            'Własna wysokość poligonu (używana, gdy szablon to Własny)'
    }
}


def find_pylupdate():
    for name in ['pylupdate6', 'pylupdate5']:
        path = shutil.which(name)
        if path:
            return path
    return None


def run_pylupdate(pylupdate_bin, ts_file, source_files):
    cmd = [pylupdate_bin, '--ts', ts_file] + source_files
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {pylupdate_bin}: {e}", file=sys.stderr)
        return False


def fill_translations(ts_path, lang_code):
    """Parse TS XML and fill unfinished translations with dictionary entries."""
    if not os.path.exists(ts_path):
        return

    tree = ET.parse(ts_path)
    root = tree.getroot()
    dictionary = TRANSLATION_DICTIONARY.get(lang_code, {})
    filled_count = 0

    for context in root.findall('context'):
        for message in context.findall('message'):
            source = message.find('source')
            if source is None or not source.text:
                continue
            source_text = source.text

            translation = message.find('translation')
            if translation is None:
                translation = ET.SubElement(message, 'translation')

            current_text = translation.text or ''
            is_unfinished = translation.get('type') == 'unfinished' or not current_text.strip()

            if is_unfinished:
                if source_text in dictionary:
                    translation.text = dictionary[source_text]
                    if 'type' in translation.attrib:
                        del translation.attrib['type']
                    filled_count += 1
                elif not current_text.strip() and lang_code == 'en':
                    translation.text = source_text
                    if 'type' in translation.attrib:
                        del translation.attrib['type']

    tree.write(ts_path, encoding='utf-8', xml_declaration=True)
    print(f"[{lang_code}] Updated {ts_path}: populated {filled_count} translation(s).")


def main():
    pylupdate_bin = find_pylupdate()
    if not pylupdate_bin:
        print("Warning: Neither pylupdate6 nor pylupdate5 found on PATH.", file=sys.stderr)
        return 1

    py_sources = [
        os.path.join(PLUGIN_DIR, f) for f in os.listdir(PLUGIN_DIR)
        if f.endswith('.py')
    ]
    ui_sources = [
        os.path.join(PLUGIN_DIR, f) for f in os.listdir(PLUGIN_DIR)
        if f.endswith('.ui')
    ]
    source_files = py_sources + ui_sources

    for lang in ['de', 'pl']:
        ts_file = os.path.join(I18N_DIR, f'polystrip_{lang}.ts')
        print(f"Extracting strings for {lang} -> {ts_file}...")
        run_pylupdate(pylupdate_bin, ts_file, source_files)
        fill_translations(ts_file, lang)

    print("Translation update completed successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
