# Farm Overlap Checker

A QGIS Python plugin for identifying overlapping farm polygons using configurable overlap percentage thresholds. The plugin provides an interactive interface for selecting polygon layers, analysing spatial overlaps, monitoring processing progress, and exporting results to CSV.

## 1. Overview

Farm Overlap Checker is designed to identify farms whose spatial boundaries intersect with those of other farms.

It evaluates the proportion of each farm's area covered by an intersection with another farm. Users can specify independent overlap thresholds for the two farms being compared.

The plugin is particularly useful for agricultural land administration, farm boundary validation, geospatial data quality assurance, and the identification of potentially overlapping farm registrations.

## 2. Features

### Current features

- **Polygon layer selection:** Select from polygon vector layers currently loaded in the QGIS project.
- **Active layer support:** Automatically prioritises the active polygon layer.
- **Layer refresh:** Refresh the available polygon layers when additional layers are loaded into the project.
- **Independent overlap thresholds:** Specify separate overlap percentage thresholds for Farm 1 and Farm 2.
- **OR-based threshold evaluation:** A pair of farms is reported when either farm's overlap percentage exceeds its corresponding threshold.
- **Farm identifier detection:** Automatically detects `farm_id`, with `id` as a fallback.
- **Spatial indexing:** Uses a spatial index to reduce unnecessary geometric comparisons.
- **Duplicate prevention:** Avoids comparing a farm with itself and prevents duplicate farm-pair records.
- **CSV export:** Saves identified overlapping farm pairs to a CSV file.
- **Temporary QGIS results table:** Loads the analysis results into the current QGIS project as a non-spatial temporary memory layer.
- **Processing progress:** Displays analysis progress.
- **Cancellation:** Provides an option to cancel an ongoing analysis.
- **Error handling:** Handles invalid geometries, missing identifiers, and other processing errors.

## 3. How the overlap calculation works

For two intersecting farm polygons, let:

- \(A_1\) denote the area of Farm 1.
- \(A_2\) denote the area of Farm 2.
- \(I_{12}\) denote the area of their intersection.

The overlap percentage relative to Farm 1 is:

$$
O_1 = \frac{I_{12}}{A_1} \times 100
$$

Similarly, the overlap percentage relative to Farm 2 is:

$$
O_2 = \frac{I_{12}}{A_2} \times 100
$$

The plugin reports a pair of farms when:

$$
O_1 > T_1 \quad \text{OR} \quad O_2 > T_2
$$

where:

- \(T_1\) is the user-defined overlap threshold for Farm 1.
- \(T_2\) is the user-defined overlap threshold for Farm 2.

**Important:** The thresholds are evaluated independently. A pair is included if either condition is satisfied. The comparison uses a strict greater-than operator, not greater-than-or-equal-to.

### Example

Suppose:

- Farm 1 has an area of 100 hectares.
- Farm 2 has an area of 50 hectares.
- Their intersection covers 20 hectares.
- Farm 1's threshold is 10%.
- Farm 2's threshold is 30%.

The overlap percentages are:

$$
O_1 = \frac{20}{100} \times 100 = 20\%
$$

$$
O_2 = \frac{20}{50} \times 100 = 40\%
$$

Both conditions are satisfied, so the farm pair is reported.

## 4. Requirements

- QGIS 3.28 or later.
- Python environment provided by QGIS.
- Polygon vector layers supported by QGIS.
- Farm identifier field named `farm_id` or, alternatively, `id`.

The plugin is being developed with compatibility across QGIS 3.x and QGIS 4.x in mind. Compatibility should be verified against the specific QGIS releases used.

## 5. Installation

### Option A: Install from the QGIS plugin directory

1. Locate your active QGIS Python plugins directory.
2. Copy the `FarmOverlapChecker` folder into that directory.
3. Restart QGIS.
4. Open **Plugins → Manage and Install Plugins**.
5. Locate Farm Overlap Checker under the installed plugins.
6. Enable the plugin.

Typical Windows plugin directories include:

**QGIS 3:**

```text
C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
```

**QGIS 4:**

```text
C:\Users\<username>\AppData\Roaming\QGIS\QGIS4\profiles\default\python\plugins\
```

The actual profile directory may differ depending on your QGIS installation.

### Option B: Install from a ZIP package

Once a packaged release is available:

1. Open QGIS.
2. Navigate to **Plugins → Manage and Install Plugins**.
3. Select **Install from ZIP**.
4. Browse to the plugin ZIP file.
5. Click **Install Plugin**.
6. Enable the plugin if necessary.

## 6. Usage
<img width="796" height="322" alt="image" src="https://github.com/user-attachments/assets/9d79daf6-bd97-42ea-9dc6-2860d8653260" />

### Step 1: Load your farm polygon data

Load one or more polygon vector layers into QGIS.

Each layer should contain a unique farm identifier field:

- `farm_id` (preferred), or
- `id` (fallback).

### Step 2: Open Farm Overlap Checker

Open the plugin from the QGIS Plugins menu or its toolbar icon.

