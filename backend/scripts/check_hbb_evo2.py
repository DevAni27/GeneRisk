import asyncio

from app.services.scoring import (
    build_variant_sequences,
    score_variant_with_evo2,
)
from app.services.ucsc import (
    get_centered_variant_context,
)


async def main():
    print(
        "Fetching HBB reference sequence..."
    )

    context = await get_centered_variant_context(
        chrom="11",
        position=5227002,
        ref="T",
        window_size=8192,
    )

    print()
    print("Variant:")
    print("HBB chr11:5227002 T>A")

    print()
    print("Genome:", context.genome)
    print(
        "Window:",
        f"{context.chrom}:{context.start}-{context.end}",
    )
    print(
        "Window length:",
        len(context.sequence),
    )
    print(
        "Variant index:",
        context.variant_index,
    )

    sequences = build_variant_sequences(
        context=context,
        alt="A",
    )

    print()
    print(
        "Reference allele:",
        sequences.reference_sequence[
            context.variant_index
        ],
    )

    print(
        "Variant allele:",
        sequences.variant_sequence[
            context.variant_index
        ],
    )

    print()
    print(
        "Scoring reference with Evo2..."
    )

    result = await score_variant_with_evo2(
        context=context,
        alt="A",
    )

    print()
    print("=== EVO2 RESULT ===")
    print(
        "Reference score:",
        result.reference_score,
    )

    print(
        "Variant score:",
        result.variant_score,
    )

    print(
        "Delta score:",
        result.delta_score,
    )

    print(
        "Window size:",
        result.window_size,
    )


if __name__ == "__main__":
    asyncio.run(main())