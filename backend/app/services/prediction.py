import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class PredictionServiceError(Exception):
    """Raised when calibration data cannot be loaded."""


@dataclass(frozen=True)
class PredictionResult:
    prediction: str | None
    confidence: float | None
    calibrated: bool
    threshold: float | None


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
        )

    threshold = float(
        calibration["threshold"]
    )

    if delta_score <= threshold:
        prediction = "likely_pathogenic"
    else:
        prediction = "likely_benign"

    # IMPORTANT:
    # We do NOT yet claim a probability/confidence from
    # distance-to-threshold. That would require separate
    # probability calibration.
    confidence = None

    return PredictionResult(
        prediction=prediction,
        confidence=confidence,
        calibrated=True,
        threshold=threshold,
    )