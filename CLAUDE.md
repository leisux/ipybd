# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ipybd` is a Chinese biodiversity data cleaning, statistics, and analysis framework for Python. It provides a unified framework for batch cleaning, transforming, and integrating biodiversity data from different sources, formats, and quality levels.

## Architecture

### Core Classes (`ipybd/core.py`)
- **`FormatDataset`**: Base class for data format conversion with column renaming, splitting, and merging
- **`RestructureTable`**: Subclass with field mapping capability using standard field aliases

### Data Models (`ipybd/table/model.py`)
Use `@imodel` decorator on an `Enum` class to create custom data models. The Enum name becomes the new field name, and the value defines the data transformation:
- `$fieldname` - reference a field for renaming/mapping
- `{'$field': ','}` - split a field by delimiter
- `('$field1', '$field2', ' ')` - merge fields with connector
- `[primary, fallback]` - priority-based selection

Built-in models: `BioGrid`, `Occurrence`, `NoiOccurrence`, `KingdoniaPlant`, `NSII`, `CVH`

### Data Cleaning Classes (`ipybd/function/cleaner.py`)
- `BioName` - scientific name cleaning and online lookup (POWO, IPNI, Tropicos)
- `GeoCoordinate` - latitude/longitude validation and conversion
- `DateTime` - date/time parsing and formatting
- `AdminDiv` - Chinese administrative division parsing
- `HumanName` - person name normalization
- `Number` - numeric value/range cleaning
- `RadioInput` - controlled vocabulary matching
- `FillNa`, `UniqueID`, `Url` - utility cleaners

Use `@ifunc` decorator for custom functions that accept `$`-prefixed data objects.

### Label Generation (`ipybd/label/`)
Uses mustache templates with CSS styling for printing labels. `Label` class generates HTML for printing with barcodes.

### Database Connectors (`ipybd/occurrence/`)
- `cvh.py` - China Virtual Herbarium connector
- `gbif.py` - GBIF connector
- `noi.py` - NOI (noi.link) connector

### Standard Fields (`ipybd/lib/std_fields_alias.json`)
Maps field aliases to DarwinCore-based standard field names for cross-datasource mapping.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run tests
python tests/test.py

# Build documentation (mkdocs)
mkdocs build
mkdocs serve  # local preview
```

## Key Patterns

1. **Model Definition**: Enum classes decorated with `@imodel` define data transformations
2. **Field Reference**: `$` prefix in model values references original data columns
3. **Field Mapping**: `fields_mapping=True` enables cross-datasource field name resolution
4. **Data Processing**: Chain cleaning classes (`BioName`, `GeoCoordinate`, etc.) in model values
5. **Custom Functions**: Decorate functions with `@ifunc` to accept `$`-prefixed pandas Series

## Data Flow

1. Load data via model constructor (Excel, CSV, JSON, DataFrame, etc.)
2. Call `rebuild_table()` to apply model transformations
3. Access cleaned data via `.df` attribute
4. Export via `.to_excel()`, `.to_csv()`, or model-specific methods like `NoiOccurrence.write_json()`
