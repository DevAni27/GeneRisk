from app.services.scoring import (
    VariantConstructionError,
    build_variant_sequences,
)
from app.services.ucsc import SequenceContext
import pytest

def test_build_variant_sequences():
    context = SequenceContext(
        genome="hg38",
        chrom="chr11",
        position=5227002,
        ref="T",
        start=5226999,
        end=5227005,
        sequence="GGTCAC",
        variant_index=2,
    )

    result = build_variant_sequences(
        context=context,
        alt="A",
    )

    assert result.reference_sequence == "GGTCAC"
    assert result.variant_sequence == "GGACAC"

    assert result.ref == "T"
    assert result.alt == "A"

    assert result.reference_sequence[
        result.variant_index
    ] == "T"

    assert result.variant_sequence[
        result.variant_index
    ] == "A"
    



def test_variant_construction_rejects_ref_mismatch():
    context = SequenceContext(
        genome="hg38",
        chrom="chr11",
        position=5227002,
        ref="T",
        start=5226999,
        end=5227005,
        sequence="GGACAC",
        variant_index=2,
    )

    with pytest.raises(VariantConstructionError):
        build_variant_sequences(
            context=context,
            alt="A",
        )