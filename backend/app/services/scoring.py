from dataclasses import dataclass

from app.services.ucsc import SequenceContext
from app.services.evo2 import score_sequence


class VariantConstructionError(ValueError):
    """Raised when a variant sequence cannot be constructed safely."""


@dataclass(frozen=True)
class VariantSequences:
    reference_sequence: str
    variant_sequence: str
    variant_index: int
    ref: str
    alt: str


def build_variant_sequences(
    context: SequenceContext,
    alt: str,
) -> VariantSequences:
    """
    Construct reference and mutated DNA sequences.

    The reference sequence comes directly from UCSC.
    The variant sequence replaces REF with ALT at the
    verified variant position.
    """

    alt = alt.upper().strip()

    if not alt:
        raise VariantConstructionError(
            "ALT allele cannot be empty."
        )

    sequence = context.sequence
    ref = context.ref
    index = context.variant_index

    observed_ref = sequence[
        index : index + len(ref)
    ]

    # Defensive check.
    # UCSC already validated this, but scoring logic should
    # not silently construct an invalid mutation.
    if observed_ref != ref:
        raise VariantConstructionError(
            (
                f"Cannot construct variant sequence: "
                f"expected REF '{ref}' at index {index}, "
                f"but found '{observed_ref}'."
            )
        )

    variant_sequence = (
        sequence[:index]
        + alt
        + sequence[index + len(ref):]
    )

    return VariantSequences(
        reference_sequence=sequence,
        variant_sequence=variant_sequence,
        variant_index=index,
        ref=ref,
        alt=alt,
    )
    
@dataclass(frozen=True)
class Evo2VariantScore:
    reference_score: float
    variant_score: float
    delta_score: float
    window_size: int


async def score_variant_with_evo2(
    context: SequenceContext,
    alt: str,
) -> Evo2VariantScore:
    """
    Score reference and alternate sequences with Evo2.

    delta_score =
        variant_score - reference_score

    More-negative delta indicates that the alternate
    sequence is less likely under Evo2 than the reference.
    """

    sequences = build_variant_sequences(
        context=context,
        alt=alt,
    )

    reference_score = await score_sequence(
        sequences.reference_sequence
    )

    variant_score = await score_sequence(
        sequences.variant_sequence
    )

    delta_score = (
        variant_score
        - reference_score
    )

    return Evo2VariantScore(
        reference_score=reference_score,
        variant_score=variant_score,
        delta_score=delta_score,
        window_size=len(
            sequences.reference_sequence
        ),
    )
    
@dataclass(frozen=True)
class DisplaySequenceContext:
    reference_sequence: str
    variant_sequence: str

    variant_index: int

    window_start: int
    window_end: int

    ref: str
    alt: str


def build_display_sequence_context(
    context: SequenceContext,
    alt: str,
    flank_size: int = 10,
) -> DisplaySequenceContext:
    """
    Build a small reference/variant window for frontend display.

    This is separate from the 8192 bp Evo2 scoring window.
    """

    sequences = build_variant_sequences(
        context=context,
        alt=alt,
    )

    index = sequences.variant_index

    start_index = max(
        0,
        index - flank_size,
    )

    end_index = min(
        len(sequences.reference_sequence),
        index + len(context.ref) + flank_size,
    )

    reference_display = (
        sequences.reference_sequence[
            start_index:end_index
        ]
    )

    variant_display = (
        sequences.variant_sequence[
            start_index:
            start_index
            + len(reference_display)
            - len(context.ref)
            + len(alt)
        ]
    )

    display_variant_index = (
        index - start_index
    )

    genomic_start = (
        context.start
        + start_index
    )

    genomic_end = (
        genomic_start
        + len(reference_display)
    )

    return DisplaySequenceContext(
        reference_sequence=reference_display,
        variant_sequence=variant_display,
        variant_index=display_variant_index,
        window_start=genomic_start,
        window_end=genomic_end,
        ref=context.ref,
        alt=alt,
    )