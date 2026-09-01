from typing import Literal

from pydantic import BaseModel


ReportType = Literal[
    "molecular_genetic",
    "hemoglobin_fractionation",
    "unknown",
]


class ReportVariantCandidate(BaseModel):
    gene: Literal["HBB"] = "HBB"

    # This is what the frontend can later send
    # directly to POST /score-query.
    query: str

    transcript: str | None = None
    hgvs_c: str
    hgvs_p: str | None = None

    zygosity: Literal[
        "heterozygous",
        "homozygous",
        "hemizygous",
    ] | None = None

    reported_classification: Literal[
        "Pathogenic",
        "Likely Pathogenic",
        "Benign",
        "Likely Benign",
        "VUS",
    ] | None = None

    common_name: str | None = None

    # Current GeneRisk scoring pipeline supports SNVs.
    can_score: bool
    reason_not_scorable: str | None = None


class ReportExtractionResponse(BaseModel):
    filename: str
    report_type: ReportType

    variants_found: int
    scorable_variants: int

    # Important: don't automatically score a variant
    # extracted from a medical document.
    requires_confirmation: bool = True

    variants: list[ReportVariantCandidate]

    message: str