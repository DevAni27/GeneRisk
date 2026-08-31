from dataclasses import dataclass

import httpx

from app.config import GENOME_ASSEMBLY, UCSC_BASE_URL


class UCSCServiceError(Exception):
    """Raised when sequence data cannot be retrieved from UCSC."""


class ReferenceAlleleMismatchError(ValueError):
    """Raised when the supplied REF allele does not match the reference genome."""


@dataclass(frozen=True)
class SequenceContext:
    genome: str
    chrom: str
    position: int
    ref: str

    # UCSC 0-based coordinates for the complete fetched window
    start: int
    end: int

    sequence: str

    # Index inside `sequence` where the variant begins
    variant_index: int


def normalize_chromosome(chrom: str) -> str:
    """
    Convert chromosome names to UCSC format.

    Examples:
        "11" -> "chr11"
        "chr11" -> "chr11"
        "CHR11" -> "chr11"
    """

    chrom = chrom.strip()

    if chrom.lower().startswith("chr"):
        chrom = chrom[3:]

    return f"chr{chrom}"


async def fetch_sequence(
    chrom: str,
    start: int,
    end: int,
) -> str:
    """
    Fetch DNA sequence from the UCSC Genome Browser API.

    UCSC uses:
        start = 0-based
        end   = end-exclusive / 1-relative boundary
    """

    chrom = normalize_chromosome(chrom)

    query = (
        f"genome={GENOME_ASSEMBLY};"
        f"chrom={chrom};"
        f"start={start};"
        f"end={end}"
    )

    url = f"{UCSC_BASE_URL}/getData/sequence?{query}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise UCSCServiceError(
            f"Failed to retrieve sequence from UCSC: {exc}"
        ) from exc

    data = response.json()

    dna = data.get("dna")

    if not dna:
        raise UCSCServiceError(
            "UCSC response did not contain DNA sequence data."
        )

    return dna.upper()


async def get_variant_context(
    chrom: str,
    position: int,
    ref: str,
    flank_size: int = 50,
) -> SequenceContext:
    """
    Fetch reference DNA surrounding a genomic variant and verify REF.

    `position` is expected to be a 1-based genomic position,
    which is how users/ClinVar typically describe variants.

    UCSC requires a 0-based start coordinate.
    """

    if position < 1:
        raise ValueError("Position must be >= 1.")

    if flank_size < 0:
        raise ValueError("flank_size cannot be negative.")

    ref = ref.upper().strip()

    if not ref:
        raise ValueError("REF allele cannot be empty.")

    chrom = normalize_chromosome(chrom)

    # Convert our 1-based genomic coordinate to UCSC's 0-based start.
    variant_start = position - 1

    # Allows REF to contain more than one nucleotide later.
    variant_end = variant_start + len(ref)

    # Grab some DNA on both sides of the mutation.
    window_start = max(
        0,
        variant_start - flank_size,
    )

    window_end = variant_end + flank_size

    sequence = await fetch_sequence(
        chrom=chrom,
        start=window_start,
        end=window_end,
    )

    # Find where our variant lies inside the fetched sequence.
    variant_index = variant_start - window_start

    observed_ref = sequence[
        variant_index : variant_index + len(ref)
    ]

    if observed_ref != ref:
        raise ReferenceAlleleMismatchError(
            (
                f"Reference allele mismatch at "
                f"{chrom}:{position}. "
                f"Expected '{ref}', "
                f"but {GENOME_ASSEMBLY} contains "
                f"'{observed_ref}'."
            )
        )

    return SequenceContext(
        genome=GENOME_ASSEMBLY,
        chrom=chrom,
        position=position,
        ref=ref,
        start=window_start,
        end=window_end,
        sequence=sequence,
        variant_index=variant_index,
    )
    
async def get_centered_variant_context(
    chrom: str,
    position: int,
    ref: str,
    window_size: int = 8192,
) -> SequenceContext:
    """
    Fetch an exactly `window_size`-bp genomic window centered
    around the variant.

    Designed for Evo2 zero-shot variant scoring.

    Position is 1-based genomic.
    UCSC start/end coordinates are 0-based/end-exclusive.
    """

    if position < 1:
        raise ValueError(
            "Position must be >= 1."
        )

    if window_size <= 0:
        raise ValueError(
            "window_size must be positive."
        )

    if window_size % 2 != 0:
        raise ValueError(
            "window_size must be even."
        )

    ref = ref.upper().strip()

    if not ref:
        raise ValueError(
            "REF allele cannot be empty."
        )

    chrom = normalize_chromosome(
        chrom
    )

    # Convert 1-based genomic position → 0-based.
    variant_start = position - 1

    half_window = window_size // 2

    # Variant sits at index 4096 for an 8192-bp window.
    window_start = (
        variant_start - half_window
    )

    if window_start < 0:
        raise ValueError(
            (
                "Variant is too close to chromosome start "
                f"for a {window_size}-bp centered window."
            )
        )

    window_end = (
        window_start + window_size
    )

    sequence = await fetch_sequence(
        chrom=chrom,
        start=window_start,
        end=window_end,
    )

    if len(sequence) != window_size:
        raise UCSCServiceError(
            (
                f"Expected {window_size} bp from UCSC, "
                f"received {len(sequence)}."
            )
        )

    variant_index = (
        variant_start - window_start
    )

    observed_ref = sequence[
        variant_index:
        variant_index + len(ref)
    ]

    if observed_ref != ref:
        raise ReferenceAlleleMismatchError(
            (
                f"Reference allele mismatch at "
                f"{chrom}:{position}. "
                f"Expected '{ref}', "
                f"but {GENOME_ASSEMBLY} contains "
                f"'{observed_ref}'."
            )
        )

    return SequenceContext(
        genome=GENOME_ASSEMBLY,
        chrom=chrom,
        position=position,
        ref=ref,
        start=window_start,
        end=window_end,
        sequence=sequence,
        variant_index=variant_index,
    )