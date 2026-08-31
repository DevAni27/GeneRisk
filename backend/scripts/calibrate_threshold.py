import argparse
import csv
import json
from pathlib import Path

import numpy as np

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from sklearn.model_selection import (
    StratifiedGroupKFold,
)


VALID_LABELS = {
    "Pathogenic": 1,
    "Benign": 0,
}


def load_scored_variants(
    path: Path,
):
    rows = []

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(handle)

        for row in reader:

            if (
                row.get("score_status")
                != "success"
            ):
                continue

            label = row.get(
                "clinical_label"
            )

            if label not in VALID_LABELS:
                continue

            rows.append(
                {
                    "chrom": row["chrom"],
                    "position": int(
                        row["position"]
                    ),
                    "ref": row["ref"],
                    "alt": row["alt"],
                    "label": label,
                    "y": VALID_LABELS[
                        label
                    ],
                    "delta_score": float(
                        row["delta_score"]
                    ),
                }
            )

    if not rows:
        raise ValueError(
            "No usable scored variants found."
        )

    labels = {
        row["y"]
        for row in rows
    }

    if labels != {0, 1}:
        raise ValueError(
            "Calibration requires BOTH "
            "Pathogenic and Benign variants."
        )

    return rows


def candidate_thresholds(
    delta_scores: np.ndarray,
):
    unique_scores = np.sort(
        np.unique(delta_scores)
    )

    candidates = []

    candidates.append(
        np.nextafter(
            unique_scores[0],
            -np.inf,
        )
    )

    for left, right in zip(
        unique_scores[:-1],
        unique_scores[1:],
    ):
        candidates.append(
            (left + right) / 2.0
        )

    candidates.append(
        np.nextafter(
            unique_scores[-1],
            np.inf,
        )
    )

    return candidates


def predictions_from_threshold(
    delta_scores,
    threshold,
):
    return (
        delta_scores <= threshold
    ).astype(int)


def calculate_metrics(
    y_true,
    y_pred,
):
    tn, fp, fn, tp = (
        confusion_matrix(
            y_true,
            y_pred,
            labels=[0, 1],
        ).ravel()
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    return {
        "accuracy": float(
            accuracy_score(
                y_true,
                y_pred,
            )
        ),

        "balanced_accuracy": float(
            balanced_accuracy_score(
                y_true,
                y_pred,
            )
        ),

        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),

        "sensitivity": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),

        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),

        "specificity": float(
            specificity
        ),

        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),

        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def find_balanced_threshold(
    delta_scores,
    y_true,
):
    best = None

    for threshold in candidate_thresholds(
        delta_scores
    ):

        y_pred = (
            predictions_from_threshold(
                delta_scores,
                threshold,
            )
        )

        metrics = calculate_metrics(
            y_true,
            y_pred,
        )

        youden_j = (
            metrics["sensitivity"]
            + metrics["specificity"]
            - 1.0
        )

        result = {
            "threshold": float(
                threshold
            ),
            "youden_j": float(
                youden_j
            ),
            "metrics": metrics,
        }

        if best is None:
            best = result
            continue

        current_key = (
            result["youden_j"],
            result["metrics"][
                "balanced_accuracy"
            ],
            result["metrics"][
                "sensitivity"
            ],
            result["metrics"][
                "specificity"
            ],
        )

        best_key = (
            best["youden_j"],
            best["metrics"][
                "balanced_accuracy"
            ],
            best["metrics"][
                "sensitivity"
            ],
            best["metrics"][
                "specificity"
            ],
        )

        if current_key > best_key:
            best = result

    return best


def find_high_sensitivity_threshold(
    delta_scores,
    y_true,
    target_sensitivity=0.95,
):
    eligible = []

    for threshold in candidate_thresholds(
        delta_scores
    ):

        y_pred = (
            predictions_from_threshold(
                delta_scores,
                threshold,
            )
        )

        metrics = calculate_metrics(
            y_true,
            y_pred,
        )

        if (
            metrics["sensitivity"]
            >= target_sensitivity
        ):
            eligible.append(
                {
                    "threshold": float(
                        threshold
                    ),
                    "metrics": metrics,
                }
            )

    if not eligible:
        return None

    return max(
        eligible,
        key=lambda result: (
            result["metrics"][
                "specificity"
            ],
            result["metrics"][
                "balanced_accuracy"
            ],
            result["metrics"][
                "precision"
            ],
        ),
    )


