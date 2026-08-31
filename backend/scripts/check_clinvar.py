import asyncio

from app.services.clinvar import (
    build_clinvar_query,
    lookup_clinvar,
)


async def main():
    chrom = "11"
    position = 5227002
    ref = "T"
    alt = "A"

    print("ClinVar query:")
    print(
        build_clinvar_query(
            chrom=chrom,
            position=position,
            ref=ref,
            alt=alt,
        )
    )

    print()
    print("Searching ClinVar...")

    result = await lookup_clinvar(
        chrom=chrom,
        position=position,
        ref=ref,
        alt=alt,
    )

    print()
    print("=== CLINVAR RESULT ===")

    print(
        "Status:",
        result.status,
    )

    print(
        "Classification:",
        result.classification,
    )

    print(
        "Variation ID:",
        result.variation_id,
    )

    print(
        "Accession:",
        result.accession,
    )

    print(
        "Accession version:",
        result.accession_version,
    )

    print(
        "Review status:",
        result.review_status,
    )

    print(
        "Title:",
        result.title,
    )


if __name__ == "__main__":
    asyncio.run(main())