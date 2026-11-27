# 🌾 Farm Overlap Checker

**A QGIS 4 plugin for identifying and analysing overlapping farm polygons.**

[![QGIS](https://img.shields.io/badge/QGIS-4.x-589632?logo=qgis&logoColor=white)](https://qgis.org/)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/DataSurgeonGh/FarmOverlapChecker/releases)
[![License](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)

**Farm Overlap Checker** is an open-source QGIS plugin designed to identify overlapping farm polygons using configurable overlap percentage thresholds.

It provides two ways to perform the analysis:

- 🖥️ **Standalone Interface:** A user-friendly graphical interface for selecting polygon layers, configuring thresholds, running the analysis and exporting results.
- ⚙️ **Processing Toolbox:** A processing algorithm that integrates directly into the QGIS Processing framework.

The plugin uses spatial indexing to improve the efficiency of overlap detection, making it suitable for analysing datasets containing large numbers of farm polygons.

---

## 📸 Plugin Preview

![Farm Overlap Checker interface](https://github.com/user-attachments/assets/9d79daf6-bd97-42ea-9dc6-2860d8653260)

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🗺️ Polygon analysis | Identifies overlaps between farm polygon features. |
| 📊 Configurable thresholds | Allows separate overlap percentage thresholds for each farm. |
| 🔀 Independent threshold evaluation | Uses an OR condition to determine whether an overlapping pair qualifies for reporting. |
| ⚡ Spatial indexing | Uses a spatial index to reduce unnecessary geometric comparisons. |
| 🖥️ Standalone interface | Provides a dedicated graphical interface for running analyses. |
| ⚙️ Processing Toolbox | Integrates with the QGIS Processing Toolbox. |
| 📁 CSV export | Exports identified overlapping pairs and their overlap percentages. |
| 📈 Progress reporting | Displays analysis progress. |
| ⏹️ Cancellation | Allows users to cancel an ongoing analysis. |
| 📋 Temporary results table | Creates a temporary QGIS memory layer containing the analysis results. |
| 🔄 Layer refresh | Allows users to refresh the available polygon layers. |

---

## 📦 Requirements

- **QGIS 4.x**
- A polygon vector layer containing farm boundaries.
- A suitable projected coordinate reference system is recommended for meaningful area measurements.

> **Compatibility:** Version 2.0.0 is developed for QGIS 4.x. It is not intended for QGIS 3.x.

---

## 🚀 Installation

### Option 1: Install from ZIP

1. Download the latest release ZIP file from the [GitHub Releases page](https://github.com/DataSurgeonGh/FarmOverlapChecker/releases).
2. Open QGIS 4.
3. Navigate to **Plugins → Manage and Install Plugins**.
4. Select **Install from ZIP**.
5. Browse to the downloaded `FarmOverlapChecker-2.0.0.zip` file.
6. Click **Install Plugin**.
7. Enable Farm Overlap Checker if it is not enabled automatically.

### Option 2: Manual installation

1. Download or clone this repository.
2. Extract the plugin folder named `FarmOverlapChecker`.
3. Copy the folder into the QGIS Python plugins directory.

On Windows, the typical location is:

```text
%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\
```

The final directory structure should be:

```text
plugins/
└── FarmOverlapChecker/
    ├── __init__.py
    ├── plugin.py
    ├── dialog.py
    ├── metadata.txt
    ├── LICENSE
    ├── README.md
    ├── core/
    │   ├── __init__.py
    │   └── analysis.py
    ├── icons/
    │   └── icon.svg
    └── processing/
        ├── __init__.py
        ├── algorithms.py
        └── provider.py
```

4. Restart QGIS.
5. Open **Plugins → Manage and Install Plugins**.
6. Enable **Farm Overlap Checker**.

---

## 🖥️ Using the Standalone Interface

After enabling the plugin:

1. Open **Farm Overlap Checker** from the QGIS Plugins menu or toolbar.
2. Select the polygon layer containing the farm boundaries.
3. Configure the two overlap percentage thresholds.
4. Specify the destination for the CSV output file.
5. Click the analysis button to begin processing.
6. Monitor the progress indicator.
7. When processing completes, inspect the exported CSV and the temporary results table added to the QGIS Layers panel.

### Configuring overlap thresholds

The plugin uses two independent thresholds:

- **Threshold 1:** Minimum required overlap percentage relative to the first farm.
- **Threshold 2:** Minimum required overlap percentage relative to the second farm.

Both thresholds must be between 0% and 100%.

The thresholds are evaluated independently. An overlapping pair is reported when either percentage strictly exceeds its corresponding threshold.

---

## ⚙️ Using the Processing Toolbox

Farm Overlap Checker also provides an algorithm within the QGIS Processing Toolbox.

To use it:

1. Open the **Processing Toolbox**.
2. Search for `Check Farm Overlaps`.
3. Open the algorithm.
4. Select the input polygon layer.
5. Specify the two overlap percentage thresholds.
6. Choose the CSV output destination.
7. Run the algorithm.

The algorithm reports the total number of farms, overlapping pairs, skipped features and geometry errors.

This integration makes the plugin suitable for users who prefer incorporating overlap analysis into their existing QGIS processing workflows.

---

## 🧮 Mathematical Formulation

Let the farm polygon dataset be:

\[
\mathcal{F}=\{F_1,F_2,\ldots,F_n\}
\]

where each \(F_i\) represents an individual farm polygon.

For two distinct farm polygons, \(F_i\) and \(F_j\), their intersection is:

\[
I_{ij}=F_i\cap F_j
\]

The area of their intersection is:

\[
A_{ij}=\operatorname{Area}(F_i\cap F_j)
\]

Let the respective areas of the two farms be:

\[
A_i=\operatorname{Area}(F_i)
\]

\[
A_j=\operatorname{Area}(F_j)
\]

The overlap percentage relative to the first farm is:

\[
\boxed{
O_{ij}^{(i)}
=
\frac{A_{ij}}{A_i}\times100
}
\]

Similarly, the overlap percentage relative to the second farm is:

\[
\boxed{
O_{ij}^{(j)}
=
\frac{A_{ij}}{A_j}\times100
}
\]

### The overlap decision rule

Let:

- \(T_1\) denote the first overlap threshold.
- \(T_2\) denote the second overlap threshold.

The pair of farms is reported when:

\[
\boxed{
O_{ij}^{(i)}>T_1
\quad\mathbf{OR}\quad
O_{ij}^{(j)}>T_2
}
\]

Equivalently, the reporting indicator is:

\[
R_{ij}
=
\begin{cases}
1, & O_{ij}^{(i)}>T_1
\text{ or }
O_{ij}^{(j)}>T_2,\\
0, & \text{otherwise}.
\end{cases}
\]

**Important:** The plugin uses a strict greater-than comparison (\(>\)), not greater-than-or-equal-to (\(\geq\)).

It also uses an **OR condition**, not an AND condition. Therefore, an overlapping pair qualifies if at least one of its two overlap percentages exceeds its corresponding threshold.

---

## 📊 Worked Example

Consider three farm polygons with the following characteristics:

| Farm | Area |
|---|---:|
| Farm A | 10,000 m² |
| Farm B | 10,000 m² |
| Farm C | 2,500 m² |

Suppose their intersections are:

- Farm A and Farm B: 2,000 m².
- Farm A and Farm C: 2,500 m².
- Farm B and Farm C: 0 m².

The resulting overlap percentages are:

| Farm pair | Overlap area | Percentage of first farm | Percentage of second farm |
|---|---:|---:|---:|
| A–B | 2,000 m² | 20% | 20% |
| A–C | 2,500 m² | 25% | 100% |
| B–C | 0 m² | 0% | 0% |

Suppose the configured thresholds are:

\[
T_1=30\%, \qquad T_2=90\%
\]

For Farm A and Farm B:

\[
20\%>30\% \quad \text{OR} \quad 20\%>90\%
\]

Both conditions are false. Therefore, the pair is not reported.

For Farm A and Farm C:

\[
25\%>30\% \quad \text{OR} \quad 100\%>90\%
\]

The first condition is false, but the second is true. Therefore, the pair is reported.

**Result:** Farm A and Farm C are identified as an overlapping pair.

This illustrates why the two thresholds must be evaluated independently.

---

## 📁 CSV Output

The analysis exports the identified overlapping farm pairs to a CSV file.

The output contains the following columns:

| Column | Description |
|---|---|
| `farm_id_1` | Identifier of the first farm. |
| `farm_id_2` | Identifier of the second farm. |
| `overlap_percentage_1` | Percentage of the first farm covered by the intersection. |
| `overlap_percentage_2` | Percentage of the second farm covered by the intersection. |

### Example output

```csv
farm_id_1,farm_id_2,overlap_percentage_1,overlap_percentage_2
FARM_A,FARM_C,25.000000,100.000000
```

Overlap percentages are exported to six decimal places.

The plugin also creates a temporary QGIS memory table containing the analysis results.

---

## ⚡ Performance and Processing

Farm Overlap Checker uses a spatial index to improve the efficiency of identifying candidate polygon pairs.

Rather than performing intersection calculations indiscriminately across every possible pair of polygons, the spatial index helps identify geometrically relevant candidates.

This reduces unnecessary geometric comparisons, particularly when working with large farm datasets.

### Progress monitoring and cancellation

During analysis:

- The progress indicator displays processing progress.
- Users can cancel an ongoing operation.
- Incomplete output from a cancelled analysis is discarded.
- An existing CSV output is protected from being overwritten by an incomplete analysis.

These features help make the analysis more reliable when working with large datasets.

---

## ⚠️ Important Considerations

1. **Polygon layers only:** The plugin is designed for polygon vector layers. Point and line layers are excluded.
2. **Coordinate reference system:** Use an appropriate projected CRS for meaningful area calculations. The plugin uses the areas returned by QGIS geometry operations.
3. **Overlap thresholds:** The two thresholds are independent and are evaluated using an OR condition.
4. **Strict comparison:** A percentage exactly equal to its threshold does not qualify.
5. **Farm identifiers:** The analysis uses an available `farm_id` or `id` field to identify farms.
6. **Geometry quality:** Invalid, empty or problematic geometries may affect intersection calculations. Review the source geometries when geometry errors are reported.
7. **Temporary results:** The results table is a temporary QGIS memory layer. Export or save results separately if they need to be retained beyond the current QGIS session.

---

## 🧪 Testing

Version 2.0.0 has been tested in QGIS 4 using controlled polygon datasets and larger test datasets.

The tests included:

- Standalone interface operation.
- Processing Toolbox integration.
- Polygon layer selection and filtering.
- Independent overlap thresholds.
- OR-based overlap evaluation.
- Strict greater-than threshold comparisons.
- CSV output generation.
- Progress reporting and cancellation.
- Protection of existing CSV output during cancelled reruns.
- Temporary results table creation.
- Analysis involving 5,000 polygon features.
- Installation and operation from the distributable ZIP package.

---

## 📂 Project Structure

```text
FarmOverlapChecker/
│
├── __init__.py
├── plugin.py
├── dialog.py
├── metadata.txt
├── README.md
├── LICENSE
├── image.png
│
├── core/
│   ├── __init__.py
│   └── analysis.py
│
├── icons/
│   └── icon.svg
│
└── processing/
    ├── __init__.py
    ├── algorithms.py
    └── provider.py
```

### Main components

| File | Responsibility |
|---|---|
| `plugin.py` | Plugin initialisation, menu and toolbar integration, and Processing provider registration. |
| `dialog.py` | Standalone graphical interface. |
| `core/analysis.py` | Core overlap detection and CSV export logic. |
| `processing/algorithms.py` | QGIS Processing algorithm implementation. |
| `processing/provider.py` | Registers the plugin's Processing algorithm provider. |
| `metadata.txt` | Plugin metadata and compatibility information. |

---

## 🛠️ Development

The plugin is developed using Python and the QGIS Python API (PyQGIS).

To contribute:

1. Fork the repository.
2. Clone your fork.
3. Make your changes in a separate development branch.
4. Test the changes in QGIS 4.
5. Submit a pull request describing the changes.

Repository:

[https://github.com/DataSurgeonGh/FarmOverlapChecker](https://github.com/DataSurgeonGh/FarmOverlapChecker)

Bug reports and feature requests can be submitted through the [GitHub Issues page](https://github.com/DataSurgeonGh/FarmOverlapChecker/issues).

---

## 👨‍💻 Author

**KA Chanik**

Email: [drkan1815@gmail.com](mailto:drkan1815@gmail.com)

GitHub: [DataSurgeonGh](https://github.com/DataSurgeonGh)

---

## 📜 Licence

Farm Overlap Checker is free and open-source software distributed under the **GNU General Public License v2.0 or later (GPL-2.0-or-later)**.

See the [LICENSE](LICENSE) file for the full licence terms.

---

<p align="center">

**🌾 Farm Overlap Checker — Making farm boundary overlap analysis easier with QGIS.**

</p>