### Step 3: Select a polygon layer

Use the polygon layer dropdown to select the layer to analyse.

The active polygon layer is prioritised automatically. Use the Refresh button to update the available layers after adding or removing layers from the QGIS project.

### Step 4: Specify overlap thresholds

Enter the required overlap thresholds for Farm 1 and Farm 2.

For example:

| Parameter | Threshold |
|---|---:|
| Farm 1 overlap threshold | 10% |
| Farm 2 overlap threshold | 5% |

A farm pair will be reported if either farm exceeds its respective threshold.

### Step 5: Specify the output CSV location

Choose the destination and filename for the CSV results file.

### Step 6: Run the analysis

Click the Run button.

The plugin processes the selected polygon layer, displays progress, and identifies qualifying overlapping farm pairs.

The analysis can be cancelled while it is running.

### Step 7: Inspect the results

After successful processing:

- The results are saved to the specified CSV file.
- A temporary, non-spatial results table is added to the QGIS Layers panel.

The temporary table can be opened through QGIS to inspect the identified farm pairs and their overlap percentages.

## 7. Output structure

The results table contains the following fields:

| Field | Description |
|---|---|
| `farm_id_1` | Identifier of the first farm |
| `farm_id_2` | Identifier of the second farm |
| `overlap_percentage_1` | Percentage of Farm 1 covered by the intersection |
| `overlap_percentage_2` | Percentage of Farm 2 covered by the intersection |

The CSV file is the persistent output. The QGIS memory layer is temporary and is lost when the project session ends unless it is exported to a permanent data source.

## 8. Processing approach

The plugin uses a spatial indexing strategy to improve processing efficiency.

Rather than calculating intersections between every possible pair of farms, it:

1. Builds a spatial index for the selected polygon layer.
2. Iterates through the farm features.
3. Retrieves spatially plausible candidate neighbours using bounding-box queries.
4. Avoids self-comparisons and duplicate pair comparisons.
5. Calculates exact polygon intersections for candidate pairs.
6. Computes the overlap percentages.
7. Applies the user-defined thresholds.
8. Writes qualifying results to the CSV output.

This approach reduces unnecessary geometric operations, particularly when working with large farm datasets.

## 9. Project structure

```text
FarmOverlapChecker/
│
├── __init__.py
├── metadata.txt
├── plugin.py
├── dialog.py
│
├── core/
│   ├── __init__.py
│   └── analysis.py
│
├── processing/
│   └── __init__.py
│
└── icons/
    └── icon.svg
```

### Main components

| File | Responsibility |
|---|---|
| `__init__.py` | QGIS plugin entry point |
| `metadata.txt` | Plugin metadata and version information |
| `plugin.py` | Plugin initialisation, toolbar and menu integration |
| `dialog.py` | Graphical user interface and user interactions |
| `core/analysis.py` | Core spatial overlap analysis engine |
| `processing/` | Reserved for future QGIS Processing Toolbox integration |
| `icons/icon.svg` | Plugin icon |

## 10. Current development status

**Version:** 1.1.0

This repository represents the initial functional implementation of Farm Overlap Checker.

The current version provides a standalone QGIS interface for analysing polygon overlaps and exporting results.

### Implemented

- Standalone plugin interface.
- Polygon layer selection.
- Dynamic layer refresh.
- Independent overlap thresholds.
- OR-based overlap evaluation.
- Spatial indexing.
- Duplicate comparison prevention.
- CSV export.
- Temporary QGIS results table.
- Progress monitoring and cancellation.

### Planned improvements

- Integration with the QGIS Processing Toolbox.
- Additional output formats.
- More detailed geometry validation and diagnostics.
- Improved performance for very large polygon datasets.
- Expanded automated testing.
- Formal compatibility testing across QGIS 3.x and QGIS 4.x.
- Distribution through a packaged ZIP release and, eventually, the QGIS Plugin Repository.

## 11. Limitations and considerations

- The analysis is performed on polygon geometries in the selected layer.
- The plugin requires a recognised farm identifier field.
- Invalid, empty, or zero-area geometries may be skipped or produce geometry errors.
- The overlap percentages depend on the area calculations provided by the input layer's coordinate reference system and geometry configuration. A suitable projected CRS is recommended for reliable area-based analysis.
- Bounding-box filtering identifies candidate pairs; actual overlap is determined using polygon intersection geometry.
- The results table is stored in memory and is not automatically permanent.
- The plugin has not yet been formally validated against every supported QGIS version.

## 12. Contributing

Contributions, bug reports, and suggestions are welcome.

When reporting an issue, please include:

- QGIS version.
- Operating system.
- Description of the issue.
- Relevant error messages from the QGIS Python Console.
- A small sample dataset, where possible.

For proposed changes, please describe the problem being addressed and the expected behaviour.

## 13. Licence

A licence has not yet been assigned to this initial repository version. A suitable open-source licence should be selected and added before public distribution.

---

**Farm Overlap Checker**

*A practical GIS tool for identifying and assessing overlapping farm boundaries.*
