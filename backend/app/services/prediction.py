import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BENIGN_MEDIAN_DELTA = 0.00005994313155488484
PATHOGENIC_MEDIAN_DELTA = -0.0022522188788729


load_dotenv()


class PredictionServiceError(Exception):
    """Raised when calibration data cannot be loaded."""


@dataclass(frozen=True)
class PredictionResult:
    prediction: str | None
    confidence: float | None
    calibrated: bool
    threshold: float | None
    pathogenicity_index: int | None
    signal_strength: str | None
    
def calculate_pathogenicity_index(
    delta_score: float,
    threshold: float,
) -> int:
    """
    Convert Evo2 delta score into a user-friendly 0-100 index.

    50 = calibrated HBB decision threshold.
    Lower scores are more benign-like.
    Higher scores are more pathogenic-like.

    This is NOT a probability or confidence percentage.
    """

    if delta_score <= threshold:
        denominator = (
            threshold
            - PATHOGENIC_MEDIAN_DELTA
        )

        if denominator == 0:
            return 50

        value = 50 + 50 * (
            (threshold - delta_score)
            / denominator
        )

        return int(
            round(
                min(
                    max(value, 50),
                    100,
                )
            )
        )

    denominator = (
        BENIGN_MEDIAN_DELTA
        - threshold
    )

    if denominator == 0:
        return 50

    value = 50 - 50 * (
        (delta_score - threshold)
        / denominator
    )

    return int(
        round(
            min(
                max(value, 0),
                50,
            )
        )
    )
    
def get_signal_strength(
    pathogenicity_index: int,
) -> str:

    if pathogenicity_index >= 70:
        return "strong_pathogenic"

    if pathogenicity_index >= 50:
        return "pathogenic_like"

    if pathogenicity_index >= 30:
        return "benign_like"

    return "strong_benign"


def load_calibration() -> dict | None:
    """
    Load the real HBB calibration file.

    Calibration is deliberately opt-in through an
    environment variable so our smoke-test JSON can never
    accidentally become the production threshold.
    """

    calibration_path = os.getenv(
        "HBB_CALIBRATION_PATH"
    )

    if not calibration_path:
        return None

    path = Path(calibration_path)

    if not path.exists():
        raise PredictionServiceError(
            f"Calibration file not found: {path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        raise PredictionServiceError(
            f"Could not load calibration file: {exc}"
        ) from exc

    if "threshold" not in data:
        raise PredictionServiceError(
            "Calibration file has no threshold."
        )

    return data


def predict_from_delta(
    delta_score: float,
) -> PredictionResult:
    """
    Convert an Evo2 delta score into a calibrated
    HBB prediction.

    Until real calibration is configured, return an
    explicitly uncalibrated result.
    """

    calibration = load_calibration()

    if calibration is None:
        return PredictionResult(
            prediction=None,
            confidence=None,
            calibrated=False,
            threshold=None,
            pathogenicity_index=None,
            signal_strength=None,
        )

    threshold = float(
        calibration["threshold"]
    )

    if delta_score <= threshold:
        prediction = "likely_pathogenic"
    else:
        prediction = "likely_benign"

    pathogenicity_index = (
        calculate_pathogenicity_index(
            delta_score=delta_score,
            threshold=threshold,
        )
    )

    signal_strength = (
        get_signal_strength(
            pathogenicity_index
        )
    )

    return PredictionResult(
        prediction=prediction,
        confidence=None,
        calibrated=True,
        threshold=threshold,
        pathogenicity_index=(
            pathogenicity_index
        ),
        signal_strength=signal_strength,
    )