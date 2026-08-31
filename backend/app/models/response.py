from typing import Literal

from pydantic import BaseModel


class SequenceContextResponse(BaseModel):
    genome: str
    chrom: str
    position: int

    window_start: int
    window_end: int

    reference_sequence: str
    variant_sequence: str

    variant_index: int

    ref: str
    alt: str
    
class ClinVarInfoResponse(BaseModel):
    status: str

    variation_id: str | None = None

    accession: str | None = None

    accession_version: str | None = None

    classification: str | None = None

    review_status: str | None = None

    title: str | None = None


class ScoreVariantResponse(BaseModel):
    delta_score: float

    prediction: Literal[
        "likely_pathogenic",
        "likely_benign",
    ] | None

    confidence: float | None
    
    calibrated : bool
    
    clinvar_label: str
    
    clinvar: ClinVarInfoResponse

    explanation: str

    sequence_context: SequenceContextResponse