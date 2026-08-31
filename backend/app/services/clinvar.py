from dataclasses import dataclass
from typing import Literal

import httpx

from app.config import (
    NCBI_API_KEY,
    NCBI_EMAIL,
    NCBI_EUTILS_BASE_URL,
    NCBI_TOOL,
)


class ClinVarServiceError(Exception):
    """Raised when ClinVar cannot be queried successfully."""


ClinVarStatus = Literal[
    "found",
    "not_found",
    "unavailable",
]


@dataclass(frozen=True)
class ClinVarResult:
    status: ClinVarStatus

    classification: str | None = None

    variation_id: str | None = None
    accession: str | None = None
    accession_version: str | None = None

    review_status: str | None = None
    title: str | None = None


def normalize_chromosome_for_clinvar(
    chrom: str,
) -> str:
    """
    ClinVar gnomAD-style search expects chromosome
    without the 'chr' prefix.

    Examples:
        chr11 -> 11
        11    -> 11
    """

    chrom = chrom.strip()

    if chrom.lower().startswith("chr"):
        chrom = chrom[3:]

    return chrom


GRCH38_REFSEQ_ACCESSIONS = {
    "11": "NC_000011.10",
}


def build_canonical_spdi(
    chrom: str,
    position: int,
    ref: str,
    alt: str,
) -> str:
    chrom = normalize_chromosome_for_clinvar(
        chrom
    )

    accession = GRCH38_REFSEQ_ACCESSIONS.get(
        chrom
    )

    if not accession:
        raise ValueError(
            (
                "No GRCh38 RefSeq accession "
                f"configured for chromosome {chrom}."
            )
        )

    ref = ref.upper().strip()
    alt = alt.upper().strip()

    # API input position = 1-based genomic
    # SPDI position = 0-based
    spdi_position = position - 1

    return (
        f"{accession}:"
        f"{spdi_position}:"
        f"{ref}:"
        f"{alt}"
    )


def build_clinvar_query(
    chrom: str,
    position: int,
    ref: str,
    alt: str,
) -> str:
    spdi = build_canonical_spdi(
        chrom=chrom,
        position=position,
        ref=ref,
        alt=alt,
    )

    return f'"{spdi}"[cspdi]'


def _common_params() -> dict[str, str]:
    """
    Parameters NCBI recommends including with
    E-utilities requests.
    """

    params = {
        "tool": NCBI_TOOL,
    }

    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    return params


async def search_clinvar(
    chrom: str,
    position: int,
    ref: str,
    alt: str,
) -> list[str]:
    """
    Search ClinVar for an exact GRCh38 genomic variant.

    Returns ClinVar Variation IDs.
    """

    query = build_clinvar_query(
        chrom=chrom,
        position=position,
        ref=ref,
        alt=alt,
    )

    params = {
        "db": "clinvar",
        "term": query,
        "retmode": "json",
        "retmax": "20",
        **_common_params(),
    }

    url = (
        f"{NCBI_EUTILS_BASE_URL}/"
        "esearch.fcgi"
    )

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise ClinVarServiceError(
            f"ClinVar ESearch failed: {exc}"
        ) from exc

    try:
        data = response.json()

        return (
            data
            .get("esearchresult", {})
            .get("idlist", [])
        )

    except ValueError as exc:
        raise ClinVarServiceError(
            "ClinVar ESearch returned invalid JSON."
        ) from exc
        
async def fetch_clinvar_summary(
    variation_id: str,
) -> ClinVarResult:
    """
    Fetch ClinVar's aggregate variant-level summary
    for a Variation ID.
    """

    params = {
        "db": "clinvar",
        "id": variation_id,
        "retmode": "json",
        **_common_params(),
    }

    url = (
        f"{NCBI_EUTILS_BASE_URL}/"
        "esummary.fcgi"
    )

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise ClinVarServiceError(
            f"ClinVar ESummary failed: {exc}"
        ) from exc

    try:
        data = response.json()

    except ValueError as exc:
        raise ClinVarServiceError(
            "ClinVar ESummary returned invalid JSON."
        ) from exc

    result = data.get(
        "result",
        {},
    )

    record = result.get(
        variation_id,
    )

    if not record:
        raise ClinVarServiceError(
            (
                "ClinVar ESummary did not contain "
                f"Variation ID {variation_id}."
            )
        )

    germline = record.get(
        "germline_classification",
        {},
    )

    classification = (
        germline.get("description")
        or None
    )

    review_status = (
        germline.get("review_status")
        or None
    )

    return ClinVarResult(
        status="found",
        classification=classification,
        variation_id=variation_id,
        accession=record.get(
            "accession"
        ),
        accession_version=record.get(
            "accession_version"
        ),
        review_status=review_status,
        title=record.get("title"),
    )
    
    
