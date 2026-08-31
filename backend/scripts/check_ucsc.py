import asyncio

from app.services.scoring import build_variant_sequences
from app.services.ucsc import get_variant_context


async def main():
    context = await get_variant_context(
        chrom="11",
        position=5227002,
        ref="T",
        flank_size=25,
    )

    sequences = build_variant_sequences(
        context=context,
        alt="A",
    )

    index = sequences.variant_index

    print("Genome:", context.genome)
    print("Chromosome:", context.chrom)
    print("Position:", context.position)

    print()
    print("Reference:")
    print(
        sequences.reference_sequence[:index]
        + "["
        + sequences.ref
        + "]"
        + sequences.reference_sequence[
            index + len(sequences.ref):
        ]
    )

    print()
    print("Variant:")
    print(
        sequences.variant_sequence[:index]
        + "["
        + sequences.alt
        + "]"
        + sequences.variant_sequence[
            index + len(sequences.alt):
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())