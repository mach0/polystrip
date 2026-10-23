# PolyStrip QGIS Plugin Makefile
# Copyright (C) 2017-2026 Werner Macho <werner.macho@gmail.com>

PLUGINNAME = polystrip
PYTHON ?= python3

# QGIS plugin deployment directory for QGIS 3.x / 4.x
QGIS_PLUGIN_DIR ?= $(HOME)/.local/share/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)

.PHONY: all compile transup transcompile transclean clean zip package deploy test check help

all: compile

help:
	@echo "PolyStrip Plugin Makefile targets:"
	@echo "  make compile       - Compile translation files (.qm)"
	@echo "  make transup       - Extract translatable strings into .ts files"
	@echo "  make transcompile  - Compile .ts files to binary .qm files"
	@echo "  make transclean    - Remove compiled .qm files"
	@echo "  make test          - Run unit test suite"
	@echo "  make check         - Verify Python syntax across all modules"
	@echo "  make clean         - Remove bytecode, caches, and build packages"
	@echo "  make deploy        - Install plugin to local QGIS profile"
	@echo "  make zip / package - Build clean release archive ($(PLUGINNAME).zip)"

compile: transcompile

transup:
	@echo "----------------------------------------"
	@echo "Updating translation source (.ts) files"
	@echo "----------------------------------------"
	$(PYTHON) scripts/update_translations.py

transcompile:
	@echo "----------------------------------------"
	@echo "Compiling translation (.qm) files"
	@echo "----------------------------------------"
	$(PYTHON) scripts/compile_translations.py

transclean:
	@echo "Removing compiled translation (.qm) files..."
	rm -f polystrip/i18n/*.qm

check:
	@echo "Checking Python syntax..."
	$(PYTHON) -m py_compile polystrip/*.py

test: compile
	@echo "----------------------------------------"
	@echo "Running unit test suite"
	@echo "----------------------------------------"
	$(PYTHON) -m unittest discover -s test -p "test_*.py" -v

clean: transclean
	@echo "Cleaning temporary files and build artifacts..."
	rm -rf build dist *.zip polystrip.zip .pytest_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	find . -type f -name "*.qm.stash" -delete 2>/dev/null || true

deploy: compile
	@echo "Deploying $(PLUGINNAME) to $(QGIS_PLUGIN_DIR)..."
	rm -rf $(QGIS_PLUGIN_DIR)
	mkdir -p $(QGIS_PLUGIN_DIR)
	cp -r polystrip/* $(QGIS_PLUGIN_DIR)/
	find $(QGIS_PLUGIN_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find $(QGIS_PLUGIN_DIR) -type f -name "*.py[cod]" -delete 2>/dev/null || true
	@echo "Successfully deployed $(PLUGINNAME) to $(QGIS_PLUGIN_DIR)"

zip: package

package: clean compile test
	@echo "----------------------------------------"
	@echo "Creating clean release zip bundle"
	@echo "----------------------------------------"
	rm -rf build $(PLUGINNAME).zip
	mkdir -p build/$(PLUGINNAME)
	cp -r polystrip/* build/$(PLUGINNAME)/
	cp LICENSE build/$(PLUGINNAME)/LICENSE
	find build/$(PLUGINNAME) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find build/$(PLUGINNAME) -type f -name "*.py[cod]" -delete 2>/dev/null || true
	find build/$(PLUGINNAME) -type f -name "*.ts" -delete 2>/dev/null || true
	find build/$(PLUGINNAME) -type f -name "*.pro" -delete 2>/dev/null || true
	cd build && zip -9 -r ../$(PLUGINNAME).zip $(PLUGINNAME)
	rm -rf build
	@echo "----------------------------------------"
	@echo "Plugin release package created: $(PLUGINNAME).zip"
	@echo "----------------------------------------"