def group_cross_validation(
    delta_scores,
    y_true,
    groups,
):
    """
    Threshold is selected ONLY from each training
    fold and then evaluated on its test fold.

    Variants at the same genomic position remain
    together to reduce leakage.
    """

    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    all_true = []
    all_pred = []

    fold_results = []

    for fold_number, (
        train_index,
        test_index,
    ) in enumerate(
        splitter.split(
            delta_scores,
            y_true,
            groups,
        ),
        start=1,
    ):

        train_scores = (
            delta_scores[
                train_index
            ]
        )

        train_labels = (
            y_true[
                train_index
            ]
        )

        test_scores = (
            delta_scores[
                test_index
            ]
        )

        test_labels = (
            y_true[
                test_index
            ]
        )

        calibration = (
            find_balanced_threshold(
                train_scores,
                train_labels,
            )
        )

        threshold = calibration[
            "threshold"
        ]

        test_predictions = (
            predictions_from_threshold(
                test_scores,
                threshold,
            )
        )

        metrics = calculate_metrics(
            test_labels,
            test_predictions,
        )

        fold_results.append(
            {
                "fold": fold_number,
                "threshold": threshold,
                "variants": int(
                    len(test_index)
                ),
                "metrics": metrics,
            }
        )

        all_true.extend(
            test_labels.tolist()
        )

        all_pred.extend(
            test_predictions.tolist()
        )

    overall_metrics = (
        calculate_metrics(
            np.asarray(all_true),
            np.asarray(all_pred),
        )
    )

    return {
        "method":
            "5-fold StratifiedGroupKFold",

        "grouping":
            "chromosome + genomic position",

        "folds":
            fold_results,

        "overall_metrics":
            overall_metrics,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_csv",
        type=Path,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/hbb_calibration.json"
        ),
    )

    parser.add_argument(
        "--target-sensitivity",
        type=float,
        default=0.95,
    )

    args = parser.parse_args()

    rows = load_scored_variants(
        args.input_csv
    )

    delta_scores = np.asarray(
        [
            row["delta_score"]
            for row in rows
        ],
        dtype=float,
    )

    y_true = np.asarray(
        [
            row["y"]
            for row in rows
        ],
        dtype=int,
    )

    groups = np.asarray(
        [
            (
                f"{row['chrom']}:"
                f"{row['position']}"
            )
            for row in rows
        ]
    )

    pathogenic_count = int(
        np.sum(
            y_true == 1
        )
    )

    benign_count = int(
        np.sum(
            y_true == 0
        )
    )

    # More negative delta =
    # stronger pathogenic signal,
    # therefore negate for AUROC.
    auc = float(
        roc_auc_score(
            y_true,
            -delta_scores,
        )
    )

    balanced = (
        find_balanced_threshold(
            delta_scores,
            y_true,
        )
    )

    high_sensitivity = (
        find_high_sensitivity_threshold(
            delta_scores,
            y_true,
            target_sensitivity=(
                args.target_sensitivity
            ),
        )
    )

    cross_validation = (
        group_cross_validation(
            delta_scores,
            y_true,
            groups,
        )
    )

    result = {
        "version": 1,

        "gene": "HBB",

        "genome_build":
            "GRCh38",

        "window_size": 8192,

        "model": "evo2-7b",

        "scoring_method":
            "mean_log_likelihood_delta",

        "delta_definition":
            "variant_score - reference_score",

        "rule":
            "delta_score <= threshold "
            "=> likely_pathogenic",

        "dataset": {
            "total_variants":
                len(rows),

            "pathogenic":
                pathogenic_count,

            "benign":
                benign_count,

            "source_file":
                args.input_csv.name,
        },

        "auroc": auc,

        # This is the threshold the API uses.
        "threshold":
            balanced["threshold"],

        "threshold_strategy":
            "maximum_youden_j_balanced",

        "metrics":
            balanced["metrics"],

        "youden_j":
            balanced["youden_j"],

        "operating_points": {
            "balanced":
                balanced,

            "high_sensitivity":
                high_sensitivity,
        },

        "cross_validation":
            cross_validation,

        "limitations": [
            (
                "Threshold was fit on a "
                "small HBB SNV dataset."
            ),
            (
                "Dataset is class-imbalanced."
            ),
            (
                "This calibration is not "
                "clinical validation."
            ),
            (
                "Confidence probabilities "
                "are not calibrated."
            ),
        ],
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with args.output.open(
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            result,
            handle,
            indent=2,
        )

    print()
    print(
        "=== HBB REAL CALIBRATION ==="
    )
    print()

    print(
        f"Variants: {len(rows)}"
    )

    print(
        f"Pathogenic: "
        f"{pathogenic_count}"
    )

    print(
        f"Benign: {benign_count}"
    )

    print()
    print(
        f"AUROC: {auc:.4f}"
    )

    print()
    print(
        "=== BALANCED OPERATING POINT ==="
    )

    print(
        f"Threshold: "
        f"{balanced['threshold']}"
    )

    metrics = balanced[
        "metrics"
    ]

    print(
        f"Sensitivity: "
        f"{metrics['sensitivity']:.4f}"
    )

    print(
        f"Specificity: "
        f"{metrics['specificity']:.4f}"
    )

    print(
        f"Balanced accuracy: "
        f"{metrics['balanced_accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"F1: "
        f"{metrics['f1']:.4f}"
    )

    if high_sensitivity:

        print()
        print(
            "=== HIGH-SENSITIVITY "
            "OPERATING POINT ==="
        )

        high_metrics = (
            high_sensitivity[
                "metrics"
            ]
        )

        print(
            f"Threshold: "
            f"{high_sensitivity['threshold']}"
        )

        print(
            f"Sensitivity: "
            f"{high_metrics['sensitivity']:.4f}"
        )

        print(
            f"Specificity: "
            f"{high_metrics['specificity']:.4f}"
        )

    cv_metrics = (
        cross_validation[
            "overall_metrics"
        ]
    )

    print()
    print(
        "=== GROUP-AWARE "
        "5-FOLD CV ==="
    )

    print(
        f"Sensitivity: "
        f"{cv_metrics['sensitivity']:.4f}"
    )

    print(
        f"Specificity: "
        f"{cv_metrics['specificity']:.4f}"
    )

    print(
        f"Balanced accuracy: "
        f"{cv_metrics['balanced_accuracy']:.4f}"
    )

    print(
        f"F1: "
        f"{cv_metrics['f1']:.4f}"
    )

    print()
    print(
        f"Saved calibration to: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()