async def fetch_clinvar_summaries(
    variation_ids: list[str],
) -> dict[str, dict]:
    """
    Retrieve ESummary records for multiple ClinVar
    Variation IDs in a single request.
    """

    if not variation_ids:
        return {}

    params = {
        "db": "clinvar",
        "id": ",".join(variation_ids),
        "retmode": "json",
        **_common_params(),
    }

    url = (
        f"{NCBI_EUTILS_BASE_URL}/"
        "esummary.fcgi"
    )

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise ClinVarServiceError(
            f"ClinVar ESummary failed: {exc}"
        ) from exc

    try:
        data = response.json()

    except ValueError as exc:
        raise ClinVarServiceError(
            "ClinVar ESummary returned invalid JSON."
        ) from exc

    result = data.get(
        "result",
        {},
    )

    records = {}

    for variation_id in variation_ids:
        record = result.get(
            variation_id
        )

        if record:
            records[variation_id] = record

    return records
  
def find_exact_spdi_record(
    records: dict[str, dict],
    target_spdi: str,
) -> tuple[str, dict] | None:
    """
    Find the ClinVar record representing exactly the
    requested simple allele.

    Haplotype records may contain our allele as one of
    several components, so we only accept records with
    exactly one variation_set entry whose canonical SPDI
    matches the requested variant.
    """

    for variation_id, record in records.items():

        variation_set = record.get(
            "variation_set",
            [],
        )

        # Important:
        # a haplotype can contain the requested allele,
        # but will contain multiple component variants.
        if len(variation_set) != 1:
            continue

        allele = variation_set[0]

        canonical_spdi = allele.get(
            "canonical_spdi"
        )

        if canonical_spdi == target_spdi:
            return variation_id, record

    return None
  
def record_to_clinvar_result(
    variation_id: str,
    record: dict,
) -> ClinVarResult:

    germline = record.get(
        "germline_classification",
        {},
    )

    classification = (
        germline.get("description")
        or None
    )

    review_status = (
        germline.get("review_status")
        or None
    )

    return ClinVarResult(
        status="found",

        classification=classification,

        variation_id=variation_id,

        accession=record.get(
            "accession"
        ),

        accession_version=record.get(
            "accession_version"
        ),

        review_status=review_status,

        title=record.get(
            "title"
        ),
    )
    
async def lookup_clinvar(
    chrom: str,
    position: int,
    ref: str,
    alt: str,
) -> ClinVarResult:
    """
    Look up the exact simple genomic variant in ClinVar.

    ClinVar search results may also include haplotypes
    containing the requested allele. We therefore inspect
    candidate records and select the one whose canonical
    SPDI exactly matches the requested variant.
    """

    # -------------------------------------------------
    # 1. Build the exact SPDI we expect
    # -------------------------------------------------
    target_spdi = build_canonical_spdi(
        chrom=chrom,
        position=position,
        ref=ref,
        alt=alt,
    )

    # -------------------------------------------------
    # 2. Search ClinVar
    # -------------------------------------------------
    variation_ids = await search_clinvar(
        chrom=chrom,
        position=position,
        ref=ref,
        alt=alt,
    )

    if not variation_ids:
        return ClinVarResult(
            status="not_found",
        )

    # -------------------------------------------------
    # 3. Fetch summaries for ALL matching IDs
    # -------------------------------------------------
    records = await fetch_clinvar_summaries(
        variation_ids
    )

    if not records:
        return ClinVarResult(
            status="not_found",
        )

    # -------------------------------------------------
    # 4. Find the record matching our exact SPDI
    # -------------------------------------------------
    match = find_exact_spdi_record(
        records=records,
        target_spdi=target_spdi,
    )

    if match is None:
        return ClinVarResult(
            status="not_found",
        )

    # -------------------------------------------------
    # 5. Convert raw ClinVar record into our model
    # -------------------------------------------------
    variation_id, record = match

    return record_to_clinvar_result(
        variation_id=variation_id,
        record=record,
    )