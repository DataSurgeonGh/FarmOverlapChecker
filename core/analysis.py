
import csv
import math
import os
import tempfile

from qgis.core import (
    QgsSpatialIndex,
    QgsWkbTypes
)


def run_overlap_analysis(
    layer,
    threshold1,
    threshold2,
    output_csv,
    progress_callback=None,
    cancel_callback=None
):
    """
    Identify overlapping polygon features.

    A pair is included when:

        overlap1 > threshold1 OR overlap2 > threshold2

    The function writes results incrementally to a temporary CSV.
    The final CSV is created only when analysis completes successfully.

    Parameters
    ----------
    layer : QgsVectorLayer
        Input polygon layer.

    threshold1 : float
        Minimum overlap percentage for Farm 1.

    threshold2 : float
        Minimum overlap percentage for Farm 2.

    output_csv : str
        Destination CSV file.

    progress_callback : callable, optional
        Receives integer progress percentages.

    cancel_callback : callable, optional
        Returns True when cancellation is requested.

    Returns
    -------
    dict
        Summary of the completed analysis.
    """

    temp_path = None

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if layer is None or not layer.isValid():
        raise ValueError("The selected layer is invalid.")

    if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError("The selected layer must contain polygons.")

    try:
        threshold1 = float(threshold1)
        threshold2 = float(threshold2)
    except (TypeError, ValueError):
        raise ValueError("Overlap thresholds must be numeric.")

    if not math.isfinite(threshold1) or not math.isfinite(threshold2):
        raise ValueError("Overlap thresholds must be finite numbers.")

    if not (0 <= threshold1 <= 100):
        raise ValueError("Farm 1 threshold must be between 0 and 100.")

    if not (0 <= threshold2 <= 100):
        raise ValueError("Farm 2 threshold must be between 0 and 100.")

    if not output_csv:
        raise ValueError("An output CSV path is required.")

    output_csv = os.path.abspath(output_csv)

    output_directory = os.path.dirname(output_csv)

    if not os.path.isdir(output_directory):
        raise ValueError("The output directory does not exist.")

    # --------------------------------------------------
    # IDENTIFY FARM ID FIELD
    # --------------------------------------------------

    field_names = layer.fields().names()

    field_lookup = {
        name.lower(): name
        for name in field_names
    }

    if "farm_id" in field_lookup:
        id_field = field_lookup["farm_id"]

    elif "id" in field_lookup:
        id_field = field_lookup["id"]

    else:
        raise ValueError(
            "Neither 'farm_id' nor 'id' exists in the selected layer."
        )

    # --------------------------------------------------
    # INITIALISE ANALYSIS
    # --------------------------------------------------

    total_features = layer.featureCount()

    if total_features == 0:
        raise ValueError("The selected layer contains no features.")

    if progress_callback:
        progress_callback(0)

    if cancel_callback and cancel_callback():
        raise InterruptedError("Analysis cancelled by user.")

    # --------------------------------------------------
    # BUILD SPATIAL INDEX
    # --------------------------------------------------

    spatial_index = QgsSpatialIndex(
        layer.getFeatures()
    )

    # --------------------------------------------------
    # INITIALISE COUNTERS
    # --------------------------------------------------

    processed_features = 0
    overlapping_pairs = 0
    skipped_features = 0
    geometry_errors = 0

    # --------------------------------------------------
    # CREATE TEMPORARY CSV
    # --------------------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8-sig",
        newline="",
        suffix=".tmp",
        prefix="farm_overlap_",
        dir=output_directory,
        delete=False
    )

    temp_path = temp_file.name

    try:

        with temp_file as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow([
                "farm_id_1",
                "farm_id_2",
                "overlap_percentage_1",
                "overlap_percentage_2"
            ])

            # ------------------------------------------
            # PROCESS FEATURES
            # ------------------------------------------

            for feature1 in layer.getFeatures():

                # Check cancellation
                if cancel_callback and cancel_callback():
                    raise InterruptedError(
                        "Analysis cancelled by user."
                    )

                processed_features += 1

                try:

                    geom1 = feature1.geometry()

                    # Skip invalid or empty geometries
                    if geom1.isNull() or geom1.isEmpty():
                        skipped_features += 1
                        continue

                    area1 = geom1.area()

                    if not math.isfinite(area1) or area1 <= 0:
                        skipped_features += 1
                        continue

                    farm_id1 = feature1[id_field]

                    # ----------------------------------
                    # FIND POSSIBLE OVERLAPPING FEATURES
                    # ----------------------------------

                    candidate_ids = spatial_index.intersects(
                        geom1.boundingBox()
                    )

                    for candidate_id in candidate_ids:

                        if cancel_callback and cancel_callback():
                            raise InterruptedError(
                                "Analysis cancelled by user."
                            )

                        # Avoid self-comparisons and duplicate pairs
                        if candidate_id <= feature1.id():
                            continue

                        feature2 = layer.getFeature(candidate_id)

                        if not feature2.isValid():
                            continue

                        geom2 = feature2.geometry()

                        if geom2.isNull() or geom2.isEmpty():
                            continue

                        area2 = geom2.area()

                        if not math.isfinite(area2) or area2 <= 0:
                            continue

                        # ------------------------------
                        # CALCULATE INTERSECTION
                        # ------------------------------

                        try:

                            intersection = geom1.intersection(
                                geom2
                            )

                            if (
                                intersection.isNull()
                                or intersection.isEmpty()
                            ):
                                continue

                            intersection_area = intersection.area()

                        except Exception:
                            geometry_errors += 1
                            continue

                        if (
                            not math.isfinite(intersection_area)
                            or intersection_area <= 0
                        ):
                            continue

                        # ------------------------------
                        # CALCULATE OVERLAP PERCENTAGES
                        # ------------------------------

                        overlap1 = (
                            intersection_area / area1
                        ) * 100

                        overlap2 = (
                            intersection_area / area2
                        ) * 100

                        # ------------------------------
                        # APPLY OR THRESHOLD LOGIC
                        # ------------------------------

                        if (
                            overlap1 > threshold1
                            or overlap2 > threshold2
                        ):

                            farm_id2 = feature2[id_field]

                            writer.writerow([
                                farm_id1,
                                farm_id2,
                                round(overlap1, 6),
                                round(overlap2, 6)
                            ])

                            overlapping_pairs += 1

                finally:

                    # Update progress even when a feature
                    # is skipped because of invalid geometry.
                    if progress_callback:

                        percentage = int(
                            processed_features
                            / total_features
                            * 100
                        )

                        progress_callback(
                            min(percentage, 100)
                        )

            # Ensure all rows are written to disk
            csv_file.flush()

        # ----------------------------------------------
        # FINALISE CSV
        # ----------------------------------------------

        if cancel_callback and cancel_callback():
            raise InterruptedError(
                "Analysis cancelled before finalising output."
            )

        os.replace(temp_path, output_csv)
        temp_path = None

        if progress_callback:
            progress_callback(100)

        # ----------------------------------------------
        # RETURN SUMMARY
        # ----------------------------------------------

        return {
            "total_farms": processed_features,
            "overlapping_pairs": overlapping_pairs,
            "output_file": output_csv,
            "skipped_features": skipped_features,
            "geometry_errors": geometry_errors,
            "id_field": id_field
        }

    finally:

        # Remove temporary output if analysis fails or is cancelled
        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)
            except OSError:
                pass
